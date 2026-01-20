from fastapi import APIRouter, HTTPException, status, Body, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import Field, BaseModel

from database.connection import get_db
from auth.dependencies import get_current_user, get_current_admin_user
from models.user import User
from auth.utils import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

# схемы
class UserUpdateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    age: Optional[int] = Field(default=None, ge=18, le=120)
    region: Optional[str] = Field(default=None, max_length=32)
    gender: Optional[str] = Field(default=None)
    marital_status: Optional[str] = Field(default=None)

class UserCreateRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str = Field(..., min_length=2, max_length=200)
    age: Optional[int] = Field(default=None, ge=18, le=120)
    region: Optional[str] = Field(default=None, max_length=32)
    gender: Optional[str] = Field(default=None)
    marital_status: Optional[str] = Field(default=None)
    role: str  #  требуется для создания администратора

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

class PagedUsersResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """получение профиля текущего пользователя"""
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    request: UserUpdateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """обновление профиля текущего пользователя"""
    # обновить поля
    current_user.full_name = request.full_name
    current_user.age = request.age
    current_user.region = request.region
    current_user.gender = request.gender.lower() if request.gender else None
    current_user.marital_status = request.marital_status.lower() if request.marital_status else None
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/{id}", response_model=UserResponse)
def get_user_by_id(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """получение пользователя по id"""
    user = db.query(User).filter(User.id == id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # проверить разрешения
    if current_user.role != "admin" and current_user.id != id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return user

@router.put("/{id}", response_model=UserResponse)
def update_user_by_id(
    id: str,
    request: UserUpdateRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """обновление пользователя по id"""
    user = db.query(User).filter(User.id == id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # проверить разрешения
    if current_user.role != "admin" and current_user.id != id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    #проверить, не пытается ли пользователь изменить роль или is_active (не разрешено для обычных пользователей)
    if hasattr(request, 'role') or hasattr(request, 'is_active'):
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    # обновление полей
    user.full_name = request.full_name
    user.age = request.age
    user.region = request.region
    user.gender = request.gender.lower() if request.gender else None
    user.marital_status = request.marital_status.lower() if request.marital_status else None
    
    # только администратор может обновлять роль и is_active
    if current_user.role == "admin":
        if hasattr(request, 'role'):
            user.role = request.role.lower()
        if hasattr(request, 'is_active'):
            user.is_active = request.is_active
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{id}")
def deactivate_user(
    id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """деактивация пользователя администратором"""
    user = db.query(User).filter(User.id == id).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_active = False
    db.commit()
    
    return {"detail": "User deactivated"}

@router.get("/", response_model=PagedUsersResponse)
def get_all_users(
    page: int = 0,
    size: int = 20,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """получение списка всех пользователей с пагинацией"""
    offset = page * size
    users_query = db.query(User)
    users = users_query.offset(offset).limit(size).all()
    total = users_query.count()
    
    return PagedUsersResponse(
        items=users,
        total=total,
        page=page,
        size=size
    )

@router.post("/", response_model=UserResponse)
def create_user_by_admin(
    request: UserCreateRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """создание пользователя администратором"""
    # проверить, существует ли уже такой email
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    
    # хэширование пароля
    password_hash = get_password_hash(request.password)
    
    # создание юзера
    new_user = User(
        email=request.email,
        password_hash=password_hash,
        full_name=request.full_name,
        age=request.age,
        region=request.region,
        gender=request.gender.lower() if request.gender else None,
        marital_status=request.marital_status.lower() if request.marital_status else None,
        role=request.role.lower()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user