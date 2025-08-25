CREATE TABLE vehicles (
  vehicle_id VARCHAR PRIMARY KEY,
  name VARCHAR,
  type VARCHAR,
  plate_no VARCHAR,
  capacity FLOAT,
  owner VARCHAR
);

CREATE TABLE positions (
  id SERIAL PRIMARY KEY,
  vehicle_id VARCHAR REFERENCES vehicles(vehicle_id),
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  sog FLOAT,
  cog FLOAT,
  heading FLOAT,
  status VARCHAR,
  ts TIMESTAMP DEFAULT NOW()
);
