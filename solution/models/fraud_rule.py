from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from database.connection import Base
from datetime import datetime
import uuid

class FraudRule(Base):
    __tablename__ = "fraud_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    dsl_expression = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)  # меньше - выше приоритет
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)