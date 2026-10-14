
from concurrent import futures
import os
import logging
import sys
import uuid
from pathlib import Path

import grpc

# Add backend/app to the Python module search path.
APP_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, APP_DIR)

import agroconnect_pb2
import agroconnect_pb2_grpc
from database import save_reading


class AgroConnectService(
    agroconnect_pb2_grpc.AgroConnectServiceServicer
):
    def SendReading(self, request, context):
        # Validate sensor identification.
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

        # Validate measurement values.
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

        # Request alert evaluation from the independent service.
        try:
            with grpc.insecure_channel(
    f"{os.getenv('ALERT_SERVICE_HOST', 'localhost')}:50052"
) as channel:
                alert_stub = (
                    agroconnect_pb2_grpc.AlertServiceStub(channel)
                )

                alert_response = alert_stub.EvaluateReading(
                    request,
                    timeout=5
                )

        except grpc.RpcError as error:
            logging.exception("Alert service request failed")
            context.abort(
                grpc.StatusCode.UNAVAILABLE,
                f"Alert service unavailable: {error.code().name}"
            )

        reading_id = str(uuid.uuid4())

        # Save the reading and its alerts to PostgreSQL.
        try:
            save_reading(
                request,
                reading_id,
                alert_response.alerts
            )
        except Exception:
            logging.exception(
                "Could not save agricultural reading to PostgreSQL"
            )
            context.abort(
                grpc.StatusCode.INTERNAL,
                "The reading could not be saved."
            )

        print("\n--- New agricultural reading ---")
        print(f"Sensor: {request.sensor_id}")
        print(f"Crop: {request.crop_id}")
        print(f"Soil moisture: {request.soil_moisture}%")
        print(f"Temperature: {request.temperature} C")
        print(f"Air humidity: {request.air_humidity}%")
        print(f"Alerts received: {len(alert_response.alerts)}")
        print("Reading and alerts saved to PostgreSQL.")

        return agroconnect_pb2.ReadingResponse(
            success=True,
            message="Agricultural reading processed and saved successfully.",
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
