import os
import httpx
from fastapi import FastAPI, HTTPException
from . import schemas

app = FastAPI()

DATA_STORAGE_URL = os.getenv("DATA_STORAGE_URL", "http://data-storage-service:8003")

@app.post("/buildings", response_model=schemas.Building)
async def create_building(building: schemas.BuildingCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{DATA_STORAGE_URL}/buildings", json=building.dict())
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error communicating with data-storage-service: {exc}")

@app.get("/buildings/{building_id}", response_model=schemas.Building)
async def get_building(building_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DATA_STORAGE_URL}/buildings/{building_id}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error communicating with data-storage-service: {exc}")

@app.post("/rooms", response_model=schemas.Room)
async def create_room(room: schemas.RoomCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{DATA_STORAGE_URL}/rooms", json=room.dict())
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error communicating with data-storage-service: {exc}")

@app.get("/rooms/{room_id}", response_model=schemas.Room)
async def get_room(room_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DATA_STORAGE_URL}/rooms/{room_id}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error communicating with data-storage-service: {exc}")

@app.post("/sensors", response_model=schemas.Sensor)
async def create_sensor(sensor: schemas.SensorCreate):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{DATA_STORAGE_URL}/sensors", json=sensor.dict())
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error communicating with data-storage-service: {exc}")

@app.get("/sensors/{sensor_id}", response_model=schemas.Sensor)
async def get_sensor(sensor_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DATA_STORAGE_URL}/sensors/{sensor_id}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error communicating with data-storage-service: {exc}")
