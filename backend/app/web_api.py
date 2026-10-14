
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

app = FastAPI(
    title="AgroConnect API",
    description="Agricultural monitoring dashboard API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "agroconnect_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.environ["PGPASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AgroConnect API"}


@app.get("/api/dashboard")
def dashboard():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) AS total_readings,
                        COUNT(DISTINCT sensor_id) AS total_sensors,
                        ROUND(AVG(soil_moisture)::numeric, 1)
                            AS avg_soil_moisture,
                        ROUND(AVG(temperature)::numeric, 1)
                            AS avg_temperature,
                        ROUND(AVG(air_humidity)::numeric, 1)
                            AS avg_air_humidity
                    FROM sensor_readings
                """)
                stats = cur.fetchone()

                cur.execute("""
                    SELECT COUNT(*) AS total_alerts
                    FROM agricultural_alerts
                """)
                alerts = cur.fetchone()

                cur.execute("""
                    SELECT COUNT(*) AS critical_alerts
                    FROM agricultural_alerts
                    WHERE severity = 'high'
                """)
                critical = cur.fetchone()

        return {
            **stats,
            "total_alerts": alerts["total_alerts"],
            "critical_alerts": critical["critical_alerts"],
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve dashboard data.",
        )


@app.get("/api/readings")
def readings(limit: int = Query(default=20, ge=1, le=100)):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        r.id,
                        r.sensor_id,
                        r.crop_id,
                        r.soil_moisture,
                        r.temperature,
                        r.air_humidity,
                        r.recorded_at,
                        r.created_at,
                        COUNT(a.id) AS alert_count
                    FROM sensor_readings r
                    LEFT JOIN agricultural_alerts a
                        ON a.reading_id = r.id
                    GROUP BY r.id
                    ORDER BY r.created_at DESC
                    LIMIT %s
                """, (limit,))

                return cur.fetchall()

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve readings.",
        )


@app.get("/api/alerts")
def alerts(limit: int = Query(default=20, ge=1, le=100)):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        a.id,
                        a.reading_id,
                        a.alert_type,
                        a.severity,
                        a.message,
                        a.created_at,
                        r.sensor_id,
                        r.crop_id,
                        r.soil_moisture
                    FROM agricultural_alerts a
                    JOIN sensor_readings r
                        ON r.id = a.reading_id
                    ORDER BY a.created_at DESC
                    LIMIT %s
                """, (limit,))

                return cur.fetchall()

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve alerts.",
        )
