import json
import os
import pika
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
DATA_STORAGE_URL = os.getenv("DATA_STORAGE_URL", "http://data-storage-service:8003")

class SensorData(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float

@app.post("/sensors")
async def ingest_sensor_data(data: SensorData):
    # 1. Validate data (Pydantic already does a good job)
    
    # 2. Publish to RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue='sensor_data')
        channel.basic_publish(exchange='',
                              routing_key='sensor_data',
                              body=data.json())
        connection.close()
    except pika.exceptions.AMQPConnectionError:
        raise HTTPException(status_code=500, detail="Could not connect to RabbitMQ")

    # 3. Save data via data-storage-service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{DATA_STORAGE_URL}/data", json=data.dict())
            response.raise_for_status()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error communicating with data-storage-service: {exc}")

    return {"status": "ok"}
