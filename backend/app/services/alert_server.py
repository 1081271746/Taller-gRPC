

from concurrent import futures
import sys
from pathlib import Path

import grpc

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

import agroconnect_pb2
import agroconnect_pb2_grpc



class AlertService(
    agroconnect_pb2_grpc.AlertServiceServicer
):
    def EvaluateReading(self, request, context):
        alerts = []

        # Rule 1: Low soil moisture.
        if request.soil_moisture < 30:
            alerts.append(
                agroconnect_pb2.AgriculturalAlert(
                    alert_type="low_soil_moisture",
                    severity="medium",
                    message=(
                        "Soil moisture is below the configured "
                        "30% threshold."
                    )
                )
            )

        # Rule 2: High temperature.
        if request.temperature > 35:
            alerts.append(
                agroconnect_pb2.AgriculturalAlert(
                    alert_type="high_temperature",
                    severity="high",
                    message=(
                        "Temperature exceeds the configured "
                        "35 C threshold."
                    )
                )
            )

        # Rule 3: Low or high air humidity.
        if request.air_humidity < 20:
            alerts.append(
                agroconnect_pb2.AgriculturalAlert(
                    alert_type="low_air_humidity",
                    severity="medium",
                    message=(
                        "Air humidity is below the configured "
                        "20% threshold."
                    )
                )
            )
        elif request.air_humidity > 85:
            alerts.append(
                agroconnect_pb2.AgriculturalAlert(
                    alert_type="high_air_humidity",
                    severity="medium",
                    message=(
                        "Air humidity exceeds the configured "
                        "85% threshold."
                    )
                )
            )

        print("\n--- Alert service evaluation ---")
        print(f"Sensor: {request.sensor_id}")
        print(f"Alerts detected: {len(alerts)}")

        for alert in alerts:
            print(f"[{alert.severity.upper()}] {alert.alert_type}")

        return agroconnect_pb2.AlertResponse(alerts=alerts)


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    agroconnect_pb2_grpc.add_AlertServiceServicer_to_server(
        AlertService(),
        server
    )

    port = server.add_insecure_port("[::]:50052")

    if port == 0:
        raise RuntimeError("Could not bind the alert service port.")

    server.start()

    print("AgroConnect Alert Service running on port 50052.")
    print("Waiting for evaluation requests...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping alert service...")
        server.stop(grace=2).wait()


if __name__ == "__main__":
    serve()
