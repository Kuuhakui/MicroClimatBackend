import json
import os
import pika
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as aioredis
from typing import Optional

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-broker:6379")
DATA_STORAGE_URL = os.getenv("DATA_STORAGE_URL", "http://data-storage-service:8003")

class SensorData(BaseModel):
    sensor_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None

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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"RabbitMQ error: {str(e)}")

    # 3. Publish to Redis Pub/Sub (for Prediction & Notifications)
    try:
        r = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await r.publish("sensor_data", data.json())
        await r.aclose()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

    return {"status": "ok"}
