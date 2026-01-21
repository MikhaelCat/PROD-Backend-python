from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database.settings import settings
import os

# cоздание базового класса для моделей
Base = declarative_base()

# Check if we're in test mode
TESTING = os.getenv("TESTING", "False").lower() == "true"

if TESTING:
    # Use SQLite in-memory database for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Use PostgreSQL for production
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# создать сессию
sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """получение сеанса базы данных"""
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()