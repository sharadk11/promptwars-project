import httpx
from google.cloud import secretmanager
import os
from utils.logger import logger

def get_secret(secret_id: str) -> str:
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

async def fetch_places_from_google(location: str, radius: float):
    api_key = get_secret("MAPS_API_KEY")
    if not api_key:
         logger.warning("No Google Maps API key found/configured.")
         return []
         
    # Query Google Places Text Search API
    query_str = f"EV charging station in {location}"
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query_str}&key={api_key}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                 data = response.json()
                 return data.get("results", [])
            else:
                 logger.error(f"Google Places API error: {response.status_code} - {response.text}")
                 return []
    except Exception as e:
        logger.error(f"Failed to call Google Maps API: {e}")
        return []
