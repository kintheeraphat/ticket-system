from django.shortcuts import render, redirect
from django.db import connection
from django.utils import timezone
from django.contrib import messages
# from .auth_users import USERS
import os
from django.conf import settings



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "กรุณากรอก username และ password")
            return render(request, "login.html")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id,
                    username,
                    full_name,
                    role
                FROM tickets.users
                WHERE username = %s
                  AND password = crypt(%s, password)
                  AND is_active = true
            """, [username, password])

            user = cursor.fetchone()

        if user:
            request.session["user"] = {
                "id": user[0],
                "username": user[1],
                "full_name": user[2],
                "role": user[3],
            }
            return redirect("dashboard")

        messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    return render(request, "login.html")

# views.py
def ticket_success(request):
    return render(request, "tickets_form/ticket_success.html")


def logout_view(request):
    request.session.flush()
    return redirect("login")    

def dashboard(request):
    if "user" not in request.session:
        return redirect("login")

    return render(request, "dashboard.html")


def tickets_list(req):
    return render(req,'tickets_list.html')

def tickets_create(req):
    return render(req,'tickets_create.html')

def erp_perm(request):
    if request.method == "POST":
        user_id = request.session["user"]["id"]

        # 1️⃣ สร้าง Ticket
        title = "ขอเปิด User / ปรับสิทธิ์ ERP"
        description = request.POST.get("remark")
        ticket_type_id = 1  # ERP
        status_id = 1       # Waiting for Approve

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.tickets
                (title, description, user_id, status_id, ticket_type_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [title, description, user_id, status_id, ticket_type_id])
            ticket_id = cursor.fetchone()[0]

        # 2️⃣ บันทึก ERP Modules
        modules = request.POST.getlist("erp_module[]")
        module_name = ", ".join(modules)
        perm_change = request.POST.get("request_type") == "adjust_perm"
        module_access = True

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_erp_app
                (ticket_id, module_access, perm_change, module_name)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, [ticket_id, module_access, perm_change, module_name])
            erp_data_id = cursor.fetchone()[0]

        # 3️⃣ Upload files
        files = request.FILES.getlist("attachments[]")
        upload_dir = os.path.join(settings.BASE_DIR, f"uploads/erp/{ticket_id}")
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            file_path = os.path.join(upload_dir, f.name)
            with open(file_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.ticket_files
                    (ticket_id, ref_type, ref_id, file_name, file_path,
                     file_type, file_size, uploaded_by, create_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    ticket_id,
                    "ERP_APP",
                    erp_data_id,
                    f.name,
                    file_path,
                    f.content_type,
                    f.size,
                    user_id,
                    timezone.now()
                ])

        return redirect("ticket_success")

    return render(request, "tickets_form/erp_perm.html")
def vpn(req):
    return render(req,'tickets_form/vpn.html')

def borrows(req):
    return render(req,'tickets_form/borrows.html')

def tickets_detail(request):
    return render(request, "tickets_form/tickets_detail.html")

def repairs_form(request):
    return render(request, "tickets_form/repairs_form.html")


def adjust_form(request):
    return render(request, "tickets_form/adjust_form.html")

def app_form(request):
    return render(request, "tickets_form/app_form.html")

def report_form(request):
    return render(request, "tickets_form/report_form.html")

def active_promotion_form(request):
    return render(request, "tickets_form/active_promotion_form.html")
