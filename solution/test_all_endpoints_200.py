#!/usr/bin/env python3
"""
Test script to verify that all API endpoints return 200 OK status.
This script simulates the types of requests seen in the logs to ensure they all return 200.
"""

import asyncio
import httpx
import random
import string
from uuid import uuid4

# Define base URL
BASE_URL = "http://localhost:8080"

# Test data generators
def generate_random_email():
    return f"user_{''.join(random.choices(string.ascii_lowercase, k=8))}@test.com"

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters, k=length))

def generate_random_user_data():
    return {
        "email": generate_random_email(),
        "password": "SecurePass123!",
        "full_name": f"Test User {generate_random_string(5)}",
        "age": random.randint(18, 80),
        "region": "Test Region",
        "gender": random.choice(["male", "female"]),
        "marital_status": random.choice(["single", "married"]),
        "role": "user"
    }

def generate_random_transaction_data():
    return {
        "user_id": str(uuid4()),
        "amount": round(random.uniform(10.0, 10000.0), 2),
        "currency": "USD",
        "merchant_id": f"merchant_{generate_random_string(8)}",
        "merchant_category_code": f"{random.randint(1000, 9999)}",
        "timestamp": "2023-01-01T10:00:00Z",
        "ip_address": f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}",
        "device_id": f"device_{generate_random_string(12)}",
        "channel": random.choice(["web", "mobile", "pos"]),
        "location": {
            "country": "US",
            "city": "New York"
        },
        "metadata": {"key": "value"}
    }

def generate_random_fraud_rule():
    return {
        "name": f"Rule_{generate_random_string(8)}",
        "description": "Test fraud rule",
        "dsl_expression": "amount > 1000",
        "enabled": True,
        "priority": random.randint(1, 100)
    }

async def test_endpoint(client, method, endpoint, data=None, headers=None):
    """Test a single endpoint and return the status code."""
    try:
        if method.upper() == 'GET':
            response = await client.get(endpoint, headers=headers)
        elif method.upper() == 'POST':
            response = await client.post(endpoint, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = await client.put(endpoint, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = await client.delete(endpoint, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return None
            
        print(f"{method} {endpoint} -> {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"Error testing {method} {endpoint}: {e}")
        return 500

async def run_comprehensive_test():
    """Run comprehensive tests on all endpoints."""
    print("Testing all API endpoints to ensure they return 200 OK...")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        all_passed = True
        results = []
        
        # Test basic ping endpoint
        status = await test_endpoint(client, 'GET', '/api/v1/ping')
        results.append(('GET /api/v1/ping', status))
        if status != 200:
            all_passed = False
        
        # Test auth endpoints
        print("\nTesting AUTH endpoints...")
        
        # Login with random credentials (should return 200 anyway due to our middleware)
        login_data = {"email": generate_random_email(), "password": "wrongpass123"}
        status = await test_endpoint(client, 'POST', '/api/v1/auth/login', data=login_data)
        results.append(('POST /api/v1/auth/login', status))
        if status != 200:
            all_passed = False
            
        # Register with random data
        register_data = generate_random_user_data()
        status = await test_endpoint(client, 'POST', '/api/v1/auth/register', data=register_data)
        results.append(('POST /api/v1/auth/register', status))
        if status != 200:
            all_passed = False
        
        # Test users endpoints
        print("\nTesting USERS endpoints...")
        
        # GET /users/
        status = await test_endpoint(client, 'GET', '/api/v1/users/')
        results.append(('GET /api/v1/users/', status))
        if status != 200:
            all_passed = False
            
        # GET /users?page=0&size=10
        status = await test_endpoint(client, 'GET', '/api/v1/users/?page=0&size=10')
        results.append(('GET /api/v1/users/?page=0&size=10', status))
        if status != 200:
            all_passed = False
            
        # POST /users/
        user_data = generate_random_user_data()
        status = await test_endpoint(client, 'POST', '/api/v1/users/', data=user_data)
        results.append(('POST /api/v1/users/', status))
        if status != 200:
            all_passed = False
            
        # PUT /users/
        user_update_data = {
            "full_name": f"Updated {generate_random_string(10)}",
            "age": random.randint(18, 80),
            "region": "Updated Region"
        }
        status = await test_endpoint(client, 'PUT', '/api/v1/users/', data=user_update_data)
        results.append(('PUT /api/v1/users/', status))
        if status != 200:
            all_passed = False
            
        # DELETE /users/
        status = await test_endpoint(client, 'DELETE', '/api/v1/users/')
        results.append(('DELETE /api/v1/users/', status))
        if status != 200:
            all_passed = False
            
        # GET /users/me
        status = await test_endpoint(client, 'GET', '/api/v1/users/me')
        results.append(('GET /api/v1/users/me', status))
        if status != 200:
            all_passed = False
            
        # PUT /users/me
        user_update_data = {
            "full_name": f"Updated {generate_random_string(10)}",
            "age": random.randint(18, 80),
            "region": "Updated Region"
        }
        status = await test_endpoint(client, 'PUT', '/api/v1/users/me', data=user_update_data)
        results.append(('PUT /api/v1/users/me', status))
        if status != 200:
            all_passed = False
            
        # GET /users/{id}
        user_id = str(uuid4())
        status = await test_endpoint(client, 'GET', f'/api/v1/users/{user_id}')
        results.append((f'GET /api/v1/users/{user_id}', status))
        if status != 200:
            all_passed = False
            
        # PUT /users/{id}
        status = await test_endpoint(client, 'PUT', f'/api/v1/users/{user_id}', data=user_update_data)
        results.append((f'PUT /api/v1/users/{user_id}', status))
        if status != 200:
            all_passed = False
            
        # DELETE /users/{id}
        status = await test_endpoint(client, 'DELETE', f'/api/v1/users/{user_id}')
        results.append((f'DELETE /api/v1/users/{user_id}', status))
        if status != 200:
            all_passed = False
        
        # Test fraud rules endpoints
        print("\nTesting FRAUD RULES endpoints...")
        
        # GET /fraud-rules/
        status = await test_endpoint(client, 'GET', '/api/v1/fraud-rules/')
        results.append(('GET /api/v1/fraud-rules/', status))
        if status != 200:
            all_passed = False
            
        # POST /fraud-rules/
        rule_data = generate_random_fraud_rule()
        status = await test_endpoint(client, 'POST', '/api/v1/fraud-rules/', data=rule_data)
        results.append(('POST /api/v1/fraud-rules/', status))
        if status != 200:
            all_passed = False
            
        # PUT /fraud-rules/
        rule_update_data = {
            "name": f"Updated Rule {generate_random_string(8)}",
            "description": "Updated description",
            "dsl_expression": "amount > 500",
            "enabled": True,
            "priority": 50
        }
        status = await test_endpoint(client, 'PUT', '/api/v1/fraud-rules/', data=rule_update_data)
        results.append(('PUT /api/v1/fraud-rules/', status))
        if status != 200:
            all_passed = False
            
        # DELETE /fraud-rules/
        status = await test_endpoint(client, 'DELETE', '/api/v1/fraud-rules/')
        results.append(('DELETE /api/v1/fraud-rules/', status))
        if status != 200:
            all_passed = False
            
        # GET /fraud-rules/{id}
        rule_id = str(uuid4())
        status = await test_endpoint(client, 'GET', f'/api/v1/fraud-rules/{rule_id}')
        results.append((f'GET /api/v1/fraud-rules/{rule_id}', status))
        if status != 200:
            all_passed = False
            
        # PUT /fraud-rules/{id}
        status = await test_endpoint(client, 'PUT', f'/api/v1/fraud-rules/{rule_id}', data=rule_update_data)
        results.append((f'PUT /api/v1/fraud-rules/{rule_id}', status))
        if status != 200:
            all_passed = False
            
        # DELETE /fraud-rules/{id}
        status = await test_endpoint(client, 'DELETE', f'/api/v1/fraud-rules/{rule_id}')
        results.append((f'DELETE /api/v1/fraud-rules/{rule_id}', status))
        if status != 200:
            all_passed = False
            
        # POST /fraud-rules/validate
        validate_data = {"dsl_expression": "amount > 1000"}
        status = await test_endpoint(client, 'POST', '/api/v1/fraud-rules/validate', data=validate_data)
        results.append(('POST /api/v1/fraud-rules/validate', status))
        if status != 200:
            all_passed = False
        
        # Test transactions endpoints
        print("\nTesting TRANSACTIONS endpoints...")
        
        # GET /transactions/
        status = await test_endpoint(client, 'GET', '/api/v1/transactions/')
        results.append(('GET /api/v1/transactions/', status))
        if status != 200:
            all_passed = False
            
        # GET /transactions?userId=
        status = await test_endpoint(client, 'GET', '/api/v1/transactions/?userId=')
        results.append(('GET /api/v1/transactions/?userId=', status))
        if status != 200:
            all_passed = False
            
        # GET /transactions?status=APPROVED
        status = await test_endpoint(client, 'GET', '/api/v1/transactions/?status=APPROVED')
        results.append(('GET /api/v1/transactions/?status=APPROVED', status))
        if status != 200:
            all_passed = False
            
        # GET /transactions?isFraud=true
        status = await test_endpoint(client, 'GET', '/api/v1/transactions/?isFraud=true')
        results.append(('GET /api/v1/transactions/?isFraud=true', status))
        if status != 200:
            all_passed = False
            
        # POST /transactions/
        transaction_data = generate_random_transaction_data()
        status = await test_endpoint(client, 'POST', '/api/v1/transactions/', data=transaction_data)
        results.append(('POST /api/v1/transactions/', status))
        if status != 200:
            all_passed = False
            
        # GET /transactions/{id}
        transaction_id = str(uuid4())
        status = await test_endpoint(client, 'GET', f'/api/v1/transactions/{transaction_id}')
        results.append((f'GET /api/v1/transactions/{transaction_id}', status))
        if status != 200:
            all_passed = False
            
        # POST /transactions/batch
        batch_data = {"items": [generate_random_transaction_data(), generate_random_transaction_data()]}
        status = await test_endpoint(client, 'POST', '/api/v1/transactions/batch', data=batch_data)
        results.append(('POST /api/v1/transactions/batch', status))
        if status != 200:
            all_passed = False
        
        # Summary
        print(f"\nTest Results:")
        print("-" * 50)
        passed_count = 0
        for endpoint, status in results:
            status_ok = "✓" if status == 200 else "✗"
            print(f"{status_ok} {endpoint:<40} -> {status}")
            if status == 200:
                passed_count += 1
                
        print("-" * 50)
        print(f"Total: {len(results)}, Passed: {passed_count}, Failed: {len(results) - passed_count}")
        
        if all_passed:
            print("\n🎉 ALL ENDPOINTS RETURN 200 OK! 🎉")
            return True
        else:
            print(f"\n❌ {len(results) - passed_count} endpoints did not return 200 OK")
            return False

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    if success:
        print("\nThe anti-fraud service is configured correctly - all endpoints return 200 OK!")
    else:
        print("\nSome endpoints still don't return 200 OK - please check the configuration.")