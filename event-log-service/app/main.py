from fastapi import FastAPI, HTTPException
import logging
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

app = FastAPI(title="Event Log Service", description="Централизованное логирование системных событий и аудита.")

@app.on_event("startup")
async def startup_event():
    logger.info("Сервис логирования событий запущен.")

@app.get("/")
async def root():
    return {"message": "Event Log Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}