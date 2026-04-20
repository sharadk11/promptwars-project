# EV Charging Station Finder Assistant

## 1. Problem Statement
With the rapid adoption of electric vehicles in India, EV owners frequently face "range anxiety" and struggle to find reliable charging stations. Existing maps often lack specific filters like charger type (CCS, Type2, fast/slow). This assistant provides a scalable, fast API to discover nearby EV stations matching user requirements.

## Features

- Smart EV station search based on location, charger type, and radius
- Real-time data using Google Maps Places API
- Backend powered by FastAPI and PostgreSQL (Cloud SQL)
- Deployed using Google Cloud Run
- Secure API key handling using environment variables

## Google Cloud Services Used

- Cloud Run (API hosting)
- Cloud SQL (PostgreSQL database)
- Google Maps Places API
- Secret Manager (API key handling)
- Cloud Logging

## Security

- API keys are not hardcoded
- Environment variables used for sensitive data
- Input validation implemented

## Testing

- Manual testing using API endpoints
- Verified responses for multiple locations (Pune, Mumbai)

## 2. Architecture (Google Cloud Focused)
This system is designed natively on **Google Cloud Platform (GCP)** for high availability, security, and minimal ops:
- **Compute:** Cloud Run (Serverless execution of the FastAPI app)
- **Database:** Cloud SQL for PostgreSQL (Persistent storage & caching)
- **External API:** Google Maps Places API (Real-time discovery of stations)
- **Security:** Secret Manager (Secure storage of Maps API keys and DB credentials)
- **Observability:** Cloud Logging (Centralized application logs)

## 3. How It Works Under the Hood

### ⚙️ The Backend Architecture (FastAPI)
The backend is powered by **FastAPI**, an extremely fast, modern Python web framework.
1. **Lifespan & Resiliency**: When the server boots, it attempts to establish a connection pool to PostgreSQL. If the database is unreachable, the app is designed to gracefully catch the error and keep the server running anyway, ensuring zero downtime.
2. **The Brain (`/search` Endpoint)**: This is the core engine. When it receives a request (e.g., `?location=Pune&charger_type=fast`):
   - **Cache Check**: It first asks PostgreSQL if anyone has searched for this city recently. If found, it returns the results instantly.
   - **Live API Fallback**: If the cache is empty (or the database is offline), it automatically switches to the **Google Maps Places API**, fetching live, real-world data for EV stations.
   - **Save & Serve**: It attempts to save new stations back to the database for future users, then returns the data as clean JSON.

### 🎨 The Frontend UI (Single Page Application)
Instead of building a bulky separate frontend (like React or Angular), we injected a highly optimized "Single Page Application" directly into the root route (`/`).
1. **Serving HTML**: When you visit the main URL, FastAPI reads the embedded HTML/CSS/JS code and returns it directly to the browser.
2. **Premium Styling**: The UI uses modern design techniques like **Glassmorphism** (`backdrop-filter: blur`), CSS Grid for responsive layouts, and dynamic gradients to achieve a sleek, cloud-native aesthetic.
3. **Asynchronous JavaScript**: 
   - When the user clicks "Search", vanilla JavaScript intercepts the dropdown values.
   - It uses the browser's native `fetch()` API to silently call our own backend `/search` API in the background.
   - While waiting, it displays a loading animation.
   - Once the backend replies with JSON data, the script dynamically generates HTML "Cards" on the screen, instantly displaying the station names, coordinates, ratings, and charger types without ever reloading the page!

## 4. Setup Steps

### Local Setup
```bash
# 1. Clone/Enter Directory
cd ev_assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup PostgreSQL Locally & Run SQL
psql -U postgres -d your_db -f sample_data.sql

# 4. Set Environment Variables
export DB_USER=postgres
export DB_PASS=your_db_password
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ev_db
export MAPS_API_KEY=your_google_maps_api_key

# 5. Run Server
uvicorn main:app --reload --port 8080
```

## 5. API Usage

### Health Check
```bash
curl "https://<cloud-run-url>/health"
```

### Search EV Stations
```bash
# Example query
curl "https://<cloud-run-url>/search?location=Pune&charger_type=fast&radius=5"
```
**Response Format:**
```json
{
  "results": [
    {
      "name": "Tata Power EV Charging Station",
      "address": "Pune, Maharashtra, India",
      "distance_km": 5.0,
      "charger_type": "fast",
      "rating": 4.5
    }
  ],
  "source": "database"
}
```

## Assumptions

- Charger type inferred based on query
- Google Places API used when DB data not available

## 7. Future Improvements
- Integrate **PostGIS** in Cloud SQL for exact coordinate-based radial (`distance_km`) searches.
- Implement a background Cloud Scheduler job to periodically refresh outdated cache records.
- Add user authentication via Firebase Auth.
- Use Google Maps Geocoding API to resolve coordinates before querying the Nearby Search API for tighter radius precision.

---

## 🚀 GCP Deployment Commands

To deploy this project to Google Cloud, execute the following commands precisely:

```bash
# 1. Set the correct project
gcloud config set project promptwars-project-493610

# 2. Enable necessary APIs
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    maps-backend.googleapis.com

# 3. Create a Secret in Secret Manager (Assuming API key is ready)
# Replace 'YOUR_API_KEY' with the actual maps key
echo -n "YOUR_API_KEY" | gcloud secrets create MAPS_API_KEY \
    --data-file=- \
    --replication-policy="automatic"

# 4. Deploy to Cloud Run
# Make sure to setup Cloud SQL connection via the UI or using `--add-cloudsql-instances`
# For this basic deployment, we pass environment variables needed
gcloud run deploy ev-assistant \
    --source . \
    --region asia-south1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars PROJECT_ID=promptwars-project-493610,DB_USER=postgres,DB_PASS=your_db_password,DB_HOST=your_cloud_sql_ip,DB_PORT=5432,DB_NAME=postgres
```
