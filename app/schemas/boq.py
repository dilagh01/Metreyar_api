from pydantic import BaseModel
from typing import List, Optional

class BOQRow(BaseModel):
    id: Optional[int]
    price_item_id: int
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: Optional[float] = 0

class BOQRequest(BaseModel):
    project_id: int
    boq: List[BOQRow]

class BOQResponse(BaseModel):
    project_id: int
    total_cost: float
    boq: List[BOQRow]
