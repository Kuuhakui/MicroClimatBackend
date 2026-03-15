import logging
import threading
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import engine, get_db, SessionLocal
from .models import Base
from .routes.sensors import SensorRoutes
from .routes.buildings import BuildingRoutes
from .routes.rooms import RoomRoutes
from . import crud, schemas
from .rabbitmq_consumer import RabbitMQConsumer
from .backup_restore import export_db_to_json, import_json_to_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rabbitmq_consumer = RabbitMQConsumer()

BACKUP_FILE_PATH = os.getenv("BACKUP_FILE_PATH", "backups/database_backup.json")
BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", "60"))
stop_backup_event = threading.Event()

def periodic_backup():
    while not stop_backup_event.is_set():
        stop_backup_event.wait(BACKUP_INTERVAL)
        if stop_backup_event.is_set():
            break
        try:
            db = SessionLocal()
            export_db_to_json(db, BACKUP_FILE_PATH)
            db.close()
        except Exception as e:
            logger.error(f"Error during periodic backup: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Сначала создаем схему
    Base.metadata.create_all(bind=engine)
    
    # 2. Инициализируем данные из бекапа при необходимости
    db = SessionLocal()
    try:
        import_json_to_db(db, BACKUP_FILE_PATH)
    finally:
        db.close()

    # 3. Запускаем фоновый процесс периодического архивирования (выгрузки данных)
    backup_thread = threading.Thread(target=periodic_backup, daemon=True)
    backup_thread.start()
    logger.info("Periodic JSON backup thread started")

    # 4. Запуск RabbitMQ Consumer в отдельном потоке
    consumer_thread = threading.Thread(target=rabbitmq_consumer.start_consuming, daemon=True)
    consumer_thread.start()
    logger.info("RabbitMQ Consumer thread started")
    
    yield
    
    # Остановка консьюмера при завершении
    stop_backup_event.set()
    if rabbitmq_consumer.channel:
        rabbitmq_consumer.channel.stop_consuming()
    consumer_thread.join(timeout=2)
    backup_thread.join(timeout=2)
    
    # Финальный дамп при остановке
    db = SessionLocal()
    try:
        export_db_to_json(db, BACKUP_FILE_PATH)
    finally:
        db.close()
        
    logger.info("Service stopped and final backup created")

app = FastAPI(
    title="Data Storage Service",
    description="Управление взаимодействием с базой данных PostgreSQL и хранение исторических данных.",
    lifespan=lifespan
)

app.include_router(SensorRoutes(prefix="/data/sensors").router)
app.include_router(BuildingRoutes(prefix="/data/buildings").router)
app.include_router(RoomRoutes(prefix="/data/rooms").router)

@app.post("/data", response_model=schemas.SensorMeasurement)
def create_data(measurement: schemas.SensorMeasurementCreate, db: Session = Depends(get_db)):
    return crud.create_sensor_measurement(db=db, measurement=measurement)

@app.get("/data/measurements/")
def get_measurements(
    skip: int = 0,
    limit: int = 500,
    from_time: str = None,
    to_time: str = None,
    db: Session = Depends(get_db)
):
    """Измерения датчиков с опциональной фильтрацией по времени"""
    from .models import SensorMeasurement
    from datetime import datetime, timezone
    query = db.query(SensorMeasurement)
    if from_time:
        try:
            dt = datetime.fromisoformat(from_time.replace("Z", "+00:00")).replace(tzinfo=None)
            query = query.filter(SensorMeasurement.measured_at >= dt)
        except Exception:
            pass
    if to_time:
        try:
            dt = datetime.fromisoformat(to_time.replace("Z", "+00:00")).replace(tzinfo=None)
            query = query.filter(SensorMeasurement.measured_at <= dt)
        except Exception:
            pass
    measurements = query.order_by(SensorMeasurement.measured_at.asc()).offset(skip).limit(limit).all()
    return [
        {
            "id": m.id,
            "sensor_id": str(m.sensor_id),
            "value": m.value,
            "measured_at": m.measured_at.isoformat() if m.measured_at else None
        }
        for m in measurements
    ]

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