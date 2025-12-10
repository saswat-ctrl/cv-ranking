import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "test@example.com"
PASSWORD = "password"

def test_api():
    # Login
    try:
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        login_resp.raise_for_status()
        token = login_resp.json()["access_token"]
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        if login_resp:
            print(login_resp.text)
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Fetch Jobs
    try:
        jobs_resp = requests.get(f"{BASE_URL}/jobs", headers=headers)
        jobs_resp.raise_for_status()
        jobs = jobs_resp.json()
        print(f"Jobs fetched: {len(jobs)}")
        if len(jobs) > 0:
            print("Job 0 structure:", json.dumps(jobs[0], indent=2))
    except Exception as e:
        print(f"Fetch jobs failed: {e}")
        if jobs_resp:
            print(jobs_resp.text)

    # Fetch Me
    try:
        me_resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        me_resp.raise_for_status()
        me = me_resp.json()
        print("Me structure:", json.dumps(me, indent=2))
    except Exception as e:
        print(f"Fetch me failed: {e}")

if __name__ == "__main__":
    test_api()
