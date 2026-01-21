from fastapi import APIRouter, HTTPException, status, Body, Depends
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from pydantic import Field, validator
from pydantic.main import BaseModel

from database.connection import get_db
from auth.utils import verify_password, get_password_hash, create_access_token
from models.user import User
from database.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# схемы
class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str = Field(..., min_length=2, max_length=200)
    age: Optional[int] = Field(default=None, ge=18, le=120)
    region: Optional[str] = Field(default=None, max_length=32)
    gender: Optional[str] = Field(default=None)
    marital_status: Optional[str] = Field(default=None)

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    age: Optional[int] = None
    region: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    expires_in: int = 3600
    user: UserResponse

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest = Body(...), db: Session = Depends(get_db)):
    """регистрация нового пользователя"""
    try:
        # проверить, существует ли уже такой email
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
        
        # хешировать пароль
        password_hash = get_password_hash(request.password)
        
        # создать пользователя
        new_user = User(
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            age=request.age,
            region=request.region,
            gender=request.gender.lower() if request.gender else None,
            marital_status=request.marital_status.lower() if request.marital_status else None,
            role="user"  # default role
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # создать токен доступа
        access_token_data = {
            "sub": new_user.id,
            "role": new_user.role
        }
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(hours=1)
        )
        
        return AuthResponse(
            access_token=access_token,
            expires_in=3600,
            user=UserResponse(
                id=new_user.id,
                email=new_user.email,
                full_name=new_user.full_name,
                age=new_user.age,
                region=new_user.region,
                gender=new_user.gender,
                marital_status=new_user.marital_status,
                role=new_user.role,
                is_active=new_user.is_active
            )
        )
    except Exception as e:
        # Re-raise the exception so the proper error response is returned
        raise e

@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest = Body(...), db: Session = Depends(get_db)):
    """аутентификация пользователя и получение токена доступа"""
    try:
        # найти пользователя по email
        user_obj = db.query(User).filter(User.email == request.email).first()
        
        if not user_obj or not verify_password(request.password, user_obj.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="User is deactivated"
            )
        
        # создать токен доступа
        access_token_data = {
            "sub": user_obj.id,
            "role": user_obj.role
        }
        access_token = create_access_token(
            data=access_token_data,
            expires_delta=timedelta(hours=1)
        )
        
        return AuthResponse(
            access_token=access_token,
            expires_in=3600,
            user=UserResponse(
                id=user_obj.id,
                email=user_obj.email,
                full_name=user_obj.full_name,
                age=user_obj.age,
                region=user_obj.region,
                gender=user_obj.gender,
                marital_status=user_obj.marital_status,
                role=user_obj.role,
                is_active=user_obj.is_active
            )
        )
    except Exception:
        # Re-raise the exception so the proper error response is returned
        raise