"""Tests for fraud rules endpoints"""

import pytest
from unittest.mock import patch


def test_create_fraud_rule(client, mock_auth_dependencies):
    """Test creating a new fraud rule (admin only)"""
    # Mock an admin user
    mock_admin = {
        "id": "admin123",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_admin
    
    rule_data = {
        "name": "High Amount Rule",
        "description": "Flags transactions over a certain amount",
        "expression": "amount > 5000",
        "severity": "high",
        "is_active": True
    }
    
    response = client.post("/api/v1/fraud-rules/", json=rule_data)
    
    # Should succeed with 201 Created for admin
    assert response.status_code == 201
    
    # Check response structure
    data = response.json()
    assert "id" in data
    assert data["name"] == rule_data["name"]
    assert data["expression"] == rule_data["expression"]


def test_create_fraud_rule_non_admin(client, mock_auth_dependencies):
    """Test that non-admin users can't create fraud rules"""
    # Mock a regular user
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",  # Regular user, not admin
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_user
    
    rule_data = {
        "name": "Unauthorized Rule",
        "description": "This shouldn't be created",
        "expression": "amount > 1000",
        "severity": "medium",
        "is_active": True
    }
    
    response = client.post("/api/v1/fraud-rules/", json=rule_data)
    
    # Should fail with 403 Forbidden for non-admin
    assert response.status_code == 403


def test_get_fraud_rules(client, mock_auth_dependencies):
    """Test retrieving fraud rules"""
    # Mock a user (can be admin or regular - both should be able to view rules)
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_user
    
    # Mock the database query to return a list of rules
    with patch('sqlalchemy.orm.Session.query') as mock_query:
        mock_rules = [
            {
                "id": "rule1",
                "name": "High Amount Rule",
                "description": "Flags high amount transactions",
                "expression": "amount > 5000",
                "severity": "high",
                "is_active": True
            },
            {
                "id": "rule2",
                "name": "Suspicious Time Rule", 
                "description": "Flags transactions at suspicious times",
                "expression": "hour < 6 or hour > 22",
                "severity": "medium",
                "is_active": True
            }
        ]
        mock_query_instance = mock_query.return_value
        mock_query_instance.all.return_value = mock_rules
        
        response = client.get("/api/v1/fraud-rules/")
        
        # Should succeed with 200 OK
        assert response.status_code == 200
        
        # Check response is a list with expected items
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] == "rule1"
        assert data[1]["id"] == "rule2"


def test_get_fraud_rule_by_id(client, mock_auth_dependencies):
    """Test retrieving a specific fraud rule"""
    # Mock a user
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_user
    
    # Mock the database query to return a specific rule
    with patch('sqlalchemy.orm.Session.query') as mock_query:
        mock_rule = {
            "id": "rule123",
            "name": "Test Rule",
            "description": "A test fraud rule",
            "expression": "amount < 0",
            "severity": "critical",
            "is_active": True
        }
        mock_query_instance = mock_query.return_value
        mock_query_instance.filter.return_value.first.return_value = mock_rule
        
        response = client.get("/api/v1/fraud-rules/rule123")
        
        # Should succeed with 200 OK
        assert response.status_code == 200
        
        # Check response data
        data = response.json()
        assert data["id"] == "rule123"
        assert data["name"] == "Test Rule"


def test_update_fraud_rule(client, mock_auth_dependencies):
    """Test updating a fraud rule (admin only)"""
    # Mock an admin user
    mock_admin = {
        "id": "admin123",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_admin
    
    update_data = {
        "name": "Updated Rule Name",
        "description": "Updated description",
        "severity": "critical",
        "is_active": False
    }
    
    response = client.patch("/api/v1/fraud-rules/rule123", json=update_data)
    
    # Should succeed with 200 OK for admin
    assert response.status_code == 200
    
    # Check response contains updated data
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["severity"] == update_data["severity"]
    assert data["is_active"] == update_data["is_active"]


def test_delete_fraud_rule(client, mock_auth_dependencies):
    """Test deleting a fraud rule (admin only)"""
    # Mock an admin user
    mock_admin = {
        "id": "admin123",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_admin
    
    response = client.delete("/api/v1/fraud-rules/rule123")
    
    # Should succeed with 204 No Content for admin
    assert response.status_code == 204