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

app = FastAPI(title="Core Service", description="Центральная бизнес-логика и системные настройки.")
core_router = APIRouter(prefix="/core", tags=["Core"])

@core_router.on_event("startup")
async def startup_event():
    logger.info("Core Service запущен.")

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
    return feature_flags

@core_router.post("/features")
async def set_feature_flag(flag: FeatureFlag):
    feature_flags[flag.flag_name] = flag.enabled
    logger.info(f"Feature flag обновлен: {flag.flag_name} = {flag.enabled}")
    return {"message": "Feature flag обновлен"}

app.include_router(core_router)