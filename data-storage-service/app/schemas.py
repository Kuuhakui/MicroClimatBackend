from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --- Схемы Sensor ---
class SensorTypeBase(BaseModel):
    name: str
    unit: Optional[str] = None

class SensorTypeCreate(SensorTypeBase):
    pass
class SensorType(SensorTypeBase):
    id: int
    class Config:
        from_attributes = True

class SensorBase(BaseModel):
    room_id: str  # UUID as string
    type_id: int
    model_name: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    status: Optional[str] = "active"

class SensorCreate(SensorBase):
    pass
class Sensor(SensorBase):
    id: str  # UUID as string
    class Config:
        from_attributes = True

# --- Схемы Measurements ---
class SensorMeasurementBase(BaseModel):
    sensor_id: str  # UUID as string
    value: float
    measured_at: datetime

class SensorMeasurementCreate(SensorMeasurementBase):
    pass
class SensorMeasurement(SensorMeasurementBase):
    id: int
    class Config:
        from_attributes = True

# --- Схемы для room-management-service ---
class BuildingBase(BaseModel):
    name: str
    address: Optional[str] = None

class BuildingCreate(BuildingBase):
    pass

class Building(BuildingBase):
    id: str # UUID as string

    class Config:
        from_attributes = True

class RoomBase(BaseModel):
    building_id: str # UUID as string
    name: str
    floor: int
    plan_image_url: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: str # UUID as string

    class Config:
        from_attributes = True

# --- Схемы для sensor-ingestion-service ---
class SensorData(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float