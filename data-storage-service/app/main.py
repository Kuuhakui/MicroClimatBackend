import logging
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import Base
from .routes.sensors import SensorRoutes
from .routes.buildings import BuildingRoutes
from .routes.rooms import RoomRoutes
from . import crud, schemas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Storage Service",
    description="Управление взаимодействием с базой данных PostgreSQL и хранение исторических данных."
)

Base.metadata.create_all(bind=engine)

app.include_router(SensorRoutes().router)
app.include_router(BuildingRoutes().router)
app.include_router(RoomRoutes().router)

@app.post("/data", response_model=schemas.SensorMeasurement)
def create_data(measurement: schemas.SensorMeasurementCreate, db: Session = Depends(get_db)):
    return crud.create_sensor_measurement(db=db, measurement=measurement)

@app.get("/")
async def root():
    return {"message": "Data Storage Service is running"}

@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса и подключения к базе данных.
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")