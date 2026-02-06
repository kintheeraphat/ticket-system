# ticket/services/erp.py
import requests

ERP_USER_URL = "http://172.17.1.55:8111/erpAPI/get_hrEmployee_user"

def call_erp_user_info(username):
    try:
        res = requests.get(
            ERP_USER_URL,
            params={"username": username},
            timeout=10
        )
    except Exception as e:
        print("ERP ERROR:", e)
        return None

    if res.status_code != 200:
        return None

    data = res.json()

    # 🔎 บาง API เป็น list ต้องหา user เอง
    if isinstance(data, list):
        for u in data:
            if u.get("user_name") == username:
                return {
                    "user_id": int(u.get("user_id")),
                    "login": u.get("user_name"),
                    "name": u.get("hr_name"),
                    "department_id": int(u.get("department_id")),
                    "department_name": u.get("department_name"),
                    "is_active": bool(u.get("hr_active")) and bool(u.get("user_active")),
                }
        return None

    # 🔎 ถ้า ERP ส่ง object เดียว
    if data.get("status") != "success":
        return None

    return {
        "user_id": data.get("user_id"),
        "login": data.get("login"),
        "name": data.get("name"),
        "department_id": data.get("department_id"),
        "department_name": data.get("department_name"),
        "is_active": data.get("hr_active") and data.get("user_active"),
    }
