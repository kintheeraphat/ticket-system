# ticket/services/erp.py
import requests
from django.conf import settings

ERP_AUTH_URL = "http://172.17.55.8111/erpAuth/"  # แก้ตามของจริง

def call_erp_user_info(username):
    try:
        res = requests.post(
            ERP_AUTH_URL,
            data={
                "username": username,
                "password": "dummy"  # ERP บางที่ไม่ใช้ แต่ต้องส่ง
            },
            timeout=10
        )
    except Exception:
        return None

    if res.status_code != 200:
        return None

    data = res.json()
    if data.get("status") != "success":
        return None

    return {
        "user_id": data.get("user_id"),
        "login": data.get("login"),
        "name": data.get("name"),
    }
