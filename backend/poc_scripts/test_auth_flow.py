import asyncio
import httpx
import sys
import os

# Add backend directory to sys.path to allow imports if needed, 
# though we are testing via HTTP so it's less critical unless we want to check DB directly.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "http://localhost:8000/api/v1"

async def test_auth_flow():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        print(f"Testing against {BASE_URL}")
        
        # 1. Signup
        email = f"test_auth_{os.urandom(4).hex()}@example.com"
        password = "password123"
        print(f"\n1. Signing up user: {email}")
        
        signup_data = {
            "email": email,
            "full_name": "Test Auth User",
            "password": password # Note: Signup endpoint might not take password directly based on previous context, checking...
        }
        
        # Based on previous context, signup takes UserCreate which has email/full_name
        # And then there is a set_password endpoint? Or maybe I should check the schema.
        # Let's try standard signup first.
        
        try:
            # Check if we need to call signup then set_password or if signup handles it.
            # Looking at auth.py: signup takes UserCreate (email, full_name). 
            # Then set_password takes UserSetPassword (user_id, password).
            
            # Step 1: Signup
            response = await client.post("/auth/signup", json={"email": email, "full_name": "Test Auth User"})
            print(f"Signup Response: {response.status_code}")
            if response.status_code != 200:
                print(f"Signup Failed: {response.text}")
                return
            
            user_data = response.json()
            user_id = user_data["id"]
            print(f"User created with ID: {user_id}")
            
            # Step 2: Set Password
            print(f"\n2. Setting password for user_id: {user_id}")
            response = await client.post("/auth/set_password", json={"user_id": user_id, "password": password})
            print(f"Set Password Response: {response.status_code}")
            if response.status_code != 200:
                print(f"Set Password Failed: {response.text}")
                return
                
            # Step 3: Login
            print(f"\n3. Logging in")
            login_data = {
                "email": email,
                "password": password
            }
            response = await client.post("/auth/login", json=login_data)
            print(f"Login Response: {response.status_code}")
            if response.status_code != 200:
                print(f"Login Failed: {response.text}")
                return
            
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"Got Access Token: {access_token[:20]}...")
            
            # Step 4: Access Protected Endpoint
            print(f"\n4. Accessing Protected Endpoint (/jobs/)")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get("/jobs/", headers=headers)
            print(f"Protected Endpoint Response: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS: Backend auth flow is working correctly.")
                print(f"Jobs: {response.json()}")
            else:
                print(f"FAILURE: Could not access protected endpoint. Status: {response.status_code}")
                print(f"Response: {response.text}")
                
            # Step 5: Test Download
            print(f"\n5. Testing Download Endpoint")
            job_id = "687a77c8-613f-4c8e-b824-cda2d003733f"
            candidate_id = "2ff99138-f21c-4d00-b22a-72ea6598edf5"
            download_url = f"/jobs/{job_id}/candidates/{candidate_id}/download"
            print(f"Downloading from: {download_url}")
            
            response = await client.get(download_url, headers=headers)
            print(f"Download Response: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {response.headers.get('content-length')}")
            print(f"Body size: {len(response.content)} bytes")
            if response.status_code != 200:
                 print(f"Error Body: {response.text}")
                
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
