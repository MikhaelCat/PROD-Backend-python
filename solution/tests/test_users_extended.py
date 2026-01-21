"""Extended tests for user endpoints with specific test names from the test suite"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the API"""
    with TestClient(app) as c:
        yield c


def test_LoginAdmin(client):
    """Test admin login functionality"""
    with patch('auth.utils.verify_password') as mock_verify, \
         patch('auth.utils.create_access_token') as mock_token:
        
        mock_verify.return_value = True
        mock_token.return_value = "mocked_token"
        
        from unittest.mock import MagicMock
        mock_user = MagicMock()
        mock_user.id = "admin123"
        mock_user.email = "admin@admin.com"
        mock_user.full_name = "Admin User"
        mock_user.is_active = True
        mock_user.role = "admin"
        mock_user.password_hash = "hashed_admin_password"
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query_instance = mock_query.return_value
            mock_query_instance.filter.return_value.first.return_value = mock_user
            
            login_data = {
                "email": "admin@admin.com",
                "password": "admin123"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["user"]["role"] == "admin"


def test_RegisterUser(client):
    """Test user registration"""
    with patch('auth.utils.get_password_hash') as mock_hash, \
         patch('auth.utils.create_access_token') as mock_token:
        
        mock_hash.return_value = "hashed_password"
        mock_token.return_value = "mocked_token"
        
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == user_data["email"]


def test_AuthUser(client):
    """Test user authentication"""
    with patch('auth.utils.verify_password') as mock_verify, \
         patch('auth.utils.create_access_token') as mock_token:
        
        mock_verify.return_value = True
        mock_token.return_value = "mocked_token"
        
        from unittest.mock import MagicMock
        mock_user = MagicMock()
        mock_user.id = "user123"
        mock_user.email = "user@example.com"
        mock_user.full_name = "Regular User"
        mock_user.is_active = True
        mock_user.role = "user"
        mock_user.password_hash = "hashed_regular_password"
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query_instance = mock_query.return_value
            mock_query_instance.filter.return_value.first.return_value = mock_user
            
            login_data = {
                "email": "user@example.com",
                "password": "userpassword123"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["role"] == "user"


def test_AuthInvalidCreds(client):
    """Test authentication with invalid credentials"""
    with patch('auth.utils.verify_password') as mock_verify:
        mock_verify.return_value = False  # Invalid credentials
        
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401  # Unauthorized


def test_GetMe(client):
    """Test getting current user profile"""
    with patch('auth.dependencies.get_current_user') as mock_get_current_user:
        mock_user_data = {
            "id": "user123",
            "email": "user@example.com",
            "full_name": "Test User",
            "role": "user",
            "is_active": True
        }
        mock_get_current_user.return_value = type('MockUser', (), mock_user_data)()
        
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "user123"
        assert data["email"] == "user@example.com"


def test_UpdateMe(client):
    """Test updating current user profile"""
    with patch('auth.dependencies.get_current_user') as mock_get_current_user:
        from unittest.mock import MagicMock
        mock_user = MagicMock()
        mock_user.id = "user123"
        mock_user.email = "user@example.com"
        mock_user.full_name = "Old Name"
        mock_user.is_active = True
        mock_user.role = "user"
        mock_user.password_hash = "hashed_user_password"
        
        mock_get_current_user.return_value = mock_user
        
        update_data = {
            "full_name": "Updated Name",
            "age": 30,
            "region": "New Region"
        }
        
        response = client.patch("/api/v1/users/me", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"


def test_ListUsersAsAdmin(client):
    """Test listing users as admin"""
    with patch('auth.dependencies.get_current_admin_user') as mock_get_current_admin:
        from unittest.mock import MagicMock
        mock_admin = MagicMock()
        mock_admin.id = "admin123"
        mock_admin.email = "admin@example.com"
        mock_admin.full_name = "Admin User"
        mock_admin.is_active = True
        mock_admin.role = "admin"
        
        mock_get_current_admin.return_value = mock_admin
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query_instance = mock_query.return_value
            mock_query_instance.offset.return_value.limit.return_value.all.return_value = []
            mock_query_instance.count.return_value = 0
            
            response = client.get("/api/v1/users/")
            
            assert response.status_code == 200
            data = response.json()
            assert "items" in data


def test_CreateUserByAdmin(client):
    """Test creating user by admin"""
    with patch('auth.dependencies.get_current_admin_user') as mock_get_current_admin:
        from unittest.mock import MagicMock
        mock_admin = MagicMock()
        mock_admin.id = "admin123"
        mock_admin.email = "admin@example.com"
        mock_admin.full_name = "Admin User"
        mock_admin.is_active = True
        mock_admin.role = "admin"
        
        mock_get_current_admin.return_value = mock_admin
        
        with patch('auth.utils.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            user_data = {
                "email": "newbyadmin@example.com",
                "password": "password123",
                "full_name": "Created by Admin",
                "role": "user"
            }
            
            response = client.post("/api/v1/users/", json=user_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == user_data["email"]