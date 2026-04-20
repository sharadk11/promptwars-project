CREATE TABLE IF NOT EXISTS ev_stations (
    id SERIAL PRIMARY KEY,
    name TEXT,
    city TEXT,
    latitude FLOAT,
    longitude FLOAT,
    charger_type TEXT,
    rating FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO ev_stations (name, city, latitude, longitude, charger_type, rating) VALUES
('Tata Power EV Charging Station', 'Pune', 18.5204, 73.8567, 'fast', 4.5),
('Ather Grid Charging', 'Pune', 18.5538, 73.9477, 'slow', 4.2),
('Jio-bp pulse Charge', 'Pune', 18.6161, 73.7981, 'CCS', 4.8),
('Zeon Charging Station', 'Mumbai', 19.0760, 72.8777, 'Type2', 4.6),
('ChargeZone Fast Charger', 'Mumbai', 19.1136, 72.8697, 'fast', 4.3);
