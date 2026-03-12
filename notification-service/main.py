from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Notification Service")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://localhost:8002")

async def get_thresholds():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CORE_SERVICE_URL}/thresholds")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Error requesting thresholds from core-service: {e}")
            return None

async def redis_listener():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    await pubsub.subscribe("sensor_data")
    print("Subscribed to sensor_data channel")
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        if message:
            print(f"Received message: {message['data']}")
            try:
                data = json.loads(message['data'])
                thresholds = await get_thresholds()
                if thresholds:
                    if data['temperature'] > thresholds.get('max_temp', 100):
                        print(f"NOTIFICATION: Temperature {data['temperature']} exceeds max threshold {thresholds['max_temp']}")
                    if data['temperature'] < thresholds.get('min_temp', 0):
                        print(f"NOTIFICATION: Temperature {data['temperature']} is below min threshold {thresholds['min_temp']}")
            except json.JSONDecodeError:
                print("Could not decode message data")
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

@app.get("/")
def read_root():
    return {"Hello": "Notification Service"}
