import asyncpg
import os
from utils.logger import logger

# Get connection details from environment (or Cloud SQL proxy)
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ev_db")

pool = None

from typing import List, Dict, Any, Optional

async def init_db_pool() -> None:
    """
    Initialize the asynchronous PostgreSQL connection pool.
    
    This creates a connection pool to the Google Cloud SQL instance
    using credentials loaded from environment variables.
    
    Raises:
        Exception: If the database connection fails.
    """
    global pool
    try:
        pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            min_size=1,
            max_size=5
        )
        logger.info("Database connection pool created.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

async def close_db_pool() -> None:
    """
    Close the active PostgreSQL connection pool gracefully.
    """
    global pool
    if pool:
        await pool.close()
        logger.info("Database connection pool closed.")

async def get_cached_stations(location: str, charger_type: Optional[str], radius: float) -> List[Dict[str, Any]]:
    """
    Retrieve cached EV charging stations from the database.
    
    Args:
        location (str): The city or location string.
        charger_type (Optional[str]): The specific charger type requested.
        radius (float): The search radius in kilometers.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionary objects representing EV stations.
    """
    if not pool:
        try:
            await init_db_pool()
        except Exception:
            return []
        
    if not pool:
        return []
        
    # For a hackathon, we use basic substring matching for city
    # In production, this would use PostGIS for exact distance calculations
    query = """
    SELECT id, name, city, latitude, longitude, charger_type, rating
    FROM ev_stations
    WHERE city ILIKE $1
    """
    args = [f"%{location}%"]
    
    if charger_type:
         query += " AND charger_type = $2"
         args.append(charger_type)
         
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"DB Error while fetching stations: {e}")
        return []

async def save_station(name: str, city: str, lat: float, lng: float, charger_type: str, rating: float) -> None:
    """
    Save a new EV charging station record into the database.
    
    Args:
        name (str): Name of the station.
        city (str): City where the station is located.
        lat (float): Latitude coordinate.
        lng (float): Longitude coordinate.
        charger_type (str): Type of charger available.
        rating (float): Average user rating.
    """
    if not pool:
         try:
             await init_db_pool()
         except Exception:
             return
             
    if not pool:
         return
         
    query = """
    INSERT INTO ev_stations (name, city, latitude, longitude, charger_type, rating)
    VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING id
    """
    try:
        async with pool.acquire() as conn:
             await conn.execute(query, name, city, lat, lng, charger_type, rating)
    except Exception as e:
        logger.error(f"DB Error while saving station: {e}")
