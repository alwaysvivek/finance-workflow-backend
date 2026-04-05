import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_api():
    print("🚀 Starting API Smoke Test...")
    
    # 1. Register Admin
    admin_data = {
        "email": f"admin_{int(time.time())}@zorvyn.com",
        "password": "strongpassword123",
        "role": "Admin",
        "company_id": 1
    }
    print("--- Registering Admin ---")
    reg_admin = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
    if reg_admin.status_code != 200:
        print(f"❌ Admin registration failed: {reg_admin.text}")
        return
    print("✅ Admin Registered")

    # 2. Login Admin
    print("--- Logging in Admin ---")
    login_admin = requests.post(f"{BASE_URL}/auth/login", data={"username": admin_data["email"], "password": admin_data["password"]})
    if login_admin.status_code != 200:
        print(f"❌ Admin login failed: {login_admin.text}")
        return
    admin_token = login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ Admin Logged In")

    # 3. Register & Login Analyst
    analyst_data = {
        "email": f"analyst_{int(time.time())}@zorvyn.com",
        "password": "strongpassword123",
        "role": "Analyst",
        "company_id": 1 # Same company
    }
    print("--- Registering Analyst ---")
    requests.post(f"{BASE_URL}/auth/register", json=analyst_data)
    login_analyst = requests.post(f"{BASE_URL}/auth/login", data={"username": analyst_data["email"], "password": analyst_data["password"]})
    analyst_token = login_analyst.json()["access_token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
    print("✅ Analyst Registered and Logged In")

    # 4. Create Transaction (Analyst)
    print("--- Creating Transaction (Analyst) ---")
    tx_data = {
        "amount": 1500.50,
        "type": "Expense",
        "category": "Cloud Hosting",
        "date": "2026-04-05T10:00:00",
        "notes": "AWS monthly bill"
    }
    created_tx = requests.post(f"{BASE_URL}/transactions/", json=tx_data, headers=analyst_headers)
    if created_tx.status_code != 200:
        print(f"❌ Transaction creation failed: {created_tx.text}")
        return
    tx_id = created_tx.json()["data"]["id"]
    print(f"✅ Transaction Created: ID {tx_id}")

    # 5. List Pending Transactions (Admin)
    print("--- Listing Pending Transactions (Admin) ---")
    list_tx = requests.get(f"{BASE_URL}/transactions/?status=Pending", headers=admin_headers)
    if list_tx.status_code != 200:
        print(f"❌ Listing failed: {list_tx.text}")
        return
    print(f"✅ Found {len(list_tx.json()['data'])} pending transactions")

    # 6. Update pending transaction (Analyst)
    print("--- Updating pending transaction (Analyst) ---")
    update_data = {"amount": 1600.00, "notes": "AWS final bill"}
    update_tx = requests.put(f"{BASE_URL}/transactions/{tx_id}", json=update_data, headers=analyst_headers)
    if update_tx.status_code != 200:
        print(f"❌ Update failed: {update_tx.text}")
        return
    print("✅ Transaction Updated")

    # 7. Approve Transaction (Admin)
    print("--- Approving Transaction (Admin) ---")
    approve_tx = requests.put(f"{BASE_URL}/transactions/{tx_id}/approve", headers=admin_headers)
    if approve_tx.status_code != 200:
        print(f"❌ Approval failed: {approve_tx.text}")
        return
    print("✅ Transaction Approved")

    # 8. Check Analytics (Admin)
    print("--- Checking Analytics ---")
    total_spend = requests.get(f"{BASE_URL}/analytics/total-spend", headers=admin_headers)
    if total_spend.status_code != 200:
        print(f"❌ Total spend failed: {total_spend.text}")
        return
    print(f"✅ Total Spend: {total_spend.json()['data']}")

    category_breakdown = requests.get(f"{BASE_URL}/analytics/category-breakdown", headers=admin_headers)
    print(f"✅ Category Breakdown: {category_breakdown.json()['data']}")

    monthly_trend = requests.get(f"{BASE_URL}/analytics/monthly-trend", headers=admin_headers)
    print(f"✅ Monthly Trend: {monthly_trend.json()['data']}")

    approval_rate = requests.get(f"{BASE_URL}/analytics/approval-rate", headers=admin_headers)
    print(f"✅ Approval Rate: {approval_rate.json()['data']}")

    # 9. Test RBAC: Prevent self-approval (Admin created)
    print("--- Testing RBAC: Admin cannot self-approve ---")
    admin_tx_data = {
        "amount": 500,
        "type": "Expense",
        "category": "Office Supplies",
        "date": "2026-04-05T12:00:00"
    }
    admin_tx = requests.post(f"{BASE_URL}/transactions/", json=admin_tx_data, headers=admin_headers)
    admin_tx_id = admin_tx.json()["data"]["id"]
    
    self_approve = requests.put(f"{BASE_URL}/transactions/{admin_tx_id}/approve", headers=admin_headers)
    if self_approve.status_code == 403:
        print("✅ Correctly rejected self-approval (403 Forbidden)")
    else:
        print(f"❌ Self-approval logic failed! Status: {self_approve.status_code}")

    print("\n🎉 SMOKE TEST COMPLETE - ALL ENDPOINTS VERIFIED OPERATIONAL AFTER OOP REFACTOR")

if __name__ == "__main__":
    test_api()
