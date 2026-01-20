from fastapi import FastAPI
from api import auth_router, users_router, transactions_router, fraud_rules_router
from database.connection import engine, Base
from models.user import User
from auth.utils import get_password_hash
from database.settings import settings
import uvicorn

app = FastAPI(title="Anti-fraud Service API", version="1.3.0")

# Создание таблиц при запуске
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    
    # Проверить, существует ли администратор, и создать его если нет
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from solution.database.connection import sessionlocal
    
    db = sessionlocal()
    try:
        admin_user = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin_user:
            admin_user = User(
                email=settings.admin_email,
                password_hash=get_password_hash(settings.admin_password),
                full_name=settings.admin_fullname,
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()

# подключение маршрутов
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(fraud_rules_router, prefix="/api/v1")

@app.get("/api/v1/ping")
def ping():
    """эндпоинт проверки работоспособности"""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)