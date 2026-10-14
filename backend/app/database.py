
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def save_reading(reading, reading_id, alerts):
    timestamp = (
        datetime.fromtimestamp(
            reading.timestamp,
            tz=timezone.utc
        )
        if reading.timestamp > 0
        else datetime.now(timezone.utc)
    )

    connection_config = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE", "agroconnect_db"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.environ["PGPASSWORD"],
        "connect_timeout": 5,
    }

    with psycopg.connect(**connection_config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sensor_readings (
                    id, sensor_id, crop_id,
                    soil_moisture, temperature,
                    air_humidity, recorded_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    reading_id,
                    reading.sensor_id,
                    reading.crop_id,
                    reading.soil_moisture,
                    reading.temperature,
                    reading.air_humidity,
                    timestamp,
                ),
            )

            for alert in alerts:
                cursor.execute(
                    """
                    INSERT INTO agricultural_alerts (
                        reading_id, alert_type,
                        severity, message
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        reading_id,
                        alert.alert_type,
                        alert.severity,
                        alert.message,
                    ),
                )

    print("Reading and alerts saved to PostgreSQL.")
