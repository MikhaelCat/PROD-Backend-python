"""Tests for authentication endpoints"""

import pytest
from unittest.mock import patch


def test_register_endpoint(client, mock_db_session):
    """Test the user registration endpoint"""
    # Mock the password hashing and token creation
    with patch('auth.utils.get_password_hash') as mock_hash, \
         patch('auth.utils.create_access_token') as mock_token:
        
        mock_hash.return_value = "hashed_password"
        mock_token.return_value = "mocked_token"
        
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "age": 25,
            "region": "Test Region",
            "gender": "male",
            "marital_status": "single"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Should succeed with 201 Created
        assert response.status_code == 201
        
        # Check response structure
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["full_name"] == user_data["full_name"]


def test_register_duplicate_email(client, mock_db_session):
    """Test registration with duplicate email"""
    with patch('auth.utils.get_password_hash') as mock_hash, \
         patch('auth.utils.create_access_token') as mock_token:
        
        mock_hash.return_value = "hashed_password"
        mock_token.return_value = "mocked_token"
        
        # First registration should succeed
        user_data = {
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Second registration with same email should fail
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 409  # Conflict


def test_login_success(client, mock_db_session):
    """Test successful login"""
    # Mock user lookup and authentication
    with patch('auth.utils.verify_password') as mock_verify, \
         patch('auth.utils.create_access_token') as mock_token:
        
        mock_verify.return_value = True
        mock_token.return_value = "mocked_token"
        
        # Mock the database query to return a user object
        from unittest.mock import MagicMock
        mock_user = MagicMock()
        mock_user.id = "12345"
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.role = "user"
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query_instance = mock_query.return_value
            mock_query_instance.filter.return_value.first.return_value = mock_user
            
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["user"]["email"] == "test@example.com"


def test_login_invalid_credentials(client, mock_db_session):
    """Test login with invalid credentials"""
    with patch('auth.utils.verify_password') as mock_verify:
        mock_verify.return_value = False  # Password doesn't match
        
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401  # Unauthorized


def test_login_inactive_user(client, mock_db_session):
    """Test login attempt by inactive user"""
    with patch('auth.utils.verify_password') as mock_verify, \
         patch('auth.utils.create_access_token') as mock_token:
        
        mock_verify.return_value = True  # Password matches
        mock_token.return_value = "mocked_token"
        
        # Mock user with is_active = False
        from unittest.mock import MagicMock
        mock_user = MagicMock()
        mock_user.id = "12345"
        mock_user.email = "inactive@example.com"
        mock_user.is_active = False  # User is inactive
        
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            mock_query_instance = mock_query.return_value
            mock_query_instance.filter.return_value.first.return_value = mock_user
            
            login_data = {
                "email": "inactive@example.com",
                "password": "validpassword"
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 423  # Locked