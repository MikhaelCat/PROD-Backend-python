from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)
    currency = Column(String(3), nullable=False)  
    status = Column(String(10), nullable=False)  # одобрено или отклонено
    merchant_id = Column(String(64), nullable=True)
    merchant_category_code = Column(String(4), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    ip_address = Column(String(64), nullable=True)
    device_id = Column(String(128), nullable=True)
    channel = Column(String(10), nullable=True)  # web, mobile, pos, other
    location = Column(Text, nullable=True)  # json string
    is_fraud = Column(Boolean, nullable=False, default=False)
    transaction_metadata = Column(Text, nullable=True)  # json string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)