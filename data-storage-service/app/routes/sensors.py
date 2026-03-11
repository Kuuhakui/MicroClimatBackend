from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, crud
from ..database import get_db

class SensorRoutes:
    def __init__(self, prefix: str = "/sensors", tags: list = ["Sensors"]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.router.add_api_route("/", self.get_sensors, methods=["GET"])
        self.router.add_api_route("/", self.create_sensor, methods=["POST"])
        self.router.add_api_route("/{sensor_id}", self.get_sensor, methods=["GET"])
        self.router.add_api_route("/{sensor_id}", self.update_sensor, methods=["PUT"])
        self.router.add_api_route("/{sensor_id}", self.delete_sensor, methods=["DELETE"])

    def get_sensors(self, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
        sensors = crud.get_sensors(db, skip=skip, limit=limit)
        return sensors

    def get_sensor(self, sensor_id: str, db: Session = Depends(get_db)):
        db_sensor = crud.get_sensor(db, sensor_id=sensor_id)
        if db_sensor is None:
            raise HTTPException(status_code=404, detail="Sensor not found")
        return db_sensor

    def create_sensor(self, sensor: schemas.SensorCreate, db: Session = Depends(get_db)):
        return crud.create_sensor(db=db, sensor=sensor)

    def update_sensor(self, sensor_id: str, sensor: schemas.SensorCreate, db: Session = Depends(get_db)):
        db_sensor = crud.get_sensor(db, sensor_id=sensor_id)
        if db_sensor is None:
            raise HTTPException(status_code=404, detail="Sensor not found")
        return crud.update_sensor(db=db, sensor=sensor, sensor_id=sensor_id)

    def delete_sensor(self, sensor_id: str, db: Session = Depends(get_db)):
        db_sensor = crud.get_sensor(db, sensor_id=sensor_id)
        if db_sensor is None:
            raise HTTPException(status_code=404, detail="Sensor not found")
        return crud.delete_sensor(db=db, sensor_id=sensor_id)