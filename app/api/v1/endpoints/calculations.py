from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List  # اضافه کردن List

router = APIRouter()

class CalculationRequest(BaseModel):
    items: List[Dict[str, Any]]
    project_id: int
    parameters: Dict[str, float] = {}

class CalculationResponse(BaseModel):
    success: bool
    total_cost: float
    breakdown: Dict[str, float]
    details: List[Dict[str, Any]]

@router.post("/calculations/estimate", response_model=CalculationResponse)
def calculate_estimation(request: CalculationRequest):
    """Calculate construction estimation for Flutter"""
    try:
        # محاسبات متره و برآورد
        result = {
            "success": True,
            "total_cost": 15000000,
            "breakdown": {
                "materials": 10000000,
                "labor": 4000000,
                "equipment": 1000000,
                "tax": 1500000
            },
            "details": [
                {
                    "id": 1,
                    "name": "سیمان",
                    "quantity": 100,
                    "unit": "کیسه",
                    "unit_price": 120000,
                    "total_price": 12000000
                },
                {
                    "id": 2,
                    "name": "آجر",
                    "quantity": 5000,
                    "unit": "عدد",
                    "unit_price": 2500,
                    "total_price": 12500000
                }
            ]
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

