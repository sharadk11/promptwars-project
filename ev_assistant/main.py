from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from contextlib import asynccontextmanager
from db import init_db_pool, close_db_pool, get_cached_stations, save_station
from services.maps import fetch_places_from_google
from utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Pool
    logger.info("Starting EV Assistant API")
    try:
        await init_db_pool()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}. API will attempt to run, but DB requests will fail.")
    yield
    # Shutdown: Clean up Database Pool
    await close_db_pool()

app = FastAPI(
    title="EV Charging Station Finder Assistant",
    description="Smart assistant to find EV charging stations using GCP and Maps API.",
    version="1.0.0",
    lifespan=lifespan
)

# Security: Add CORS middleware to restrict cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For hackathon. In prod, restrict to specific domains.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EV Station Finder</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap" rel="stylesheet">
        <style>
            :root { --bg: #0f172a; --surface: rgba(30, 41, 59, 0.7); --primary: #10b981; --text: #f8fafc; }
            body { 
                margin: 0; min-height: 100vh; background: var(--bg); color: var(--text);
                font-family: 'Outfit', sans-serif;
                background-image: radial-gradient(circle at top right, #064e3b, transparent 40%), radial-gradient(circle at bottom left, #1e3a8a, transparent 40%);
                display: flex; flex-direction: column; align-items: center; padding: 2rem;
            }
            .container { max-width: 800px; width: 100%; z-index: 10; }
            h1 { text-align: center; font-size: 3rem; margin-bottom: 0.5rem; background: linear-gradient(to right, #34d399, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            p.subtitle { text-align: center; color: #94a3b8; margin-bottom: 3rem; font-size: 1.1rem; }
            .search-box { 
                background: var(--surface); padding: 2rem; border-radius: 1rem; 
                backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1);
                display: grid; grid-template-columns: 1fr auto auto auto; gap: 1rem; align-items: center;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }
            input, select { 
                padding: 1rem; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.2); 
                background: rgba(15, 23, 42, 0.6); color: white; font-family: inherit; font-size: 1rem; outline: none;
            }
            input:focus, select:focus { border-color: var(--primary); }
            button { 
                padding: 1rem 2rem; border-radius: 0.5rem; border: none; background: var(--primary); 
                color: white; font-weight: bold; cursor: pointer; transition: transform 0.2s, background 0.2s; font-size: 1rem;
            }
            button:hover { background: #059669; transform: translateY(-2px); }
            .results { margin-top: 3rem; display: grid; gap: 1rem; }
            .card { 
                background: var(--surface); padding: 1.5rem; border-radius: 1rem; backdrop-filter: blur(12px); 
                border: 1px solid rgba(255,255,255,0.05); transition: transform 0.3s;
                display: flex; justify-content: space-between; align-items: center;
            }
            .card:hover { transform: translateY(-5px); border-color: rgba(255,255,255,0.2); }
            .card h3 { margin: 0 0 0.5rem 0; color: #34d399; }
            .card p { margin: 0; color: #cbd5e1; font-size: 0.9rem; }
            .badge { background: rgba(52, 211, 153, 0.2); color: #34d399; padding: 0.3rem 0.8rem; border-radius: 2rem; font-size: 0.8rem; font-weight: bold; }
            .loader { text-align: center; display: none; margin-top: 2rem; color: var(--primary); }
            
            @media (max-width: 768px) {
                .search-box { grid-template-columns: 1fr; }
                .card { flex-direction: column; align-items: flex-start; gap: 1rem; }
            }
        </style>
    </head>
    <body>
        <main class="container">
            <h1>EV Station Finder</h1>
            <p class="subtitle">Discover charging stations near you powered by Google Cloud</p>
            
            <div class="search-box">
                <label for="location" class="visually-hidden" style="display:none;">Location</label>
                <input type="text" id="location" name="location" aria-label="Enter City" placeholder="Enter City (e.g., Pune, Mumbai)..." value="Pune">
                
                <label for="charger" class="visually-hidden" style="display:none;">Charger Type</label>
                <select id="charger" name="charger" aria-label="Select Charger Type">
                    <option value="fast">Fast Charger</option>
                    <option value="slow">Slow Charger</option>
                    <option value="CCS">CCS</option>
                    <option value="Type2">Type 2</option>
                </select>
                
                <label for="radius" class="visually-hidden" style="display:none;">Search Radius</label>
                <select id="radius" name="radius" aria-label="Select Search Radius">
                    <option value="5">5 km</option>
                    <option value="10">10 km</option>
                    <option value="20">20 km</option>
                </select>
                
                <button aria-label="Search for EV Stations" onclick="searchStations()">Search</button>
            </div>

            <div class="loader" id="loader" role="status" aria-live="polite">Fetching stations... ⚡</div>
            <div class="results" id="results" aria-live="polite"></div>
        </main>

        <script>
            async function searchStations() {
                const loc = document.getElementById('location').value;
                const type = document.getElementById('charger').value;
                const rad = document.getElementById('radius').value;
                const resultsDiv = document.getElementById('results');
                const loader = document.getElementById('loader');
                
                if(!loc) return alert("Please enter a location!");
                
                resultsDiv.innerHTML = '';
                loader.style.display = 'block';

                try {
                    const response = await fetch(`/search?location=${loc}&charger_type=${type}&radius=${rad}`);
                    const data = await response.json();
                    
                    loader.style.display = 'none';
                    
                    if(data.results && data.results.length > 0) {
                        data.results.forEach(station => {
                            resultsDiv.innerHTML += `
                                <div class="card">
                                    <div>
                                        <h3>${station.name}</h3>
                                        <p>📍 ${station.address || 'Address not available'}</p>
                                        <p style="margin-top: 0.5rem">⭐ ${station.rating || 'N/A'} / 5.0 | Source: ${data.source}</p>
                                    </div>
                                    <div class="badge">⚡ ${station.charger_type.toUpperCase()}</div>
                                </div>
                            `;
                        });
                    } else {
                        resultsDiv.innerHTML = '<p style="text-align:center">No stations found in this area. Try another city!</p>';
                    }
                } catch(e) {
                    loader.style.display = 'none';
                    resultsDiv.innerHTML = '<p style="text-align:center; color:#ef4444;">Error fetching data. Check your API key or server status.</p>';
                }
            }
            
            // Initial load
            searchStations();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "EV Assistant"}

# Endpoint to search EV stations
# Takes location, charger_type and radius as input
# Fetch data from Google Places API if not found in DB
@app.get("/search")
async def search_ev_stations(
    location: str = Query(..., description="City or location to search"),
    charger_type: Optional[str] = Query(None, description="fast, slow, CCS, Type2"),
    radius: Optional[float] = Query(5.0, description="Search radius in km")
):
    logger.info(f"Searching EV stations: Location={location}, Type={charger_type}, Radius={radius}km")
    
    try:
        # 1. Check PostgreSQL for cached results
        cached_results = await get_cached_stations(location, charger_type, radius)
        
        if cached_results:
            logger.info(f"Found {len(cached_results)} stations in cache")
            return {"results": cached_results, "source": "database"}
            
        # 2. If not found in cache -> call Google Places API
        logger.info("No cached results found, fetching from Google Places API...")
        places = await fetch_places_from_google(location, radius)
        
        results = []
        for place in places:
            name = place.get("name", "Unknown Station")
            address = place.get("formatted_address", "")
            lat = place.get("geometry", {}).get("location", {}).get("lat", 0.0)
            lng = place.get("geometry", {}).get("location", {}).get("lng", 0.0)
            rating = place.get("rating", 0.0)
            
            # Use requested charger type or default to unknown if not specified
            ctype = charger_type if charger_type else "standard"
            
            # 3. Store new results in Database
            await save_station(name, location, lat, lng, ctype, rating)
            
            results.append({
                "name": name,
                "address": address,
                "distance_km": radius, # Estimated representation for now
                "charger_type": ctype,
                "rating": rating,
                "latitude": lat,
                "longitude": lng
            })
            
        return {"results": results, "source": "google_places_api"}
        
    except Exception as e:
        logger.error(f"Search endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while searching for EV stations")
