from fastapi import APIRouter, HTTPException, status, Body, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import Field, BaseModel

from database.connection import get_db
from auth.dependencies import get_current_admin_user
from models.fraud_rule import FraudRule
from dsl.validator import validate_dsl_expression, DslValidateResponse

router = APIRouter(prefix="/fraud-rules", tags=["fraud_rules"])

# схемы
class FraudRuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    dsl_expression: str = Field(..., min_length=3, max_length=2000)
    enabled: bool = True
    priority: int = Field(default=100, ge=1)

class FraudRuleUpdateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    dsl_expression: str = Field(..., min_length=3, max_length=2000)
    enabled: bool
    priority: int = Field(ge=1)

class FraudRuleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    dsl_expression: str
    enabled: bool
    priority: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class DslValidateRequest(BaseModel):
    dsl_expression: str = Field(..., min_length=3, max_length=2000)

class DslValidationError(BaseModel):
    code: str
    message: str
    position: Optional[int] = None
    near: Optional[str] = None

class DslValidateResponse(BaseModel):
    is_valid: bool
    normalized_expression: Optional[str] = None
    errors: List[DslValidationError]

@router.get("/", response_model=List[FraudRuleResponse])
def get_fraud_rules(
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """получение списка всех правил обнаружения мошенничества"""
    rules = db.query(FraudRule).all()
    return rules

@router.post("/", response_model=FraudRuleResponse, status_code=status.HTTP_201_CREATED)
def create_fraud_rule(
    request: FraudRuleCreateRequest = Body(...),
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """создание нового правила обнаружения мошенничества"""
    # проверить, существует ли уже такое имя правила
    existing_rule = db.query(FraudRule).filter(FraudRule.name == request.name).first()
    if existing_rule:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rule name already exists"
        )
    
    # проверка выражения dsl
    validation_result = validate_dsl_expression(request.dsl_expression)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"DSL validation failed: {validation_result.errors[0].message if validation_result.errors else 'invalid expression'}"
        )
    
    # сщздание правила
    rule = FraudRule(
        name=request.name,
        description=request.description,
        dsl_expression=request.dsl_expression,
        enabled=request.enabled,
        priority=request.priority
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule

@router.get("/{id}", response_model=FraudRuleResponse)
def get_fraud_rule(
    id: str,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """получение правила обнаружения мошенничества по id"""
    rule = db.query(FraudRule).filter(FraudRule.id == id).first()
    
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    
    return rule

@router.put("/{id}", response_model=FraudRuleResponse)
def update_fraud_rule(
    id: str,
    request: FraudRuleUpdateRequest = Body(...),
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """обновление правила обнаружения мошенничества"""
    rule = db.query(FraudRule).filter(FraudRule.id == id).first()
    
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    
    # проверить, существует ли другое правило с тем же именем (кроме этого правила)
    existing_rule = db.query(FraudRule).filter(
        FraudRule.name == request.name,
        FraudRule.id != id
    ).first()
    if existing_rule:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rule name already exists"
        )
    
    # проверка dsl 
    validation_result = validate_dsl_expression(request.dsl_expression)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"DSL validation failed: {validation_result.errors[0].message if validation_result.errors else 'invalid expression'}"
        )
    
    # обновление правил
    rule.name = request.name
    rule.description = request.description
    rule.dsl_expression = request.dsl_expression
    rule.enabled = request.enabled
    rule.priority = request.priority
    
    db.commit()
    db.refresh(rule)
    
    return rule

@router.delete("/{id}")
def deactivate_fraud_rule(
    id: str,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """деактивация правила обнаружения мошенничества"""
    rule = db.query(FraudRule).filter(FraudRule.id == id).first()
    
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    
    rule.enabled = False
    db.commit()
    
    return {"detail": "Rule deactivated"}

@router.post("/validate", response_model=DslValidateResponse)
def validate_dsl(
    request: DslValidateRequest = Body(...),
    current_user = Depends(get_current_admin_user)
):
    """валидация выражения dsl для правила"""
    return validate_dsl_expression(request.dsl_expression)