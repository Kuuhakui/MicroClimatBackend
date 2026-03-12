from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, crud
from ..database import get_db

class RoomRoutes:
    def __init__(self, prefix: str = "/rooms", tags: list = ["Rooms"]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.router.add_api_route("/", self.get_rooms, methods=["GET"], response_model=list[schemas.Room])
        self.router.add_api_route("/", self.create_room, methods=["POST"], response_model=schemas.Room)
        self.router.add_api_route("/{room_id}", self.get_room, methods=["GET"], response_model=schemas.Room)

    def get_rooms(self, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
        rooms = crud.get_rooms(db, skip=skip, limit=limit)
        return rooms

    def get_room(self, room_id: str, db: Session = Depends(get_db)):
        db_room = crud.get_room(db, room_id=room_id)
        if db_room is None:
            raise HTTPException(status_code=404, detail="Room not found")
        return db_room

    def create_room(self, room: schemas.RoomCreate, db: Session = Depends(get_db)):
        return crud.create_room(db=db, room=room)
