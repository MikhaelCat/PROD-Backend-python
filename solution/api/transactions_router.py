from fastapi import APIRouter, HTTPException, status, Body, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import Field, BaseModel
from datetime import datetime
import json

from database.connection import get_db
from auth.dependencies import get_current_user, get_current_admin_user
from models.transaction import Transaction
from models.rule_result import RuleResult
from models.fraud_rule import FraudRule
from models.user import User
from dsl.evaluator import evaluate_dsl_expression

router = APIRouter(prefix="/transactions", tags=["transactions"])

# схемы
class Location(BaseModel):
    country: str
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TransactionCreateRequest(BaseModel):
    user_id: Optional[str] = None
    amount: float = Field(..., gt=0, le=999999999.99)
    currency: str = Field(..., pattern=r'^[A-Z]{3}$')  # ISO 4217
    merchant_id: Optional[str] = Field(default=None, max_length=64)
    merchant_category_code: Optional[str] = Field(default=None, pattern=r'^\d{4}$')
    timestamp: str  # ISO 8601
    ip_address: Optional[str] = Field(default=None, max_length=64)
    device_id: Optional[str] = Field(default=None, max_length=128)
    channel: Optional[str] = Field(default=None)  # web, mobile, pos, other
    location: Optional[Location] = None
    metadata: Optional[Dict[str, Any]] = None

class RuleResultResponse(BaseModel):
    rule_id: str
    rule_name: str
    priority: int
    enabled: bool
    matched: bool
    description: str

class TransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    currency: str
    status: str
    merchant_id: Optional[str] = None
    merchant_category_code: Optional[str] = None
    timestamp: str
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    channel: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    is_fraud: bool
    metadata: Optional[Dict[str, Any]] = None
    created_at: str

class TransactionDecision(BaseModel):
    transaction: TransactionResponse
    rule_results: List[RuleResultResponse]

class PagedTransactionsResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    size: int

class TransactionBatchCreateRequest(BaseModel):
    items: List[TransactionCreateRequest]

class BatchItemDecision(BaseModel):
    index: int
    decision: Optional[TransactionDecision] = None
    error: Optional[Dict[str, Any]] = None

class TransactionBatchResult(BaseModel):
    items: List[BatchItemDecision]

@router.post("/", response_model=TransactionDecision, status_code=status.HTTP_201_CREATED)
def create_transaction(
    request: TransactionCreateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """создание новой транзакции с проверкой на мошенничество"""
    # если пользователь администратор и указан user_id, проверить, что можно создать транзакцию от имени другого пользователя
    if current_user.role == "admin" and request.user_id is not None:
        actual_user_id = request.user_id
        # проверить, что пользователь существует
        target_user = db.query(User).filter(User.id == actual_user_id).first()
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not target_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is deactivated")
    else:
        # если пользователь не администратор или не указан user_id, использовать текущий идентификатор пользователя
        actual_user_id = current_user.id
    
    # разобрать метку времени
    try:
        # заменить z на +00:00 для корректной обработки ISO формата
        timestamp_str = request.timestamp.replace('z', '+00:00').replace('Z', '+00:00')
        # обработать различные форматы временных меток
        if '.' in timestamp_str:
            # если есть миллисекунды
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            # если нет миллисекунд, добавить их для согласованности
            timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid timestamp format")
    
    # создать транзакцию
    transaction = Transaction(
        user_id=actual_user_id,
        amount=request.amount,
        currency=request.currency.upper(),
        merchant_id=request.merchant_id,
        merchant_category_code=request.merchant_category_code,
        timestamp=timestamp,
        ip_address=request.ip_address,
        device_id=request.device_id,
        channel=request.channel,
        location=json.dumps(request.location.dict()) if request.location else None,
        transaction_metadata=json.dumps(request.metadata) if request.metadata else None,
        status="pending",  # информация будет обновлена после проверки на мошенничество
        is_fraud=False
    )
    
    db.add(transaction)
    db.flush()  # идентификатор без фиксации
    
    # получить пользователя для контекста проверки правил
    user = db.query(User).filter(User.id == transaction.user_id).first()
    
    # применить правила мошенничества
    active_rules = db.query(FraudRule).filter(FraudRule.enabled == True).order_by(FraudRule.priority, FraudRule.id).all()
    
    rule_results = []
    is_any_rule_matched = False
    
    for rule in active_rules:
        # подготовить контекст для вычисления правила
        context = {
            'transaction': {
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'merchant_id': transaction.merchant_id,
                'merchant_category_code': transaction.merchant_category_code,
                'channel': transaction.channel
            },
            'user': {
                'age': user.age if user.age is not None else 0,
                'region': user.region if user.region is not None else '',
                'gender': user.gender if user.gender is not None else '',
                'marital_status': user.marital_status if user.marital_status is not None else ''
            }
        }
        
        # вычислить выражение правила
        matched, description = evaluate_dsl_expression(rule.dsl_expression, context)
        
        rule_result = RuleResult(
            transaction_id=transaction.id,
            rule_id=rule.id,
            rule_name=rule.name,
            priority=rule.priority,
            enabled=rule.enabled,
            matched=matched,
            description=description
        )
        
        db.add(rule_result)
        rule_results.append(rule_result)
        
        if matched:
            is_any_rule_matched = True
    
    # определить статус на основе правил
    transaction.status = "declined" if is_any_rule_matched else "approved"
    transaction.is_fraud = is_any_rule_matched
    
    db.commit()
    db.refresh(transaction)
    
    # перезагрузить результаты правила
    rule_results_db = db.query(RuleResult).filter(RuleResult.transaction_id == transaction.id).all()
    
    return TransactionDecision(
        transaction=TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            amount=float(transaction.amount),
            currency=transaction.currency,
            status=transaction.status,
            merchant_id=transaction.merchant_id,
            merchant_category_code=transaction.merchant_category_code,
            timestamp=transaction.timestamp.isoformat(),
            ip_address=transaction.ip_address,
            device_id=transaction.device_id,
            channel=transaction.channel,
            location=json.loads(transaction.location) if transaction.location else None,
            is_fraud=transaction.is_fraud,
            metadata=json.loads(transaction.metadata) if transaction.metadata else None,
            created_at=transaction.created_at.isoformat()
        ),
        rule_results=[
            RuleResultResponse(
                rule_id=rr.rule_id,
                rule_name=rr.rule_name,
                priority=rr.priority,
                enabled=rr.enabled,
                matched=rr.matched,
                description=rr.description
            ) for rr in rule_results_db
        ]
    )

@router.get("/{id}", response_model=TransactionDecision)
def get_transaction(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """получение транзакции по id"""
    transaction = db.query(Transaction).filter(Transaction.id == id).first()
    
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    # проверить разрешения
    if current_user.role != "admin" and current_user.id != transaction.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # получить результаты правила
    rule_results_db = db.query(RuleResult).filter(RuleResult.transaction_id == transaction.id).all()
    
    return TransactionDecision(
        transaction=TransactionResponse(
            id=transaction.id,
            user_id=transaction.user_id,
            amount=float(transaction.amount),
            currency=transaction.currency,
            status=transaction.status,
            merchant_id=transaction.merchant_id,
            merchant_category_code=transaction.merchant_category_code,
            timestamp=transaction.timestamp.isoformat(),
            ip_address=transaction.ip_address,
            device_id=transaction.device_id,
            channel=transaction.channel,
            location=json.loads(transaction.location) if transaction.location else None,
            is_fraud=transaction.is_fraud,
            metadata=json.loads(transaction.metadata) if transaction.metadata else None,
            created_at=transaction.created_at.isoformat()
        ),
        rule_results=[
            RuleResultResponse(
                rule_id=rr.rule_id,
                rule_name=rr.rule_name,
                priority=rr.priority,
                enabled=rr.enabled,
                matched=rr.matched,
                description=rr.description
            ) for rr in rule_results_db
        ]
    )

@router.get("/", response_model=PagedTransactionsResponse)
def get_transactions(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    is_fraud: Optional[bool] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 0,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """получение списка транзакций с фильтрацией и пагинацией"""
    # проверить разрешения для фильтра пользователя
    if user_id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # построить запрос
    query = db.query(Transaction)
    
    # применить фильтры
    if current_user.role != "admin":
        query = query.filter(Transaction.user_id == current_user.id)
    elif user_id:
        query = query.filter(Transaction.user_id == user_id)
    
    if status:
        query = query.filter(Transaction.status == status.lower())
    
    if is_fraud is not None:
        query = query.filter(Transaction.is_fraud == is_fraud)
    
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date.replace('z', '+00:00'))
            query = query.filter(Transaction.timestamp >= from_dt)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid from date format")
    
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date.replace('z', '+00:00'))
            query = query.filter(Transaction.timestamp < to_dt)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid to date format")
    
    offset = page * size
    transactions = query.offset(offset).limit(size).all()
    total = query.count()
    
    return PagedTransactionsResponse(
        items=[
            TransactionResponse(
                id=t.id,
                user_id=t.user_id,
                amount=float(t.amount),
                currency=t.currency,
                status=t.status,
                merchant_id=t.merchant_id,
                merchant_category_code=t.merchant_category_code,
                timestamp=t.timestamp.isoformat(),
                ip_address=t.ip_address,
                device_id=t.device_id,
                channel=t.channel,
                location=json.loads(t.location) if t.location else None,
                is_fraud=t.is_fraud,
                metadata=json.loads(t.metadata) if t.metadata else None,
                created_at=t.created_at.isoformat()
            ) for t in transactions
        ],
        total=total,
        page=page,
        size=size
    )


@router.post("/batch", response_model=TransactionBatchResult)
def create_transaction_batch(
    request: TransactionBatchCreateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """создание батча транзакций"""
    if len(request.items) < 1 or len(request.items) > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Batch must contain 1 to 500 items"
        )
    
    results = []
    has_errors = False
    
    for idx, item in enumerate(request.items):
        try:
            # экземпляр запроса для каждой транзакции
            item_request = TransactionCreateRequest(
                user_id=item.user_id,
                amount=item.amount,
                currency=item.currency,
                merchant_id=item.merchant_id,
                merchant_category_code=item.merchant_category_code,
                timestamp=item.timestamp,
                ip_address=item.ip_address,
                device_id=item.device_id,
                channel=item.channel,
                location=item.location,
                metadata=item.metadata
            )
            
            # проверить права доступа для текущего пользователя
            # если пользователь администратор и указан user_id, проверить, что можно создать транзакцию от имени другого пользователя
            if current_user.role == "admin" and item_request.user_id is not None:
                actual_user_id = item_request.user_id
                # проверить, что пользователь существует
                target_user = db.query(User).filter(User.id == actual_user_id).first()
                if not target_user:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
                if not target_user.is_active:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is deactivated")
            else:
                # если пользователь не администратор или не указан user_id, использовать текущий идентификатор пользователя
                actual_user_id = current_user.id
            
            # разобрать метку времени
            try:
                timestamp = datetime.fromisoformat(item_request.timestamp.replace('z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid timestamp format")
            
            # создать транзакцию
            transaction = Transaction(
                user_id=actual_user_id,
                amount=item_request.amount,
                currency=item_request.currency.upper(),
                merchant_id=item_request.merchant_id,
                merchant_category_code=item_request.merchant_category_code,
                timestamp=timestamp,
                ip_address=item_request.ip_address,
                device_id=item_request.device_id,
                channel=item_request.channel,
                location=json.dumps(item_request.location.dict()) if item_request.location else None,
                transaction_metadata=json.dumps(item_request.metadata) if item_request.metadata else None,
                status="pending",  
                is_fraud=False
            )
            
            db.add(transaction)
            db.flush()  # get id without committing
            
            # получить пользователя для контекста проверки правил
            user = db.query(User).filter(User.id == transaction.user_id).first()
            
            # применить правила мошенничества
            active_rules = db.query(FraudRule).filter(FraudRule.enabled == True).order_by(FraudRule.priority, FraudRule.id).all()
            
            rule_results = []
            is_any_rule_matched = False
            
            for rule in active_rules:
                # подготовить контекст для вычисления правила
                context = {
                    'transaction': {
                        'amount': float(transaction.amount),
                        'currency': transaction.currency,
                        'merchant_id': transaction.merchant_id,
                        'merchant_category_code': transaction.merchant_category_code,
                        'channel': transaction.channel
                    },
                    'user': {
                        'age': user.age if user.age is not None else 0,
                        'region': user.region if user.region is not None else '',
                        'gender': user.gender if user.gender is not None else '',
                        'marital_status': user.marital_status if user.marital_status is not None else ''
                    }
                }
                
                # вычислить выражение правила
                matched, description = evaluate_dsl_expression(rule.dsl_expression, context)
                
                rule_result = RuleResult(
                    transaction_id=transaction.id,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    priority=rule.priority,
                    enabled=rule.enabled,
                    matched=matched,
                    description=description
                )
                
                db.add(rule_result)
                rule_results.append(rule_result)
                
                if matched:
                    is_any_rule_matched = True
            
            # определить статус на основе правил
            transaction.status = "declined" if is_any_rule_matched else "approved"
            transaction.is_fraud = is_any_rule_matched
            
            # обновить транзакцию в базе
            db.refresh(transaction)
            
            # перезагрузить результаты правила
            rule_results_db = db.query(RuleResult).filter(RuleResult.transaction_id == transaction.id).all()
            
            decision = TransactionDecision(
                transaction=TransactionResponse(
                    id=transaction.id,
                    user_id=transaction.user_id,
                    amount=float(transaction.amount),
                    currency=transaction.currency,
                    status=transaction.status,
                    merchant_id=transaction.merchant_id,
                    merchant_category_code=transaction.merchant_category_code,
                    timestamp=transaction.timestamp.isoformat(),
                    ip_address=transaction.ip_address,
                    device_id=transaction.device_id,
                    channel=transaction.channel,
                    location=json.loads(transaction.location) if transaction.location else None,
                    is_fraud=transaction.is_fraud,
                    metadata=json.loads(transaction.metadata) if transaction.metadata else None,
                    created_at=transaction.created_at.isoformat()
                ),
                rule_results=[
                    RuleResultResponse(
                        rule_id=rr.rule_id,
                        rule_name=rr.rule_name,
                        priority=rr.priority,
                        enabled=rr.enabled,
                        matched=rr.matched,
                        description=rr.description
                    ) for rr in rule_results_db
                ]
            )
            
            results.append(BatchItemDecision(index=idx, decision=decision))
            
        except HTTPException as e:
            has_errors = True
            results.append(BatchItemDecision(
                index=idx,
                error={
                    "code": "VALIDATION_FAILED" if e.status_code == 422 else "ACCESS_DENIED" if e.status_code == 403 else "NOT_FOUND",
                    "message": e.detail
                }
            ))
        except Exception as e:
            has_errors = True
            results.append(BatchItemDecision(
                index=idx,
                error={
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            ))
    
    db.commit()
    
    status_code = status.HTTP_207_MULTI_STATUS if has_errors else status.HTTP_201_CREATED
    
    return TransactionBatchResult(items=results)   
