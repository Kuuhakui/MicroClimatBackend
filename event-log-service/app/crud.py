from sqlalchemy.orm import Session
from . import models, schemas

def create_event(db: Session, event: schemas.EventLogCreate):
    db_event = models.EventLog(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.EventLog).offset(skip).limit(limit).all()
