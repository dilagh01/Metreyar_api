from fastapi import APIRouter
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.calculation import calculate_total

router = APIRouter()

@router.post("/calculate", response_model=AnalysisResponse)
def calculate_analysis(data: AnalysisRequest):
    total = calculate_total(data.components)
    return AnalysisResponse(boq_item_id=data.boq_item_id, total_cost=total, components=data.components)
