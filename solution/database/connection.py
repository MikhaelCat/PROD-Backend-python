from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database.settings import settings

# cоздание базового класса для моделей
Base = declarative_base()

# создать движок
engine = create_engine(
    f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

# создать сессию
sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """получение сеанса базы данных"""
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()