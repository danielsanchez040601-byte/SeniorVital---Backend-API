import httpx
import json

GATEWAY_URL = "http://127.0.0.1:8000"

def test_flow():
    print("1. Testing POST /auth/login...")
    login_data = {"email": "senior@seniorvital.com", "password": "password123"}
    resp = httpx.post(f"{GATEWAY_URL}/auth/login", json=login_data)
    print("Login Status:", resp.status_code)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    print("Token received successfully.")

    headers = {"Authorization": f"Bearer {token}"}

    print("\n2. Testing GET /auth/me...")
    resp = httpx.get(f"{GATEWAY_URL}/auth/me", headers=headers)
    print("Me Status:", resp.status_code)
    assert resp.status_code == 200, f"Me failed: {resp.text}"
    user_info = resp.json()
    user_id = user_info["id"]
    print("User Info:", user_info)

    print("\n3. Testing POST /routines/generate...")
    gen_data = {"user_id": user_id, "force": True}
    resp = httpx.post(f"{GATEWAY_URL}/routines/generate", json=gen_data, headers=headers)
    print("Generate Routine Status:", resp.status_code)
    print("Generate Routine Response:", resp.text)
    assert resp.status_code == 200, f"Generate routine failed: {resp.text}"

    print("\n4. Testing GET /routines/today...")
    resp = httpx.get(f"{GATEWAY_URL}/routines/today?user_id={user_id}", headers=headers)
    print("Get Today Routine Status:", resp.status_code)
    print("Get Today Routine Response:", resp.text)
    assert resp.status_code == 200, f"Get today routine failed: {resp.text}"

    print("\n5. Testing GET /catalog/exercises...")
    resp = httpx.get(f"{GATEWAY_URL}/catalog/exercises", headers=headers)
    print("Catalog Status:", resp.status_code)
    print("Catalog Count:", len(resp.json()))
    assert resp.status_code == 200, f"Catalog failed: {resp.text}"

    print("\n6. Testing POST /tracking/record (exercise finish)...")
    tracking_data = {
        "user_id": user_id,
        "exercise_id": "00000000-0000-0000-0000-000000000000",
        "sets": 2,
        "reps": 10,
        "rpe": 6,
        "felt_difficulty": "moderado"
    }
    resp = httpx.post(f"{GATEWAY_URL}/tracking/record", json=tracking_data, headers=headers)
    print("Record Status:", resp.status_code)
    print("Record Response:", resp.text)
    assert resp.status_code == 200, f"Tracking record failed: {resp.text}"

    print("\n7. Testing POST /tracking/habits...")
    habits_data = {
        "user_id": user_id,
        "water_glasses": 6,
        "walking_minutes": 25,
        "meds_taken": True
    }
    resp = httpx.post(f"{GATEWAY_URL}/tracking/habits", json=habits_data, headers=headers)
    print("Habits Status:", resp.status_code)
    print("Habits Response:", resp.text)
    assert resp.status_code == 200, f"Habits failed: {resp.text}"

    print("\n8. Testing GET /tracking/habits...")
    resp = httpx.get(f"{GATEWAY_URL}/tracking/habits?user_id={user_id}", headers=headers)
    print("Get Habits Status:", resp.status_code)
    print("Get Habits Response:", resp.text)
    assert resp.status_code == 200, f"Get habits failed: {resp.text}"

    print("\nAll flow steps completed successfully!")

if __name__ == "__main__":
    test_flow()
