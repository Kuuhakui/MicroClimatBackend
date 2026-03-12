from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class BuildingBase(BaseModel):
    name: str
    address: Optional[str] = None

class BuildingCreate(BuildingBase):
    pass

class Building(BuildingBase):
    id: UUID

    class Config:
        from_attributes = True


class RoomBase(BaseModel):
    building_id: UUID
    name: str
    floor: int
    plan_image_url: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class Room(RoomBase):
    id: UUID

    class Config:
        from_attributes = True


class SensorBase(BaseModel):
    room_id: UUID
    type_id: int
    model_name: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    status: Optional[str] = "active"

class SensorCreate(SensorBase):
    pass

class Sensor(SensorBase):
    id: UUID

    class Config:
        from_attributes = True
