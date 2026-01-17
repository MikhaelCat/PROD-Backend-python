from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from solution.database.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """проверка соответствия открытого пароля хэшированному паролю"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """хэширование пароля"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """создание токена доступа jwt"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.random_secret, algorithm="hs256")
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """декодирование токена доступа jwt"""
    try:
        payload = jwt.decode(token, settings.random_secret, algorithms=["HS256"])
        return payload
    except JWTError:
        return None