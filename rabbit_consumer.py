
import asyncio
import aio_pika
import json
import os
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client import WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = os.getenv("RABBITMQ_MESSAGE_QUEUE_NAME")

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            # Decode and parse the message
            body = message.body.decode("utf-8")
            payload = json.loads(body)
            print("📩 Received message:", payload)

            point = (
            Point("url_clicks")
            .tag("short_url", payload["short_url"])
            .tag("browser", payload["browser"])
            .tag("os", payload["os"])
            .tag("device", payload["device"])
            .tag("referrer", payload["referrer"])
            .field("click",1)
             .time(datetime.now(timezone.utc), WritePrecision.NS) 
            )

            
            x = write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            print(x)


        except Exception as e:
            print("❌ Error handling message:", e)

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    queue = await channel.declare_queue(QUEUE_NAME,durable=True)
    
    # Start consuming messages
    print("🚀 Waiting for messages...")
    await queue.consume(handle_message)

    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
