import time
import json
import logging
import random
import requests
from uuid import uuid4

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SensorSimulator")

import os

INGESTION_URL = os.getenv("INGESTION_URL", "http://localhost:8004/sensors")
DATA_STORAGE_URL = os.getenv("DATA_STORAGE_URL", "http://localhost:8003/sensors")
ROOM_ID = "00000000-0000-0000-0000-000000000001" # Fake room id for testing

# Мы сгенерируем 4 физических датчика:
# 1. Датчик температуры и влажности (комбинированный)
# 2. Только датчик температуры
# 3. Только датчик влажности
SENSORS = [
    {"id": "11111111-1111-1111-1111-111111111111", "type": "temp_hum", "name": "Комбинированный (T+H)", "db_type_id": 1},
    {"id": "22222222-2222-2222-2222-222222222222", "type": "temp", "name": "Датчик Температуры", "db_type_id": 1},
    {"id": "33333333-3333-3333-3333-333333333333", "type": "hum", "name": "Датчик Влажности", "db_type_id": 2}
]

def register_sensors_in_db():
    pass
    # В реальном сценарии, здесь был бы запрос в data-storage-service
    # для уверенности, что датчики существуют в PostgreSQL,
    # чтобы избежать ошибок Foreign Key constraint. 
    # В данный момент мы пропускаем, предполагая, что они создаются либо миграциями
    # либо другим путем. Но этот скрипт генерирует случайные UUID каждый запуск.
    # Так как мы тестируем потоковую передачу - пока оставим генерацию UUID.
    # Позже, при тестировании полного потока с БД, нам понадобится этот функционал.


def generate_sensor_data(sensor):
    base_temp = 22.0
    base_hum = 45.0
    
    data = {
        "sensor_id": sensor["id"]
    }
    
    if sensor["type"] == "temp_hum":
        data["temperature"] = round(base_temp + random.uniform(-2.0, 2.0), 2)
        data["humidity"] = round(base_hum + random.uniform(-5.0, 5.0), 2)
    elif sensor["type"] == "temp":
        data["temperature"] = round(base_temp + random.uniform(-2.0, 2.0), 2)
    elif sensor["type"] == "hum":
        data["humidity"] = round(base_hum + random.uniform(-5.0, 5.0), 2)
        
    return data

def main():
    logger.info("Starting Sensor Simulator...")
    # register_sensors_in_db()
    
    while True:
        for sensor in SENSORS:
            payload = generate_sensor_data(sensor)
            
            try:
                response = requests.post(INGESTION_URL, json=payload, timeout=2)
                if response.status_code == 200:
                    logger.info(f"Successfully sent data for {sensor['name']}: {payload}")
                else:
                    logger.warning(f"Failed to send data for {sensor['name']}. Status: {response.status_code}, Response: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error connecting to {INGESTION_URL}: {e}")
                
        time.sleep(5) # Отправка данных каждые 5 секунд

if __name__ == "__main__":
    main()
