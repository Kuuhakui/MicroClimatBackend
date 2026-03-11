from fastapi import FastAPI, HTTPException  # Добавили HTTPException
import logging
from sqlalchemy import text  # Добавили text для SQL-запросов
from .database import engine
from .models import Base
from .routes.sensors import SensorRoutes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Data Storage Service", 
    description="Управление взаимодействием с базой данных PostgreSQL и хранение исторических данных."
)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Подключение маршрутов
sensor_routes = SensorRoutes()
app.include_router(sensor_routes.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Сервис хранения данных запущен.")

@app.get("/")
async def root():
    return {"message": "Data Storage Service is running"}

@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса и подключения к базе данных.
    """
    try:
        # Теперь 'text' и 'engine' определены
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Теперь 'HTTPException' определен
        raise HTTPException(status_code=503, detail="Database connection failed")