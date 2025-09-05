from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.services.price_service import PriceService
from app.models.price_list import PriceItem, Formula, CoefficientTable

router = APIRouter()

@router.get("/price-items", response_model=List[Dict[str, Any]])
def get_price_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(PriceItem).offset(skip).limit(limit).all()
    return [
        {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "category": item.category,
            "formula": item.formula,
            "parameters": item.parameters
        }
        for item in items
    ]

@router.post("/calculate")
def calculate_price(calculation_data: dict, db: Session = Depends(get_db)):
    try:
        item_code = calculation_data.get("item_code")
        quantities = calculation_data.get("quantities", {})
        
        result = PriceService.calculate_item_price(item_code, quantities, db)
        
        return {
            "success": True,
            "item_code": item_code,
            "quantities": quantities,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/coefficients/{table_name}/{key}")
def get_coefficient(table_name: str, key: str, db: Session = Depends(get_db)):
    coefficient = PriceService.get_coefficient(table_name, key, db)
    if coefficient is None:
        raise HTTPException(status_code=404, detail="ضریب یافت نشد")
    
    return {"table": table_name, "key": key, "value": coefficient}

@router.get("/formulas")
def get_formulas(db: Session = Depends(get_db)):
    formulas = db.query(Formula).all()
    return [{"id": f.id, "name": f.name, "expression": f.expression} for f in formulas]
