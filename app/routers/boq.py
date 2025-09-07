from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.schemas.boq import BOQRequest, BOQResponse, BOQRow
from app.services.calculation import calculate_boq_total

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/calculate", response_model=BOQResponse)
def calculate_boq(data: BOQRequest):
    total = calculate_boq_total(data.boq)
    return BOQResponse(project_id=data.project_id, total_cost=total, boq=data.boq)
