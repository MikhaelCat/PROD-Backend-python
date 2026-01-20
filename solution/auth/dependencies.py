from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional
from sqlalchemy.orm import Session
from auth.utils import decode_access_token
from database.connection import get_db
from models.user import User

http_bearer = HTTPBearer()

def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """получение текущего аутентифицированного пользователя"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token.credentials)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user_obj = db.query(User).filter(User.id == user_id).first()
    if user_obj is None:
        raise credentials_exception
    
    if not user_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="User is deactivated"
        )
    
    return user_obj

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """проверка прав администратора для текущего пользователя"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user