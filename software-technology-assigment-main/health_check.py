import requests

# Desc: Health check for the API service
response = requests.get("http://localhost:8000/")
if response.status_code == 200:
    print("API service is healthy")
else:
    print("API service is not healthy")
    exit(1)
