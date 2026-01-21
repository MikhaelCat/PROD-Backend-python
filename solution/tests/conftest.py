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
    # Set testing environment variable
    import os
    os.environ["TESTING"] = "True"
    
    # Import after setting the environment variable to ensure proper configuration
    from database.connection import Base, engine, sessionlocal
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create an in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    
    test_engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    Base.metadata.create_all(bind=test_engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Override the get_db function in the connection module
    from database import connection
    original_get_db = connection.get_db
    connection.get_db = override_get_db
    
    yield TestingSessionLocal()
    
    Base.metadata.drop_all(bind=test_engine)
    
    # Restore original function
    connection.get_db = original_get_db


@pytest.fixture
def mock_auth_dependencies():
    """Mock authentication dependencies for testing"""
    with patch("auth.dependencies.get_current_user") as mock_get_current_user:
        yield mock_get_current_user