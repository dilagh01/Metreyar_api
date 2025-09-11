from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get("/items")
def get_items():
    """Get sample items for Flutter"""
    return [
        {
            "id": 1,
            "code": "001.001",
            "name": "حفاری با بیل مکانیکی",
            "unit": "متر مکعب",
            "unit_price": 150000,
            "category": "حفاری"
        },
        {
            "id": 2,
            "code": "002.001",
            "name": "بتن ریزی فونداسیون",
            "unit": "متر مکعب",
            "unit_price": 850000,
            "category": "بتن ریزی"
        }
    ]
