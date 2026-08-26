"""Smoke tests for all SeniorVital services."""
import httpx, sys, json, uuid

BASE = "http://localhost"
tests = []

def check(name, status, result):
    ok = "PASS" if status else "FAIL"
    print(f"  [{ok}] {name}: {result}")
    return status

print("=== SeniorVital Smoke Tests ===\n")

# Helper: create senior user
def create_senior(email):
    r = httpx.post(f"{BASE}:8001/auth/register", json={"email":email,"password":"test123","role":"senior"}, timeout=5)
    if r.status_code == 200:
        return r.json()["id"]
    # If already exists, login to get id
    r2 = httpx.post(f"{BASE}:8001/auth/login", json={"email":email,"password":"test123"}, timeout=5)
    # Can't get id from login response, so just create with unique email
    return None

# 1. Auth Service
print("1. Auth Service (port 8001)")
try:
    r = httpx.post(f"{BASE}:8001/auth/register", json={"email":"smoke@test.com","password":"test123","role":"senior"}, timeout=5)
    uid = r.json().get("id","")
    tests.append(check("Register", r.status_code in (200,400), f"{r.status_code} user_id={uid[:8] if uid else 'exists'}"))
except Exception as e:
    tests.append(check("Register", False, str(e)))
try:
    r = httpx.post(f"{BASE}:8001/auth/login", json={"email":"smoke@test.com","password":"test123"}, timeout=5)
    token = r.json().get("access_token","")
    tests.append(check("Login", r.status_code==200 and len(token)>0, f"{r.status_code} token_len={len(token)}"))
except Exception as e:
    tests.append(check("Login", False, str(e)))

# 2. Catalog Service
print("\n2. Catalog Service (port 8002)")
ex_id = None
try:
    r = httpx.post(f"{BASE}:8002/catalog/exercises", json={
        "name":"Sentadillas","level":1,"contraindications":[]
    }, timeout=5)
    ex_id = r.json().get("id","") if r.status_code==201 else ""
    tests.append(check("Create exercise", r.status_code==201, f"{r.status_code} id={ex_id[:8] if ex_id else 'none'}"))
except Exception as e:
    tests.append(check("Create exercise", False, str(e)))
try:
    r = httpx.get(f"{BASE}:8002/catalog/exercises", timeout=5)
    tests.append(check("List exercises", r.status_code==200, f"{r.status_code} count={len(r.json())}"))
except Exception as e:
    tests.append(check("List exercises", False, str(e)))
try:
    if ex_id:
        r = httpx.get(f"{BASE}:8002/catalog/exercises/{ex_id}", timeout=5)
        tests.append(check("Get exercise", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Get exercise", False, str(e)))

# 3. Routines-AI Service
print("\n3. Routines-AI Service (port 8003)")
try:
    r = httpx.post(f"{BASE}:8003/routines/generate", json={"user_id":"00000000-0000-0000-0000-000000000000"}, timeout=10)
    tests.append(check("Generate routine (no user)", r.status_code in (404,500,503), f"{r.status_code}"))
except Exception as e:
    tests.append(check("Generate routine (no user)", False, str(e)))

# 4. Tracking Service - first create real user
print("\n4. Tracking Service (port 8004)")
track_uid = None
try:
    # Create a fresh user for tracking (FK constraint)
    uniq = str(uuid.uuid4())[:8]
    r = httpx.post(f"{BASE}:8001/auth/register", json={"email":f"track_{uniq}@test.com","password":"test123","role":"senior"}, timeout=5)
    if r.status_code == 200:
        track_uid = r.json()["id"]
    tests.append(check("Create tracking user", r.status_code==200, f"{r.status_code} uid={track_uid[:8] if track_uid else 'none'}"))
except Exception as e:
    tests.append(check("Create tracking user", False, str(e)))

try:
    if track_uid:
        r = httpx.post(f"{BASE}:8004/tracking/record", json={
            "user_id": track_uid,
            "exercise_id": "ex1",
            "sets": 3, "reps": 12, "rpe": 5
        }, timeout=5)
        tests.append(check("Record exercise", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Record exercise", False, str(e)))

try:
    if track_uid:
        r = httpx.post(f"{BASE}:8004/tracking/record", json={
            "user_id": track_uid,
            "exercise_id": "ex2",
            "sets": 3, "reps": 10, "rpe": 9
        }, timeout=5)
        tests.append(check("High fatigue (rpe=9)", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("High fatigue (rpe=9)", False, str(e)))

# 5. Dashboard Service
print("\n5. Dashboard Service (port 8005)")
try:
    r = httpx.get(f"{BASE}:8005/dashboard/insights/00000000-0000-0000-0000-000000000000", timeout=5)
    tests.append(check("Insights (empty)", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Insights (empty)", False, str(e)))
try:
    r = httpx.get(f"{BASE}:8005/dashboard/progress/00000000-0000-0000-0000-000000000000", timeout=5)
    tests.append(check("Progress (no user)", r.status_code==404, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Progress (no user)", False, str(e)))
try:
    if track_uid:
        r = httpx.get(f"{BASE}:8005/dashboard/progress/{track_uid}", timeout=5)
        tests.append(check("Progress (real user)", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Progress (real user)", False, str(e)))

# 6. Notification Service
print("\n6. Notification Service (port 8006)")
try:
    r = httpx.post(f"{BASE}:8006/notify/subscribe", json={
        "user_id":"smoke@test.com",
        "subscription":{"endpoint":"https://fake.push/api","keys":{"p256dh":"abc123","auth":"def456"}}
    }, timeout=5)
    tests.append(check("Subscribe", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Subscribe", False, str(e)))
try:
    r = httpx.post(f"{BASE}:8006/notify/send", json={"user_id":"smoke@test.com","title":"Test","body":"Test body"}, timeout=5)
    tests.append(check("Send notification", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Send notification", False, str(e)))

# 7. API Gateway
print("\n7. API Gateway (port 8000)")
try:
    r = httpx.get(f"{BASE}:8000/catalog/exercises", timeout=5)
    tests.append(check("Gateway proxy /catalog/", r.status_code==200, f"{r.status_code} count={len(r.json())}"))
except Exception as e:
    tests.append(check("Gateway proxy /catalog/", False, str(e)))
try:
    r = httpx.post(f"{BASE}:8000/auth/login", json={"email":"smoke@test.com","password":"test123"}, timeout=5)
    tests.append(check("Gateway proxy /auth/ login", r.status_code==200, f"{r.status_code}"))
except Exception as e:
    tests.append(check("Gateway proxy /auth/ login", False, str(e)))

# Summary
print("\n" + "="*40)
passed = sum(1 for t in tests if t)
total = len(tests)
print(f"Result: {passed}/{total} passed")
if passed < total:
    sys.exit(1)
