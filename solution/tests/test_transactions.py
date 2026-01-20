"""Tests for transaction endpoints"""

import pytest
from unittest.mock import patch


def test_create_transaction(client, mock_auth_dependencies):
    """Test creating a new transaction"""
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_user
    
    transaction_data = {
        "user_id": "12345",
        "amount": 100.50,
        "currency": "USD",
        "timestamp": "2023-01-01T10:00:00Z"
    }
    
    response = client.post("/api/v1/transactions/", json=transaction_data)
    
    # Should succeed with 201 Created
    assert response.status_code == 201
    
    # Check response structure
    data = response.json()
    assert "transaction" in data
    assert data["transaction"]["amount"] == transaction_data["amount"]
    assert data["transaction"]["currency"] == transaction_data["currency"]


def test_get_transaction_by_id(client, mock_auth_dependencies):
    """Test retrieving a specific transaction"""
    # Set up mock authenticated user
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_user
    
    # Mock the database query to return a transaction
    with patch('sqlalchemy.orm.Session.query') as mock_query:
        mock_transaction = {
            "id": "trans789",
            "user_id": "12345",
            "amount": 250.00,
            "currency": "EUR",
            "source_account": "acc789",
            "destination_account": "acc012",
            "status": "completed",
            "fraud_score": 0.1,
            "created_at": "2023-01-01T10:00:00Z",
            "timestamp": "2023-01-01T10:00:00Z"
        }
        mock_rule_result = {
            "rule_id": "rule1",
            "rule_name": "Test Rule",
            "priority": 1,
            "enabled": True,
            "matched": False,
            "description": "Test rule description"
        }
        
        mock_query_instance = mock_query.return_value
        mock_query_instance.filter.return_value.first.return_value = mock_transaction
        
        with patch('sqlalchemy.orm.Session.query') as mock_rule_query:
            mock_rule_query.return_value.filter.return_value.all.return_value = [mock_rule_result]
            
            response = client.get("/api/v1/transactions/trans789")
            
            # Should succeed with 200 OK
            assert response.status_code == 200
            
            # Check response data
            data = response.json()
            assert data["transaction"]["id"] == "trans789"
            assert data["transaction"]["amount"] == 250.00


def test_get_user_transactions(client, mock_auth_dependencies):
    """Test retrieving transactions for current user"""
    # Set up mock authenticated user
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_user
    
    # Mock the database query to return a list of transactions
    with patch('sqlalchemy.orm.Session.query') as mock_query:
        mock_transactions = [
            {
                "id": "trans001",
                "user_id": "12345",
                "amount": 100.00,
                "currency": "USD",
                "source_account": "acc123",
                "destination_account": "acc456",
                "status": "completed",
                "created_at": "2023-01-01T10:00:00Z",
                "timestamp": "2023-01-01T10:00:00Z"
            },
            {
                "id": "trans002", 
                "user_id": "12345",
                "amount": 50.25,
                "currency": "EUR",
                "source_account": "acc456",
                "destination_account": "acc789",
                "status": "pending",
                "created_at": "2023-01-01T10:00:00Z",
                "timestamp": "2023-01-01T10:00:00Z"
            }
        ]
        mock_query_instance = mock_query.return_value
        mock_query_instance.filter.return_value.all.return_value = mock_transactions
        
        response = client.get("/api/v1/transactions/")
        
        # Should succeed with 200 OK
        assert response.status_code == 200
        
        # Check response is a list with expected items
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["transaction"]["id"] == "trans001"
        assert data[1]["transaction"]["id"] == "trans002"


def test_fraud_check_on_transaction(client, mock_auth_dependencies):
    """Test that fraud rules are applied when creating a transaction"""
    # Set up mock authenticated user
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True
    }
    mock_auth_dependencies.return_value = mock_user
    
    # Mock transaction data that might trigger fraud rules
    high_risk_transaction = {
        "user_id": "12345",
        "amount": 10000.00,  # High amount
        "currency": "USD",
        "timestamp": "2023-01-01T10:00:00Z"
    }
    
    # Mock fraud rule checking
    with patch('dsl.validator.apply_fraud_rules') as mock_fraud_check:
        mock_fraud_check.return_value = {
            "is_fraud": True,
            "score": 0.95,
            "rules_triggered": ["high_amount_transaction"]
        }
        
        response = client.post("/api/v1/transactions/", json=high_risk_transaction)
        
        # Should still succeed (fraudulent transactions aren't rejected, just flagged)
        assert response.status_code == 201
        
        # Check that fraud score was included in response
        data = response.json()
        assert "transaction" in data
        assert data["transaction"]["is_fraud"] == True