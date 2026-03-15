from fastapi import FastAPI, HTTPException, Depends, APIRouter
import logging
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

import psycopg2
from psycopg2 import pool
from contextlib import asynccontextmanager

db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname=os.getenv("DB_NAME", "my_database"),
            user=os.getenv("DB_USER", "user"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        logger.info("DB Pool initialized")
    except Exception as e:
        logger.error(f"Failed to init DB pool: {e}")
    yield
    if db_pool:
        db_pool.closeall()
        logger.info("DB Pool closed")

def get_db_conn():
    if not db_pool:
        raise HTTPException(status_code=503, detail="DB Connection Pool not initialized")
    return db_pool.getconn()

app = FastAPI(title="Core Service", description="Центральная бизнес-логика и системные настройки.", lifespan=lifespan)
core_router = APIRouter(prefix="/core", tags=["Core"])
# logger.info("Core Service запущен.")

@core_router.get("/")
async def root():
    return {"message": "Core Service is running"}

@core_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# === Управление ML-моделями ===

class ModelConfig(BaseModel):
    model_id: str
    version: str
    is_active: bool = True
    hyperparameters: Dict[str, Any] = {}

ml_models = {}

@core_router.post("/models/config")
async def create_model_config(config: ModelConfig):
    ml_models[config.model_id] = config.dict()
    logger.info(f"Конфигурация модели создана: {config.model_id}")
    return {"message": "Конфигурация модели создана", "model_id": config.model_id}

@core_router.get("/models/config/{model_id}")
async def get_model_config(model_id: str):
    if model_id not in ml_models:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    return ml_models[model_id]

@core_router.put("/models/config/{model_id}")
async def update_model_config(model_id: str, config: ModelConfig):
    if model_id not in ml_models:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    ml_models[model_id] = config.dict()
    logger.info(f"Конфигурация модели обновлена: {model_id}")
    return {"message": "Конфигурация модели обновлена", "model_id": model_id}

# === Управление уставками (Thresholds) ===

class Threshold(BaseModel):
    sensor_type: str
    min_value: float
    max_value: float
    severity: str = "warning"  # "warning" or "critical"

temperature_thresholds = [
    Threshold(sensor_type="temperature", min_value=18.0, max_value=24.0, severity="warning"),
    Threshold(sensor_type="temperature", min_value=16.0, max_value=26.0, severity="critical"),
]

humidity_thresholds = [
    Threshold(sensor_type="humidity", min_value=30.0, max_value=60.0, severity="warning"),
    Threshold(sensor_type="humidity", min_value=20.0, max_value=70.0, severity="critical"),
]

@core_router.get("/thresholds")
async def get_all_thresholds():
    return {
        "temperature": [t.dict() for t in temperature_thresholds],
        "humidity": [h.dict() for h in humidity_thresholds]
    }

@core_router.post("/thresholds/{sensor_type}")
async def create_threshold(sensor_type: str, threshold: Threshold):
    threshold_list = temperature_thresholds if sensor_type == "temperature" else humidity_thresholds
    threshold_list.append(threshold)
    logger.info(f"Новый порог для {sensor_type} установлен: {threshold.dict()}")
    return {"message": "Порог установлен"}

# === Кэширование системных данных ===

cached_system_data: Dict[str, Any] = {
    "last_ml_training": "2023-10-27T10:00:00Z",
    "system_version": "1.0.0",
    "maintenance_mode": False
}

@core_router.get("/cache/{key}")
async def get_cached_data(key: str):
    if key not in cached_system_data:
        raise HTTPException(status_code=404, detail="Данные не найдены в кэше")
    return {"key": key, "value": cached_system_data[key]}

@core_router.post("/cache/{key}")
async def set_cached_data(key: str, value: Any):
    cached_system_data[key] = value
    logger.info(f"Кэшированы системные данные: {key}")
    return {"message": "Данные кэшированы"}

# === Управление Feature Flags ===

feature_flags = {
    "enable_realtime_prediction": True,
    "enable_advanced_analytics": False,
    "enable_mobile_notifications": True
}

class FeatureFlag(BaseModel):
    flag_name: str
    enabled: bool

@core_router.get("/features")
async def get_all_features():
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name, is_enabled FROM feature_flags")
        flags = cur.fetchall()
        return {row[0]: row[1] for row in flags}
    except Exception as e:
        logger.error(f"Error fetching features: {e}")
        return {}
    finally:
        cur.close()
        db_pool.putconn(conn)

@core_router.post("/features")
async def set_feature_flag(flag: FeatureFlag):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO feature_flags (name, is_enabled) VALUES (%s, %s) ON CONFLICT (name) DO UPDATE SET is_enabled = EXCLUDED.is_enabled",
            (flag.flag_name, flag.enabled)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error setting feature flag: {e}")
        raise HTTPException(status_code=500, detail="Error setting feature flag")
    finally:
        cur.close()
        db_pool.putconn(conn)
    
    logger.info(f"Feature flag обновлен: {flag.flag_name} = {flag.enabled}")
    return {"message": "Feature flag обновлен"}

app.include_router(core_router)