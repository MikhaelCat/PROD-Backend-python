from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from database.connection import Base
from datetime import datetime
from typing import Optional
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(254), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=True)
    region = Column(String(32), nullable=True)
    gender = Column(Enum("male", "female", name="gender_enum"), nullable=True)
    marital_status = Column(Enum("single", "married", "divorced", "widowed", name="marital_status_enum"), nullable=True)
    role = Column(Enum("user", "admin", name="role_enum"), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)