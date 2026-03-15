from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine, get_db
import logging
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Log Service", description="Централизованное логирование системных событий и аудита.")

# Роутер с префиксом /events для корректной работы через API Gateway
events_router = APIRouter(prefix="/events", tags=["Events"])

@app.on_event("startup")
async def startup_event():
    logger.info("Сервис логирования событий запущен.")

@events_router.post("/", response_model=schemas.EventLog)
def create_event(event: schemas.EventLogCreate, db: Session = Depends(get_db)):
    return crud.create_event(db=db, event=event)

@events_router.get("/", response_model=list[schemas.EventLog])
def read_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    events = crud.get_events(db, skip=skip, limit=limit)
    return events

@app.get("/")
async def root():
    return {"message": "Event Log Service is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(events_router)