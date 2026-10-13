
import grpc

import agroconnect_pb2
import agroconnect_pb2_grpc


def main():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = agroconnect_pb2_grpc.AgroConnectServiceStub(channel)

        reading = agroconnect_pb2.SensorReading(
            sensor_id="SENSOR-001",
            crop_id="CULTIVO-TOMATE-01",
            soil_moisture=28.5,
            temperature=31.2,
            air_humidity=45.0,
            timestamp=1791849600
        )

        print("Sending agricultural reading...")

        response = stub.SendReading(reading, timeout=10)

        print("\n--- Server response ---")
        print(f"Success: {response.success}")
        print(f"Message: {response.message}")
        print(f"Reading ID: {response.reading_id}")

        if response.alerts:
            print("\n--- Agricultural alerts ---")

            for alert in response.alerts:
                print(f"Type: {alert.alert_type}")
                print(f"Severity: {alert.severity}")
                print(f"Message: {alert.message}")
                print("-" * 40)
        else:
            print("\nNo alerts detected.")


if __name__ == "__main__":
    main()
