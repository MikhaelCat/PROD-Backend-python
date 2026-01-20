import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app
from database.connection import Base


@pytest.fixture(scope="module")
def client():
    """Create a test client for the API"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def mock_db_session():
    """Mock database session for testing"""
    # Create an in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    from database import connection
    connection.get_db = override_get_db
    
    yield TestingSessionLocal()
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_auth_dependencies():
    """Mock authentication dependencies for testing"""
    with patch("auth.dependencies.get_current_user") as mock_get_current_user:
        yield mock_get_current_user