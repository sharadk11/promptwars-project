import requests
from google.cloud import secretmanager
import os
from typing import List, Dict, Any
from utils.logger import logger
import asyncio

def get_secret(secret_id: str) -> str:
    """
    Fetch a secret from Google Cloud Secret Manager.
    
    This function first checks local environment variables for the secret.
    If not found, it securely fetches the latest version of the secret
    from Google Cloud Secret Manager.
    
    Args:
        secret_id (str): The identifier of the secret to fetch.
        
    Returns:
        str: The decoded secret payload, or an empty string if retrieval fails.
    """
    # Local fallback
    if os.environ.get("MAPS_API_KEY"):
         return os.environ["MAPS_API_KEY"]
         
    project_id = os.environ.get("PROJECT_ID", "promptwars-project-493610")
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to fetch secret {secret_id}: {e}")
        return ""

async def fetch_places_from_google(location: str, radius: float) -> List[Dict[str, Any]]:
    """
    Fetch live EV charging station data from the Google Maps Places API.
    
    Constructs an optimized text search query for EV stations near the
    specified location and executes the API call asynchronously.
    
    Args:
        location (str): The geographical location to search.
        radius (float): The search radius in kilometers.
        
    Returns:
        List[Dict[str, Any]]: A list of raw result dictionaries returned by Google API.
    """
    api_key = get_secret("MAPS_API_KEY")
    if not api_key:
         logger.warning("No Google Maps API key found/configured.")
         return []
         
    # Query Google Places Text Search API
    query_str = f"EV charging station in {location}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query_str}&key={api_key}"
    
    def _fetch() -> requests.Response:
        return requests.get(url, timeout=10)
    
    try:
        # Use asyncio.to_thread for efficient async execution of blocking I/O
        response = await asyncio.to_thread(_fetch)
        if response.status_code == 200:
             data = response.json()
             return data.get("results", [])
        else:
             logger.error(f"Google Places API error: {response.status_code} - {response.text}")
             return []
    except Exception as e:
        logger.error(f"Failed to call Google Maps API: {e}")
        return []
