import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "test@example.com"
PASSWORD = "password"

def debug_score():
    # Login
    try:
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        login_resp.raise_for_status()
        token = login_resp.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Fetch Jobs
    try:
        jobs_resp = requests.get(f"{BASE_URL}/jobs", headers=headers)
        jobs_resp.raise_for_status()
        jobs = jobs_resp.json()
        print(f"Found {len(jobs)} jobs.")
    except Exception as e:
        print(f"Fetch jobs failed: {e}")
        return

    # Fetch Candidates for first job
    if jobs:
        job_id = jobs[0]['id']
        print(f"Checking candidates for Job ID: {job_id}")
        try:
            cand_resp = requests.get(f"{BASE_URL}/jobs/{job_id}/candidates", headers=headers)
            cand_resp.raise_for_status()
            candidates = cand_resp.json()
            print(f"Found {len(candidates)} candidates.")
            for i, c in enumerate(candidates):
                print(f"Candidate {i}: match_score={c.get('match_score')}, score={c.get('score')}, ranking_score={c.get('ranking_score')}")
        except Exception as e:
            print(f"Fetch candidates failed: {e}")

if __name__ == "__main__":
    debug_score()
