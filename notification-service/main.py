from fastapi import FastAPI, HTTPException
import redis.asyncio as redis
import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Notification Service")

REDIS_HOST = os.getenv("REDIS_HOST", "redis-broker")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://core-service:8002")
EVENT_LOG_SERVICE_URL = os.getenv("EVENT_LOG_SERVICE_URL", "http://event-log-service:8008")

async def get_thresholds():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CORE_SERVICE_URL}/core/thresholds")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Error requesting thresholds from core-service: {e}")
            return None

async def log_event(event_type: str, message: str):
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "service": "notification-service",
                "event_type": event_type,
                "message": message
            }
            response = await client.post(f"{EVENT_LOG_SERVICE_URL}/events/", json=payload)
            response.raise_for_status()
            print(f"Successfully logged event: {event_type}")
        except httpx.RequestError as e:
            print(f"Error logging event to event-log-service: {e}")

async def redis_listener():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("sensor_data", "prediction_results")
    print("Subscribed to sensor_data and prediction_results channels")
    while True:
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                print(f"Received message on {message['channel']}: {message['data']}")
                
                if message['channel'] == "sensor_data":
                    data = json.loads(message['data'])
                    thresholds = await get_thresholds()
                    if thresholds and 'temperature' in data and data['temperature'] is not None:
                        temp = float(data['temperature'])
                        # thresholds is dict like {"temperature": [{"max_value": 24.0, ...}, ...]}
                        temp_thresholds = thresholds.get('temperature', [])
                        
                        for thr in temp_thresholds:
                            max_val = thr.get('max_value')
                            min_val = thr.get('min_value')
                            
                            if max_val is not None and temp > max_val:
                                msg = f"NOTIFICATION: Temperature {temp} exceeds max threshold {max_val} ({thr.get('severity')})"
                                print(msg)
                                await log_event("THRESHOLD_EXCEEDED", msg)
                                
                            if min_val is not None and temp < min_val:
                                msg = f"NOTIFICATION: Temperature {temp} is below min threshold {min_val} ({thr.get('severity')})"
                                print(msg)
                                await log_event("THRESHOLD_EXCEEDED", msg)
                
                elif message['channel'] == "prediction_results":
                    data = json.loads(message['data'])
                    print(f"Received ML Prediction: {data}")
                    # В будущем тут можно задавать отдельные алерты для предсказаний
                    
        except json.JSONDecodeError:
            print("Could not decode message data")
        except Exception as e:
            print(f"Redis listener error: {e}")
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

@app.get("/")
def read_root():
    return {"Hello": "Notification Service"}
