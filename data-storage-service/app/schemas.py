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