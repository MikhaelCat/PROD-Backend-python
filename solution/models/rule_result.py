from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from database.connection import Base
from datetime import datetime
import uuid

class RuleResult(Base):
    __tablename__ = "rule_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), nullable=False)  # внешний ключ к транзакциям
    rule_id = Column(String(36), nullable=False)  # внешний ключ к fraud_rules
    rule_name = Column(String(120), nullable=False)
    priority = Column(Integer, nullable=False)
    enabled = Column(Boolean, nullable=False)
    matched = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=False)  # объяснение того, почему правило соответствует или нет
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)