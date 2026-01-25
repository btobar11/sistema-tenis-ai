import requests
import json

url = "https://hexpbbbsqkgowbrrorjt.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhleHBiYmJzcWtnb3dicnJvcmp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg5MzUzOTMsImV4cCI6MjA4NDUxMTM5M30.IZOYAX0jk-8VJ0C-eGBI718xKK1qFkmkGqg_MEfpuuo"

auth_url = f"{url}/auth/v1/token?grant_type=password"
headers = {
    "apikey": key,
    "Content-Type": "application/json"
}
data = {
    "email": "benja11tobar@gmail.com",
    "password": "Bjc_101926"
}

print(f"Testing login for {data['email']}...")

try:
    resp = requests.post(auth_url, headers=headers, json=data)
    if resp.status_code == 200:
        user_data = resp.json()
        print("LOGIN SUCCESS!")
        print(f"User ID: {user_data['user']['id']}")
    else:
        print(f"LOGIN FAILED: {resp.status_code}")
        print(resp.text)
except Exception as e:
    print(f"EXCEPTION: {e}")
