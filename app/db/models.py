from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class PriceItem(Base):
    __tablename__ = "price_items"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)

class BOQItem(Base):
    __tablename__ = "boq_items"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    price_item_id = Column(Integer, ForeignKey("price_items.id"))
    quantity = Column(Float, default=0)
    total_price = Column(Float, default=0)
    price_item = relationship("PriceItem")
