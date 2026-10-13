
from concurrent import futures
import logging
import sys
import uuid
from pathlib import Path

import grpc

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

import agroconnect_pb2
import agroconnect_pb2_grpc


def evaluate_reading(reading):
    alerts = []

    # Prototype rule: low soil moisture.
    if reading.soil_moisture < 30:
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

    # Prototype rule: high temperature.
    if reading.temperature > 35:
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

    # Prototype rule: unusual air humidity.
    if reading.air_humidity < 20:
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
    elif reading.air_humidity > 85:
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

    return alerts


class AgroConnectService(
    agroconnect_pb2_grpc.AgroConnectServiceServicer
):
    
    def SendReading(self, request, context):
        if not request.sensor_id.strip():
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "The sensor ID cannot be empty."
            )

        if not request.crop_id.strip():
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "The crop ID cannot be empty."
            )

        if not 0 <= request.soil_moisture <= 100:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Soil moisture must be between 0 and 100."
            )

        if not 0 <= request.air_humidity <= 100:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Air humidity must be between 0 and 100."
            )

        if not -50 <= request.temperature <= 70:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Temperature is outside the accepted range."
            )

        # Call the independent alert microservice.
        try:
            with grpc.insecure_channel(
                "localhost:50052"
            ) as channel:
                alert_stub = (
                    agroconnect_pb2_grpc.AlertServiceStub(channel)
                )

                alert_response = alert_stub.EvaluateReading(
                    request,
                    timeout=5
                )

        except grpc.RpcError as error:
            context.abort(
                grpc.StatusCode.UNAVAILABLE,
                f"Alert service unavailable: {error.code().name}"
            )

        reading_id = str(uuid.uuid4())

        print("\n--- New agricultural reading ---")
        print(f"Sensor: {request.sensor_id}")
        print(f"Crop: {request.crop_id}")
        print(f"Soil moisture: {request.soil_moisture}%")
        print(f"Temperature: {request.temperature} C")
        print(f"Air humidity: {request.air_humidity}%")
        print(f"Alerts received: {len(alert_response.alerts)}")

        return agroconnect_pb2.ReadingResponse(
            success=True,
            message="Agricultural reading processed successfully.",
            reading_id=reading_id,
            alerts=alert_response.alerts
        )



def serve():
    logging.basicConfig(level=logging.INFO)

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10)
    )

    agroconnect_pb2_grpc.add_AgroConnectServiceServicer_to_server(
        AgroConnectService(),
        server
    )

    port = server.add_insecure_port("[::]:50051")

    if port == 0:
        raise RuntimeError("Could not bind the gRPC server port.")

    server.start()

    print("AgroConnect gRPC server is running on port 50051.")
    print("Waiting for sensor readings...")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nStopping AgroConnect gRPC server...")
        server.stop(grace=2).wait()


if __name__ == "__main__":
    serve()
