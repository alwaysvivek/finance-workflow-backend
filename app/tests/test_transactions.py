from fastapi.testclient import TestClient
from app.tests.conftest import get_token_headers
from app.core.config import settings

def test_rbac_viewer_cannot_create_transaction(client: TestClient, setup_data: dict):
    viewer1 = setup_data["viewer1"]
    headers = get_token_headers(viewer1)
    
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=headers,
        json={
            "amount": "100.50",
            "type": "Expense",
            "category": "Software",
            "date": "2024-03-15T00:00:00Z"
        }
    )
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Not enough permissions"

def test_admin_can_create_transaction(client: TestClient, setup_data: dict):
    admin1 = setup_data["admin1"]
    headers = get_token_headers(admin1)
    
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=headers,
        json={
            "amount": "1500.00",
            "type": "Expense",
            "category": "Office Supplies",
            "date": "2024-03-15T00:00:00Z"
        }
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["amount"] == "1500.00"
    assert data["status"] == "Pending"

def test_multi_tenant_isolation(client: TestClient, setup_data: dict):
    admin1 = setup_data["admin1"]
    admin2 = setup_data["admin2"]
    
    headers_admin1 = get_token_headers(admin1)
    headers_admin2 = get_token_headers(admin2)
    
    # Admin 1 creates tx
    response1 = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=headers_admin1,
        json={
            "amount": "200.00",
            "type": "Expense",
            "category": "Advertising",
            "date": "2024-03-15T00:00:00Z"
        }
    )
    tx_id = response1.json()["data"]["id"]
    
    # Admin 2 tries to approve Admin 1's tx (should be 404 because not found in company)
    response2 = client.put(
        f"{settings.API_V1_STR}/transactions/{tx_id}/approve",
        headers=headers_admin2
    )
    assert response2.status_code == 404

def test_cannot_self_approve(client: TestClient, setup_data: dict):
    admin1 = setup_data["admin1"]
    headers = get_token_headers(admin1)
    
    response = client.post(
        f"{settings.API_V1_STR}/transactions/",
        headers=headers,
        json={
            "amount": "300.00",
            "type": "Income",
            "category": "Sales",
            "date": "2024-03-15T00:00:00Z"
        }
    )
    tx_id = response.json()["data"]["id"]
    
    response_approve = client.put(
        f"{settings.API_V1_STR}/transactions/{tx_id}/approve",
        headers=headers
    )
    # the self-approve check triggers 403
    assert response_approve.status_code == 403
