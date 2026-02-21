import requests

url = "http://localhost:8000/"
print(f"Testing redirection for {url}...")
r = requests.get(url, allow_redirects=False)
print(f"Status: {r.status_code}")
print(f"Location: {r.headers.get('Location')}")
if r.status_code == 303 and r.headers.get('Location') == '/login':
    print("Redirection working!")
else:
    print("Redirection FAILED.")
