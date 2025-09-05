from app.core.database import SessionLocal
from app.models.price_list import PriceItem, Formula, CoefficientTable

def seed_price_items():
    db = SessionLocal()
    
    # آیتم‌های نمونه
    sample_items = [
        PriceItem(
            code="001.001",
            name="حفاری با بیل مکانیکی",
            unit="متر مکعب",
            unit_price=150000,
            category="حفاری",
            formula="{volume} * {unit_price} * {coefficient}",
            parameters={"coefficient": 1.2}
        ),
        PriceItem(
            code="002.001", 
            name="بتن ریزی فونداسیون",
            unit="متر مکعب",
            unit_price=850000,
            category="بتن ریزی",
            formula="{volume} * {unit_price} * {cement_ratio} * {labor_factor}",
            parameters={"cement_ratio": 1.1, "labor_factor": 1.3}
        )
    ]
    
    # جداول ضرایب
    coefficient_tables = [
        CoefficientTable(
            name="ضریب سختی خاک",
            table_data={
                "نرم": 1.0,
                "متوسط": 1.2,
                "سخت": 1.5,
                "بسیار سخت": 2.0
            }
        )
    ]
    
    db.add_all(sample_items)
    db.add_all(coefficient_tables)
    db.commit()
    db.close()
