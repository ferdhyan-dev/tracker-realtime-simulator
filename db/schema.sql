CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id VARCHAR PRIMARY KEY,
  name       VARCHAR,
  type       VARCHAR,
  plate_no   VARCHAR,
  capacity   FLOAT,
  owner      VARCHAR
);

CREATE TABLE IF NOT EXISTS positions (
  id         SERIAL PRIMARY KEY,
  vehicle_id VARCHAR REFERENCES vehicles(vehicle_id),
  lat        DOUBLE PRECISION,
  lon        DOUBLE PRECISION,
  sog        FLOAT,     -- speed over ground
  cog        FLOAT,     -- course over ground
  heading    FLOAT,
  status     VARCHAR,
  ts         TIMESTAMP DEFAULT NOW()
);

-- Index yang membantu query posisi terakhir
CREATE INDEX IF NOT EXISTS idx_positions_vehicle_ts ON positions(vehicle_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_positions_ts       ON positions(ts DESC);
