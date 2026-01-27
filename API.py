import requests

url = "http://172.17.1.55:8111/erpAuth/"

payload = {
    "username": "adminsp",
    "password": "tns2025"
}

response = requests.post(url, data=payload)

print(response.status_code)
print(response.json())
