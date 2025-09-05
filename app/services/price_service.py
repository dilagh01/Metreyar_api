import math
import json
from sqlalchemy.orm import Session
from app.models.price_list import PriceItem, Formula, CoefficientTable

class PriceService:
    
    @staticmethod
    def calculate_item_price(item_code: str, quantities: dict, db: Session):
        item = db.query(PriceItem).filter(PriceItem.code == item_code).first()
        if not item:
            return None
        
        if item.formula:
            # محاسبه با فرمول
            return PriceService._calculate_with_formula(item, quantities)
        else:
            # محاسبه ساده
            return item.unit_price * quantities.get('quantity', 1)
    
    @staticmethod
    def _calculate_with_formula(item: PriceItem, quantities: dict):
        try:
            # اجرای فرمول
            formula = item.formula
            variables = {**quantities, **(item.parameters or {})}
            
            # جایگزینی متغیرها در فرمول
            for var_name, var_value in variables.items():
                formula = formula.replace(f'{{{var_name}}}', str(var_value))
            
            # محاسبه نتیجه
            result = eval(formula, {"__builtins__": None}, {"math": math})
            return result
            
        except Exception as e:
            raise ValueError(f"خطا در محاسبه فرمول: {e}")
    
    @staticmethod
    def get_coefficient(table_name: str, key: str, db: Session):
        table = db.query(CoefficientTable).filter(CoefficientTable.name == table_name).first()
        if not table or not table.table_data:
            return None
        
        return table.table_data.get(key)
