import os
import json
import asyncio
import joblib
import pandas as pd
import numpy as np
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Конфигурация
MODEL_PATH = os.getenv("MODEL_PATH", "models/xgboost_final_5y.pkl")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis-broker:6379")

app = FastAPI(title="ML Prediction Service", description="Сервис прогнозирования температуры")

# Глобальная переменная для модели
model = None

class PredictionRequest(BaseModel):
    temp_outdoor: float
    humidity: float
    precipitation: float = 0.0
    cloud_cover: float = 0.0
    # Исторические данные, необходимые для модели
    temp_lag_1h: float
    temp_roll_mean_6h: float
    timestamp: Optional[datetime] = None

@app.on_event("startup")
def load_model():
    global model
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            print(f"✅ Модель загружена: {MODEL_PATH}")
        else:
            print(f"⚠️ Файл модели не найден по пути: {MODEL_PATH}. Предикции будут недоступны.")
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
    
    # Запуск фоновой задачи прослушивания Redis
    asyncio.create_task(redis_listener())

@app.get("/ml/health")
def health_check():
    """Проверка доступности сервиса и модели"""
    return {
        "status": "online",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH
    }

def run_prediction(data: PredictionRequest):
    """Внутренняя функция для расчета прогноза"""
    if not model:
        return None

    current_time = data.timestamp or datetime.now()
    hour = current_time.hour
    
    # Генерация фичей
    features = pd.DataFrame([{
        'temp_outdoor': data.temp_outdoor,
        'humidity': data.humidity,
        'precipitation': data.precipitation,
        'cloud_cover': data.cloud_cover,
        'temp_lag_1h': data.temp_lag_1h,
        'temp_diff': data.temp_outdoor - data.temp_lag_1h,
        'temp_roll_mean_6h': data.temp_roll_mean_6h,
        'temp_sin': np.sin(2 * np.pi * hour / 24),
        'temp_cos': np.cos(2 * np.pi * hour / 24)
    }])
    
    return float(model.predict(features)[0])

async def redis_listener():
    """Фоновая задача: слушает данные от датчиков и публикует прогноз"""
    try:
        r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe("sensor_data")
        print(f"✅ ML Service подписан на Redis канал: sensor_data")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    payload = json.loads(message["data"])
                    # Пример ожидаемых данных от датчика.
                    # В реальности тут может понадобиться запрос в БД за историей (lag_1h)
                    # Для упрощения считаем, что сенсор шлет полный пакет или мы мокаем историю
                    req_data = PredictionRequest(
                        temp_outdoor=payload.get("temperature", 0.0),
                        humidity=payload.get("humidity", 0.0),
                        # Остальные поля берем из payload или дефолтные
                        temp_lag_1h=payload.get("temperature", 0.0), # Временная заглушка
                        temp_roll_mean_6h=payload.get("temperature", 0.0) # Временная заглушка
                    )
                    
                    prediction = run_prediction(req_data)
                    
                    if prediction is not None:
                        # Публикуем результат обратно в Redis
                        result = {
                            "sensor_id": payload.get("sensor_id"),
                            "predicted_temp": prediction,
                            "timestamp": datetime.now().isoformat()
                        }
                        await r.publish("prediction_results", json.dumps(result))
                        print(f"🔮 Прогноз опубликован: {prediction:.2f}°C")
                        
                except Exception as e:
                    print(f"⚠️ Ошибка обработки сообщения Redis: {e}")

    except Exception as e:
        print(f"❌ Ошибка соединения с Redis в ML Service: {e}")

@app.post("/ml/predict")
def predict_endpoint(data: PredictionRequest):
    """
    Прогноз температуры на +1 час.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Модель машинного обучения не загружена")

    try:
        prediction = run_prediction(data)
        return {
            "predicted_temp_next_hour": prediction,
            "model_version": "xgboost_final_5y"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при прогнозировании: {str(e)}")