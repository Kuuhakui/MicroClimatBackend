from pydantic import BaseModel
import datetime

class EventLogBase(BaseModel):
    service: str
    event_type: str
    message: str

class EventLogCreate(EventLogBase):
    pass

class EventLog(EventLogBase):
    id: int
    timestamp: datetime.datetime

    class Config:
        orm_mode = True
