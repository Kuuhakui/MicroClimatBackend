from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, crud
from ..database import get_db

class BuildingRoutes:
    def __init__(self, prefix: str = "/buildings", tags: list = ["Buildings"]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.router.add_api_route("/", self.get_buildings, methods=["GET"], response_model=list[schemas.Building])
        self.router.add_api_route("/", self.create_building, methods=["POST"], response_model=schemas.Building)
        self.router.add_api_route("/{building_id}", self.get_building, methods=["GET"], response_model=schemas.Building)

    def get_buildings(self, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
        buildings = crud.get_buildings(db, skip=skip, limit=limit)
        return buildings

    def get_building(self, building_id: str, db: Session = Depends(get_db)):
        db_building = crud.get_building(db, building_id=building_id)
        if db_building is None:
            raise HTTPException(status_code=404, detail="Building not found")
        return db_building

    def create_building(self, building: schemas.BuildingCreate, db: Session = Depends(get_db)):
        return crud.create_building(db=db, building=building)
