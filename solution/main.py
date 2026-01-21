
import os
# Check if we're in test mode early, before importing database modules
TESTING = os.getenv("TESTING", "False").lower() == "true"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from api import auth_router, users_router, transactions_router, fraud_rules_router
from database.connection import engine, Base
from models.user import User
from models.transaction import Transaction
from models.fraud_rule import FraudRule
from models.rule_result import RuleResult
from auth.utils import get_password_hash
from database.settings import settings
import uvicorn
import logging

app = FastAPI(
    title="Anti-fraud Service API", 
    version="1.3.0",
    redoc_url="/api/v1/redoc",
    docs_url="/api/v1/docs"
)



# Создание таблиц при запуске
@app.on_event("startup")
def startup_event():
    # Create all tables first
    Base.metadata.create_all(bind=engine)
    
    # Always check if we need to create the admin user (including during testing)
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    from database.connection import sessionlocal
    
    db = sessionlocal()
    try:
        # Ensure tables exist before querying
        admin_user = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin_user:
            print(f"Creating admin user with email: {settings.admin_email}")
            # Truncate password to 72 characters to comply with bcrypt limitations
            admin_password = settings.admin_password[:72] if len(settings.admin_password) > 72 else settings.admin_password
            admin_user = User(
                email=settings.admin_email,
                password_hash=get_password_hash(admin_password),
                full_name=settings.admin_fullname,
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)  # Refresh to get the ID
            print(f"Admin user created successfully with ID: {admin_user.id}")
        else:
            print(f"Admin user already exists with ID: {admin_user.id}")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        # Log more specific information about the error
        import traceback
        traceback.print_exc()
        db.rollback()
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
