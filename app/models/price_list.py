from sqlalchemy import Column, Integer, String, Float, Text, JSON
from app.core.database import Base

class PriceItem(Base):
    __tablename__ = "price_items"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, default=0.0)
    category = Column(String)
    sub_category = Column(String)
    description = Column(Text)
    formula = Column(Text)  # فرمول محاسبه
    parameters = Column(JSON)  # پارامترهای فرمول
    coefficients = Column(JSON)  # ضرایب مختلف

class Formula(Base):
    __tablename__ = "formulas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    expression = Column(Text, nullable=False)
    variables = Column(JSON)  # متغیرهای فرمول
    description = Column(Text)

class CoefficientTable(Base):
    __tablename__ = "coefficient_tables"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    table_data = Column(JSON)  # داده‌های جدول
    applicable_to = Column(String)  # موارد کاربرد
