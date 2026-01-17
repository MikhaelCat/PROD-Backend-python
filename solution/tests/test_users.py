"""тесты для эндпоинтов пользователя"""

import pytest
from unittest.mock import patch


def test_get_current_user(client, mock_auth_dependencies):
    """тест получения информации о текущем пользователе"""
    # настройка мок-пользователя
    mock_user = {
        "id": "12345",
        "email": "test@example.com", 
        "full_name": "test user",
        "role": "user",
        "is_active": true
    }
    mock_auth_dependencies.return_value = mock_user
    
    response = client.get("/api/v1/users/me")
    
    # должен завершиться успешно с кодом 200 ok
    assert response.status_code == 200
    
    # проверка, что данные в ответе совпадают с мок-пользователем
    data = response.json()
    assert data["id"] == mock_user["id"]
    assert data["email"] == mock_user["email"]
    assert data["full_name"] == mock_user["full_name"]


def test_update_user_profile(client, mock_auth_dependencies):
    """тест обновления профиля пользователя"""
    # настройка мок-пользователя
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "test user",
        "role": "user",
        "is_active": true
    }
    mock_auth_dependencies.return_value = mock_user
    
    update_data = {
        "full_name": "updated name",
        "age": 30,
        "region": "updated region"
    }
    
    response = client.patch("/api/v1/users/me", json=update_data)
    
    # должен завершиться успешно с кодом 200 ok
    assert response.status_code == 200
    
    # проверка, что ответ содержит обновлённые данные
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["age"] == update_data["age"]
    assert data["region"] == update_data["region"]


def test_get_users_list(client, mock_auth_dependencies):
    """тест получения списка пользователей (только для администратора)"""
    # мок-администратор
    mock_admin = {
        "id": "admin123",
        "email": "admin@example.com",
        "full_name": "admin user",
        "role": "admin",
        "is_active": true
    }
    mock_auth_dependencies.return_value = mock_admin
    
    response = client.get("/api/v1/users/")
    
    # должен завершиться успешно с кодом 200 ok
    assert response.status_code == 200
    
    # ответ должен быть списком
    data = response.json()
    assert isinstance(data, list)


def test_get_users_list_non_admin(client, mock_auth_dependencies):
    """тест, что обычные пользователи не могут получить список пользователей"""
    # мок-обычный пользователь
    mock_user = {
        "id": "12345",
        "email": "test@example.com",
        "full_name": "test user",
        "role": "user",  # обычный пользователь, не админ
        "is_active": true
    }
    mock_auth_dependencies.return_value = mock_user
    
    response = client.get("/api/v1/users/")
    
    # должен вернуться код 403 forbidden
    assert response.status_code == 403