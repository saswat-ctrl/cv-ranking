#!/usr/bin/env python
import requests
import json

url = "http://localhost:8000/api/v1/auth/signup"
data = {"email": "direct_test@example.com", "name": "Direct Test"}

print(f"POST {url}")
print(f"Data: {json.dumps(data)}")

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code != 200:
        print(f"Headers: {response.headers}")
except Exception as e:
    print(f"Error: {e}")
