import requests

url = "http://localhost:8000/login"
data = {
    "email": "admin@local",
    "password": "Admin12345!"
}

print(f"Testing login for {data['email']}...")
r = requests.post(url, data=data, allow_redirects=False)
print(f"Status: {r.status_code}")
print(f"Headers: {r.headers}")
if r.status_code == 303:
    print("Login successful (redirected)")
else:
    print(f"Login failed. Response: {r.text[:200]}")
