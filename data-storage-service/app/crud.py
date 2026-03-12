from sqlalchemy.orm import Session
from . import models, schemas

def get_sensor(db: Session, sensor_id: str):
    return db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()

def get_sensors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sensor).offset(skip).limit(limit).all()

def create_sensor(db: Session, sensor: schemas.SensorCreate):
    db_sensor = models.Sensor(**sensor.dict())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor

def update_sensor(db: Session, sensor: schemas.SensorCreate, sensor_id: str):
    db_sensor = get_sensor(db, sensor_id)
    if db_sensor:
        update_data = sensor.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_sensor, key, value)
        db.add(db_sensor)
        db.commit()
        db.refresh(db_sensor)
    return db_sensor

def delete_sensor(db: Session, sensor_id: str):
    db_sensor = get_sensor(db, sensor_id)
    if db_sensor:
        db.delete(db_sensor)
        db.commit()
    return db_sensor

# CRUD for Buildings
def get_building(db: Session, building_id: str):
    return db.query(models.Building).filter(models.Building.id == building_id).first()

def get_buildings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Building).offset(skip).limit(limit).all()

def create_building(db: Session, building: schemas.BuildingCreate):
    db_building = models.Building(**building.dict())
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building

# CRUD for Rooms
def get_room(db: Session, room_id: str):
    return db.query(models.Room).filter(models.Room.id == room_id).first()

def get_rooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Room).offset(skip).limit(limit).all()

def create_room(db: Session, room: schemas.RoomCreate):
    db_room = models.Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

# CRUD for Sensor Measurements
def create_sensor_measurement(db: Session, measurement: schemas.SensorMeasurementCreate):
    db_measurement = models.SensorMeasurement(**measurement.dict())
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement