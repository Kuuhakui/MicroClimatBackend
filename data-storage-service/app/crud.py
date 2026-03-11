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