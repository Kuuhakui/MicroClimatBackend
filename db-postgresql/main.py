import os
import json
import psycopg2
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": "localhost",
    "port": os.getenv("DB_PORT")
}

REQUIRED_TABLES = [
    "roles", "users", "user_preferences", "buildings", "rooms", 
    "room_physical_params", "sensor_types", "sensors", 
    "sensor_measurements", "ml_models", "system_events"
]

def check_db_status():
    status_dict = {}
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        for table in REQUIRED_TABLES:
            cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
            status_dict[table] = cur.fetchone()[0]
        cur.close()
        conn.close()
        logger.info("Статус базы данных успешно проверен.")
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        status_dict = {table: False for table in REQUIRED_TABLES}
    return status_dict

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    tables_status = check_db_status()
    return templates.TemplateResponse("index.html", {"request": request, "tables": tables_status})

@app.post("/init-db")
async def initialize_database():
    sql_path = "init-db/schema.sql"
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cur = conn.cursor()
        with open(sql_path, 'r', encoding='utf-8') as f:
            cur.execute(f.read())
        cur.close()
        conn.close()
        logger.info("Схема базы данных успешно инициализирована.")
        # После создания таблиц возвращаемся на главную
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Запуск сервиса управления базой данных на хосте 0.0.0.0 и порту 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)