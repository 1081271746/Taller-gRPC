
CREATE TABLE IF NOT EXISTS sensor_readings (
    id UUID PRIMARY KEY,
    sensor_id VARCHAR(100) NOT NULL,
    crop_id VARCHAR(100) NOT NULL,
    soil_moisture DOUBLE PRECISION NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    air_humidity DOUBLE PRECISION NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agricultural_alerts (
    id BIGSERIAL PRIMARY KEY,
    reading_id UUID NOT NULL
        REFERENCES sensor_readings(id)
        ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
