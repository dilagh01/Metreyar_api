from pydantic import BaseModel
from typing import List, Optional

class AnalysisComponent(BaseModel):
    id: Optional[int] = None
    boq_item_id: int
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: Optional[float] = 0

class AnalysisRequest(BaseModel):
    boq_item_id: int
    components: List[AnalysisComponent]

class AnalysisResponse(BaseModel):
    boq_item_id: int
    total_cost: float
    components: List[AnalysisComponent]
