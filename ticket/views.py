from django.shortcuts import render, redirect
from django.db import connection ,transaction
from django.utils import timezone
from django.contrib import messages
from django.utils.dateparse import parse_date
from datetime import timezone as dt_timezone
from datetime import date, timedelta
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import os,json
from django.http import Http404
from .decorators import login_required_custom
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import requests
from functools import wraps
from django.http import HttpResponseForbidden
from ticket.utils.approval import create_ticket_approval_by_ticket_type
from django.views.decorators.http import require_POST



ERP_API_URL = "http://172.17.1.55:8111/erpAuth/"

@csrf_exempt
def erp_auth(username, password):
    """
    ตรวจสอบ username / password กับ ERP
    คืนค่า dict ถ้าสำเร็จ
    คืน None ถ้าไม่ผ่าน
    """

    try:
        response = requests.post(
            ERP_API_URL,
            data={
                "username": username,
                "password": password
            },
            timeout=10
        )
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()

    if data.get("status") != "success":
        return None

    return data
def get_department_id(dept_name):
    if not dept_name:
        return None

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id
            FROM tickets.department
            WHERE LOWER(dept_name) = LOWER(%s)
        """, [dept_name])

        row = cursor.fetchone()
        return row[0] if row else None

def index(request):
    user = request.session.get("user")

    if not user:
        return redirect("/login/")

    role = user.get("role")
    if role in ["admin", "manager"]:
        return redirect("/dashboard/")

    return redirect("/tickets/")

def thai_date(d):
    """
    แปลง date → 'วัน/เดือน/ปี (พ.ศ.)'
    """
    if not d:
        return ""
    return d.strftime("%d/%m/") + str(d.year + 543)

def role_required_role_id(allowed_role_ids):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.session.get("user")
            if not user:
                return redirect("login")

            role_id = user.get("role_id")
            if role_id not in allowed_role_ids:
                return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าใช้งานหน้านี้")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
def login_view(request):

    # ==========================
    # ถ้า login แล้ว
    # ==========================
    user = request.session.get("user")
    if user:
        if user.get("role_id") in [1, 2]:
            return redirect("/dashboard/")
        return redirect("/tickets/")

    # ==========================
    # POST LOGIN
    # ==========================
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            return render(request, "login.html")

        # ==================================================
        # 1️⃣ LOGIN FROM DATABASE
        # ==================================================
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, full_name, role_id
                FROM tickets.users
                WHERE username = %s
                  AND password = crypt(%s, password)
                  AND is_active = TRUE
            """, [username, password])
            row = cursor.fetchone()

        if row:
            request.session["user"] = {
                "id": row[0],
                "username": row[1],
                "full_name": row[2],
                "role_id": row[3],
            }

            if row[3] in [1, 2]:
                return redirect("/dashboard/")
            return redirect("/tickets/")

        # ==================================================
        # 2️⃣ LOGIN FROM ERP
        # ==================================================
        try:
            res = requests.post(
                ERP_API_URL,
                data={"username": username, "password": password},
                timeout=10
            )
        except Exception:
            messages.error(request, "ไม่สามารถเชื่อมต่อ ERP")
            return render(request, "login.html")

        if res.status_code != 200:
            messages.error(request, "ไม่สามารถเชื่อมต่อ ERP")
            return render(request, "login.html")

        data = res.json()
        if data.get("status") != "success":
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            return render(request, "login.html")

        # ==================================================
        # 3️⃣ INSERT USER IF NOT EXISTS
        # ==================================================
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, role_id
                FROM tickets.users
                WHERE erp_user_id = %s
            """, [data["user_id"]])
            row = cursor.fetchone()

            if not row:
                cursor.execute("""
                    INSERT INTO tickets.users
                    (erp_user_id, username, full_name, role_id, is_active)
                    VALUES (%s, %s, %s, %s, TRUE)
                    RETURNING id, role_id
                """, [
                    data["user_id"],
                    data["login"],
                    data["name"],
                    3  # default = user
                ])
                row = cursor.fetchone()

        # ==================================================
        # 4️⃣ LOGIN SUCCESS
        # ==================================================
        request.session["user"] = {
            "id": row[0],
            "username": data["login"],
            "full_name": data["name"],
            "role_id": row[1],
        }

        if row[1] in [1, 2]:
            return redirect("/dashboard/")
        return redirect("/tickets/")

    return render(request, "login.html")


# def login_view(request):

#     user = request.session.get("user")

#     if user:
#         role = user.get("role")
#         if role in ["admin", "manager"]:
#             return redirect("/dashboard/")
#         return redirect("/tickets/")

#     if request.method == "POST":
#         username = request.POST.get("username", "").strip()
#         password = request.POST.get("password", "").strip()

#         if not username or not password:
#             messages.error(request, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
#             return render(request, "login.html")

#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 SELECT
#                     u.id,
#                     u.username,
#                     u.full_name,
#                     LOWER(TRIM(r.role_name)) AS role
#                 FROM tickets.users u
#                 JOIN tickets.roles r ON r.id = u.role_id
#                 WHERE u.username = %s
#                   AND u.password = crypt(%s, u.password)
#                   AND u.is_active = TRUE
#             """, [username, password])

#             row = cursor.fetchone()

#         if not row:
#             messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
#             return render(request, "login.html")

#         request.session["user"] = {
#             "id": row[0],
#             "username": row[1],
#             "full_name": row[2],
#             "role": row[3],
#         }

#         if row[3] in ["admin", "manager"]:
#             return redirect("/dashboard/")
#         return redirect("/tickets/")

#     return render(request, "login.html")


def manage_user(request):

    user = request.session.get("user")
    if not user or user["role_id"] != 1:
        raise Http404("Not allowed")

    # =====================
    # UPDATE USER
    # =====================
    if request.method == "POST":
        user_id     = request.POST.get("user_id")
        is_active   = request.POST.get("is_active") == "1"
        role_id     = request.POST.get("role_id")

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets.users
                SET is_active = %s,
                    role_id = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, [is_active, role_id, user_id])

        messages.success(request, "อัปเดตผู้ใช้งานเรียบร้อยแล้ว")
        return redirect("manage_user")

    # =====================
    # LOAD DATA
    # =====================
    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT
                u.id,
                u.erp_user_id,
                u.username      AS erp_name,
                u.is_active,
                r.id            AS role_id,
                r.name          AS role_name
            FROM tickets.users u
            LEFT JOIN tickets.roles r ON r.id = u.role_id
            ORDER BY u.id
        """)
        users = dictfetchall(cursor)

        cursor.execute("""
            SELECT id, name
            FROM tickets.roles
            ORDER BY id
        """)
        roles = dictfetchall(cursor)

    return render(request, "admin/manage_user.html", {
        "users": users,
        "roles": roles
    })

@login_required_custom
@role_required_role_id([1, 2, 3])  
def ticket_success(request):
    return render(request, "tickets_form/ticket_success.html")


def logout_view(request):
    request.session.flush()
    return redirect("login")    


@login_required_custom
@role_required_role_id([1, 2])  
def dashboard(request):

    # =====================
    # AUTH
    # =====================
    if "user" not in request.session:
        return redirect("login")

    # =====================
    # DATE FILTER
    # =====================
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date or not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)

    # 👉 แปลงวันที่เป็นข้อความไทย
    start_date_th = thai_date(start_date)
    end_date_th = thai_date(end_date)

    # =====================
    # DB QUERY
    # =====================
    with connection.cursor() as cursor:

        # ---------- COUNT BY STATUS ----------
        cursor.execute("""
            SELECT status_id, COUNT(*)
            FROM tickets.tickets
            WHERE create_at BETWEEN %s AND %s
            GROUP BY status_id
        """, [start_date, end_date])
        rows = cursor.fetchall()

        status_counts = {sid: cnt for sid, cnt in rows}

        waiting_approve = status_counts.get(1, 0)
        approved        = status_counts.get(2, 0)
        rejected        = status_counts.get(3, 0)
        in_progress     = status_counts.get(4, 0)
        completed       = status_counts.get(5, 0)

        total = sum(status_counts.values())

        # ---------- TOP CATEGORY ----------
        cursor.execute("""
            SELECT tt.name, COUNT(t.id) AS total
            FROM tickets.ticket_type tt
            LEFT JOIN tickets.tickets t
                ON t.ticket_type_id = tt.id
               AND t.create_at BETWEEN %s AND %s
            GROUP BY tt.name
            ORDER BY total DESC
            LIMIT 1
        """, [start_date, end_date])
        top1 = cursor.fetchone()

        top_category_name  = top1[0] if top1 else "-"
        top_category_count = top1[1] if top1 else 0

        # ---------- CATEGORY CHART ----------
        cursor.execute("""
            SELECT tt.name, COUNT(t.id) AS total
            FROM tickets.ticket_type tt
            LEFT JOIN tickets.tickets t
                ON t.ticket_type_id = tt.id
               AND t.create_at BETWEEN %s AND %s
            GROUP BY tt.name
            ORDER BY total DESC
        """, [start_date, end_date])
        category_rows = cursor.fetchall()

        chart_labels = [row[0] for row in category_rows]
        chart_values = [row[1] for row in category_rows]

    # =====================
    # CONTEXT
    # =====================
    context = {
        # DATE (ใช้กับ input)
        "start_date": start_date,
        "end_date": end_date,

        # DATE (แสดงผลภาษาไทย)
        "start_date_th": start_date_th,
        "end_date_th": end_date_th,

        # STATUS
        "waiting_approve": waiting_approve,
        "approved": approved,
        "rejected": rejected,
        "in_progress": in_progress,
        "completed": completed,
        "total": total,

        # CATEGORY
        "top_category_name": top_category_name,
        "top_category_count": top_category_count,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }

    return render(request, "dashboard.html", context)

@login_required_custom
@role_required_role_id([1, 2, 3])  
def tickets_list(request):

    user = request.session["user"]
    user_id = user["id"]

    search = request.GET.get("search", "")
    date_range = request.GET.get("date_range", "")

    query = """
        SELECT DISTINCT
            t.id,
            t.title,
            t.description,
            c.name        AS category,
            tt.name       AS ticket_type,
            t.ticket_type_id,
            u.username    AS requester,
            t.create_at,
            s.name        AS ticket_status,

            -- level ที่ user ต้องอนุมัติ (ถ้ามี)
            (
                SELECT tas.level
                FROM tickets.ticket_approval_status tas
                WHERE tas.ticket_id = t.id
                  AND tas.user_id = %s
                  AND tas.status_id = 7
                LIMIT 1
            ) AS approve_level,

            (
                SELECT tas.status_id
                FROM tickets.ticket_approval_status tas
                WHERE tas.ticket_id = t.id
                  AND tas.user_id = %s
                ORDER BY tas.level
                LIMIT 1
            ) AS approve_status_id

        FROM tickets.tickets t
        JOIN tickets.users u
            ON u.id = t.user_id
        JOIN tickets.ticket_type tt
            ON tt.id = t.ticket_type_id
        JOIN tickets.category c
            ON c.id = tt.category
        JOIN tickets.status s
            ON s.id = t.status_id

        WHERE
        (
            -- ผู้ร้องขอ
            t.user_id = %s

            OR

            -- ผู้ที่ถึงคิวอนุมัติ
            EXISTS (
                SELECT 1
                FROM tickets.ticket_approval_status tas
                WHERE tas.ticket_id = t.id
                  AND tas.user_id = %s
                  AND tas.status_id = 7
            )
        )
    """

    params = [
        user_id,  # approve_level
        user_id,  # approve_status_id
        user_id,  # requester
        user_id,  # approver
    ]

    if search:
        query += " AND (t.id::text ILIKE %s OR t.title ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    if date_range:
        try:
            start_str, end_str = date_range.split(" ถึง ")
            start_date = parse_date("/".join(reversed(start_str.split("/"))))
            end_date = parse_date("/".join(reversed(end_str.split("/"))))
            if start_date and end_date:
                query += " AND t.create_at::date BETWEEN %s AND %s"
                params.extend([start_date, end_date])
        except ValueError:
            pass

    query += " ORDER BY t.create_at DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    tickets_data = []
    for row in rows:
        created_at = row[7]
        if created_at and timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at)
        if created_at:
            created_at = timezone.localtime(created_at)

        tickets_data.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "category": row[3],
            "ticket_type": row[4],
            "ticket_type_id": row[5],
            "requester": row[6],
            "created_at": created_at,
            "ticket_status": row[8],

            "approve_level": row[9],
            "approve_status_id": row[10],
            "is_my_turn": (row[9] is not None),
        })

    return render(request, "tickets_list.html", {
        "tickets": tickets_data,
    })
    
@login_required_custom
@role_required_role_id([1, 2, 3])  
def tickets_create(req):
    return render(req,'tickets_create.html')

def erp_perm(request):
    if request.method == "POST":

        # -----------------------------
        # REQUEST TYPE
        # -----------------------------
        request_type = request.POST.get("request_type")

        # -----------------------------
        # DEFAULT VALUE (กัน NameError)
        # -----------------------------
        title = "คำร้อง ERP"
        ticket_type_id = 1   # default
        status_id = 1        # Waiting for Approve

        if request_type == "open_user":
            title = "ขอเปิด User ใหม่"
            ticket_type_id = 2

        elif request_type == "adjust_perm":
            title = "ปรับปรุงสิทธิ์เดิม"
            ticket_type_id = 1

        # -----------------------------
        # OTHER DATA
        # -----------------------------
        description = request.POST.get("remark", "")
        user_id = request.session["user"]["id"]
        department = request.POST.getlist("department[]")

        # -----------------------------
        # INSERT TICKET
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.tickets
                (title, description, user_id, status_id, ticket_type_id,department)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                title,
                description,
                user_id,
                status_id,
                ticket_type_id,
                department
            ])
            ticket_id = cursor.fetchone()[0]
            create_ticket_approval_by_ticket_type(
    ticket_id=ticket_id,
    ticket_type_id=ticket_type_id,
    requester_user_id=user_id
)
        # -----------------------------
        # PREPARE ERP DATA
        # -----------------------------
        module_access = True
        perm_change = (request_type == "adjust_perm")

        # รายชื่อผู้ขอ (หลายคน)
        names = request.POST.getlist("name_en[]")
        requester_names = "\n".join([n.strip() for n in names if n.strip()])

        # module ERP (หลาย module)
        modules = request.POST.getlist("erp_module[]")
        requested_modules = "\n".join([m.strip() for m in modules if m.strip()])

        # -----------------------------
        # INSERT ticket_data_erp_app
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_erp_app
                (ticket_id, module_access, perm_change,
                 requester_names, module_name)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [
                ticket_id,
                module_access,
                perm_change,
                requester_names,
                requested_modules
            ])
            erp_data_id = cursor.fetchone()[0]

        # -----------------------------
        # UPLOAD FILES → ticket_files
        # -----------------------------
        files = request.FILES.getlist("attachments[]")
        upload_dir = f"uploads/erp/{ticket_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            file_path = f"{upload_dir}/{f.name}"

            with open(file_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.ticket_files
                    (ticket_id, ref_type, ref_id,
                     file_name, file_path, file_type,
                     file_size, uploaded_by, create_at)
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
@login_required_custom
@role_required_role_id([3])  
def my_tickets(request):
    user_id = request.session["user"]["id"]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, title, create_at
            FROM tickets.tickets
            WHERE user_id = %s
            ORDER BY create_at DESC
        """, [user_id])

        rows = cursor.fetchall()

    return render(request, "tickets_history.html", {
        "tickets": rows
    })

def vpn(request):
    if request.method == "POST":

        # -----------------------------
        # BASIC TICKET INFO
        # -----------------------------
        title = "ขออนุมัติใช้งาน Virtual Private Network (VPN)"
        description = request.POST.get("reason", "")
        ticket_type_id = 3      
        status_id = 1           
        user_id = request.session["user"]["id"]

        # รวมแผนก (กรณีหลายคน → เก็บเป็น text)
        departments = request.POST.getlist("department[]")
        department_text = ", ".join([d.strip() for d in departments if d.strip()])

        # -----------------------------
        # INSERT tickets.tickets
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.tickets
                (title, description, user_id, status_id, ticket_type_id, department)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                title,
                description,
                user_id,
                status_id,
                ticket_type_id,
                department_text
            ])
            ticket_id = cursor.fetchone()[0]

        # -----------------------------
        # PREPARE VPN DATA
        # -----------------------------
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        vpn_reason = request.POST.get("reason", "")

        # รายชื่อผู้ใช้ VPN (หลายคน)
        names = request.POST.getlist("user_names[]")
        uservpn = "\n".join([n.strip() for n in names if n.strip()])

        # -----------------------------
        # INSERT ticket_data_vpn
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_vpn
                (ticket_id, start_date, end_date, vpn_reason, uservpn)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [
                ticket_id,
                start_date,
                end_date,
                vpn_reason,
                uservpn
            ])
            vpn_data_id = cursor.fetchone()[0]
            create_ticket_approval_by_ticket_type(
    ticket_id=ticket_id,
    ticket_type_id=ticket_type_id,
    requester_user_id=user_id
)

        # -----------------------------
        # UPLOAD FILES
        # -----------------------------
        files = request.FILES.getlist("order_file[]")
        upload_dir = f"media/uploads/vpn/{ticket_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            file_path = f"{upload_dir}/{f.name}"

            with open(file_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.ticket_files
                    (ticket_id, ref_type, ref_id,
                     file_name, file_path, file_type,
                     file_size, uploaded_by, create_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    ticket_id,
                    "VPN",
                    vpn_data_id,
                    f.name,
                    file_path,
                    f.content_type,
                    f.size,
                    user_id,
                    timezone.now()
                ])

        return redirect("ticket_success")

    return render(request, "tickets_form/vpn.html")

def borrows(req):
    return render(req,'tickets_form/borrows.html')

def dictfetchone(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))
APPROVE_PENDING = 7

def tickets_detail_erp(request, ticket_id):

    user_id = request.session["user"]["id"]

    # -----------------------------
    # ticket หลัก
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT t.id, t.title, t.description,
                   u.username, t.create_at
            FROM tickets.tickets t
            JOIN tickets.users u ON u.id = t.user_id
            WHERE t.id = %s
        """, [ticket_id])

        row = cursor.fetchone()

    ticket = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "user_name": row[3],
        "create_at": row[4],
    }

    # -----------------------------
    # เช็คว่าอยู่ในสายอนุมัติไหม (level ≥ 1)
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT level, status_id
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
              AND user_id = %s
            LIMIT 1
        """, [ticket_id, user_id])

        approval_row = cursor.fetchone()

    is_in_approval_flow = approval_row is not None
    can_approve = False
    my_level = None

    if approval_row:
        my_level = approval_row[0]
        can_approve = (approval_row[1] == APPROVE_PENDING)

    return render(request, "tickets_form/tickets_detail_erp.html", {
        "ticket": ticket,
        "is_in_approval_flow": is_in_approval_flow,
        "can_approve": can_approve,
        "my_level": my_level,
    })

def tickets_detail_vpn(request, ticket_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id            AS ticket_id,
                t.title,
                t.description,
                t.create_at     AS ticket_create_at,
                u.full_name,
                t.department,
                t.ticket_type_id,
                v.uservpn,
                v.vpn_reason
            FROM tickets.ticket_data_vpn v
            JOIN tickets.tickets t ON t.id = v.ticket_id
            JOIN tickets.users u on u.id = t.user_id 
            where t.id = %s 
        
        """, [ticket_id])

        data = dictfetchone(cursor)

        if not data:
            raise Http404("VPN Ticket not found")

    # -----------------------------
    # แยก uservpn (ขึ้นบรรทัด)
    # -----------------------------
    vpn_user_list = []
    if data.get("uservpn"):
        vpn_user_list = [
            u.strip()
            for u in data["uservpn"].splitlines()
            if u.strip()
        ]

    # -----------------------------
    # แยก department (คั่นด้วย ,)
    # -----------------------------
    department_list = []
    if data.get("department"):
        department_list = [
            d.strip()
            for d in data["department"].split(",")
            if d.strip()
        ]

    # -----------------------------
    # จับคู่ user + department
    # -----------------------------
    vpn_users_with_department = []
    for i, name in enumerate(vpn_user_list):
        dept = department_list[i] if i < len(department_list) else ""
        vpn_users_with_department.append({
            "name": name,
            "department": dept
        })

    return render(request, "tickets_form/tickets_detail_vpn.html", {
        "ticket": {
            "id": data["ticket_id"],
            "title": data["title"],
            "description": data["description"],
            "create_at": data["ticket_create_at"],
            "user_name": data["full_name"],
            "ticket_type_id": data["ticket_type_id"],
        },
        "detail": {
            "vpn_users": vpn_users_with_department,
            "vpn_reason": data["vpn_reason"],
        }
    })

def tickets_detail_repairs(request, ticket_id):
    query = """
        SELECT
            t.id,
            t.title,
            t.description,
            t.create_at,
            u.full_name,
            b.department,
            t.ticket_type_id,
            b.problem_detail,
            b.building
        FROM tickets.ticket_data_building_repair b
        JOIN tickets.tickets t ON t.id = b.ticket_id
        JOIN tickets.users u ON u.erp_user_id = t.user_id
        WHERE t.id = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [ticket_id])
        row = cursor.fetchone()

    if not row:
        return render(request, "404.html", status=404)

    created_at = row[3]
    if created_at and timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at, dt_timezone.utc)
    created_at = timezone.localtime(created_at)

    detail = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "created_at": created_at,
        "full_name": row[4],
        "department": row[5],
        "ticket_type_id": row[6],
        "problem_detail": row[7],
        "building": row[8],
    }

    return render(request, "tickets_form/tickets_detail_repairs.html", {
        "detail": detail
    })
    
@login_required_custom
@role_required_role_id([1, 2, 3])  
def tickets_detail_report(request, ticket_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id            AS ticket_id,
                t.title,
                t.description,
                t.create_at     AS ticket_create_at,
                COALESCE(u.full_name, '-') AS full_name,
                t.department,
                t.ticket_type_id,
                e.old_value,
                e.new_value
            FROM tickets.ticket_data_erp_app e
            JOIN tickets.tickets t 
                ON t.id = e.ticket_id
            LEFT JOIN tickets.users u 
                ON u.id = t.user_id      -- ✅ แก้ตรงนี้
            WHERE e.report_access IS TRUE
              AND t.id = %s
            ORDER BY e.id DESC
            LIMIT 1
        """, [ticket_id])

        data = dictfetchone(cursor)

        if not data:
            raise Http404("Report ticket not found")

    created_at = data["ticket_create_at"]
    if created_at and timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at, dt_timezone.utc)
    created_at = timezone.localtime(created_at)

    return render(
        request,
        "tickets_form/tickets_detail_report.html",
        {
            "ticket": {
                "id": data["ticket_id"],
                "title": data["title"],
                "description": data["description"],
                "create_at": created_at,
                "user_name": data["full_name"],
                "department": data["department"],
            },
            "detail": {
                "old_value": data["old_value"],
                "new_value": data["new_value"],
            }
        }
    )
def tickets_detail_newapp(request, ticket_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id            AS ticket_id,
                t.title,
                t.description,
                t.create_at     AS ticket_create_at,
                u.full_name,
                t.department,
                t.ticket_type_id,
                n.new_value 
            FROM tickets.ticket_data_erp_app n
            JOIN tickets.tickets t ON t.id = n.ticket_id
            JOIN tickets.users u ON u.erp_user_id = t.user_id
            WHERE t.id = %s
        """, [ticket_id])

        data = dictfetchone(cursor)

        if not data:
            raise Http404("New App ticket not found")

    # timezone
    created_at = data["ticket_create_at"]
    if created_at and timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at, dt_timezone.utc)
    created_at = timezone.localtime(created_at)

    return render(request, "tickets_form/tickets_detail_newapp.html", {
        "ticket": {
            "id": data["ticket_id"],
            "title": data["title"],
            "description": data["description"],
            "create_at": created_at,
            "user_name": data["full_name"],
            "department": data["department"],
        },
        "detail": {
            "new_value": data["new_value"],
        }
    })
    
    
    
def repairs_form(request):
    if request.method == "POST":

        # -----------------------------
        # BASIC TICKET INFO
        # -----------------------------
        title = "แจ้งซ่อมอาคาร"
        description = request.POST.get("problem_detail")
        user_id = request.session["user"]["id"]

        status_id = 1        # Waiting
        ticket_type_id = 4   # Building Repair

        department = request.POST.get("department")
        building = request.POST.get("building")

        # กัน error กรณีฟอร์มไม่ครบ
        if not department or not building:
            return render(request, "tickets_form/repairs_form.html", {
                "error": "กรุณากรอกข้อมูลให้ครบถ้วน"
            })

        # -----------------------------
        # INSERT tickets.tickets
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.tickets
                (title, description, user_id, status_id, ticket_type_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [
                title,
                description,
                user_id,
                status_id,
                ticket_type_id
            ])
            ticket_id = cursor.fetchone()[0]
            create_ticket_approval_by_ticket_type(
    ticket_id=ticket_id,
    ticket_type_id=ticket_type_id,
    requester_user_id=user_id
)
        # -----------------------------
        # INSERT ticket_data_building_repair
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_building_repair
                (ticket_id, user_id, problem_detail, department, building, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                ticket_id,
                user_id,
                description,
                department,
                building,
                timezone.now()
            ])

        # -----------------------------
        # UPLOAD FILES
        # -----------------------------
        files = request.FILES.getlist("attachments[]")
        upload_dir = f"media/uploads/repairs/{ticket_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            file_path = f"{upload_dir}/{f.name}"

            with open(file_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.ticket_files
                    (ticket_id, ref_type, file_name, file_path,
                     file_type, file_size, uploaded_by, create_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    ticket_id,
                    "BUILDING_REPAIR",
                    f.name,
                    file_path,
                    f.content_type,
                    f.size,
                    user_id,
                    timezone.now()
                ])
                
        return redirect("ticket_success")
    return render(request, "tickets_form/repairs_form.html")

def active_promotion_detail(request, ticket_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                t.id                AS ticket_id,
                t.title,
                t.description,
                t.create_at         AS ticket_create_at,
                u.full_name         AS requester_name,
                tt.name             AS type,
                s.name              AS status,

                e.promo_name,
                e.start_date,
                e.end_date
            FROM tickets.tickets t
            JOIN tickets.users u ON u.id = t.user_id
            JOIN tickets.ticket_type tt ON t.ticket_type_id = tt.id
            JOIN tickets.status s ON t.status_id = s.id
            LEFT JOIN tickets.ticket_data_erp_app e
                ON e.ticket_id = t.id
            WHERE t.id = %s
        """, [ticket_id])

        data = dictfetchone(cursor)

    if not data:
        raise Http404("Active Promotion Ticket not found")

    # =============================
    # FILES
    # =============================
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                id,
                file_name,
                file_path,
                file_type,
                file_size,
                create_at
            FROM tickets.ticket_files
            WHERE ticket_id = %s
              AND ref_type = 'ACTIVE_PROMOTION'
            ORDER BY create_at
        """, [ticket_id])

        files = dictfetchall(cursor)

    return render(request, "tickets_form/active_promotion_detail.html", {
        "ticket": {
            "id": data["ticket_id"],
            "title": data["title"],
            "description": data["description"],      # ✅ ใช้ตรงนี้
            "create_at": data["ticket_create_at"],
            "user_name": data["requester_name"],
            "status": data["status"],
        },
        "promotion": {
            "promo_name": data["promo_name"],
            "start_date": data["start_date"],
            "end_date": data["end_date"],
        },
        "files": files,
    })



def adjust_form(request):
    user = request.session.get("user")
    if not user:
        return redirect("login")

    if request.method == "POST":

        # ---------------- BASIC TICKET ----------------
        title = "ปรับยอดสะสม"
        description = request.POST.get("remark", "")
        user_id = user["id"]
        status_id = 1  # Waiting
        ticket_type_id = int(request.POST.get("adj_category"))

        CATEGORY_MAP = {
            5: "ยอดยกจากเดิม",
            6: "แก้ไขยอด",
            7: "โอนระหว่างร้าน",
            8: "โอนระหว่างโปรโมชั่น",
        }
        adj_category = CATEGORY_MAP.get(ticket_type_id, "ไม่ระบุ")

        # ---------------- GET LIST ----------------
        source_cust = request.POST.getlist("source_cust[]")
        source_name = request.POST.getlist("source_customer_name[]")
        promo_info = request.POST.getlist("promo_info[]")
        earn_master = request.POST.getlist("earn_master[]")
        amount = request.POST.getlist("amount[]")

        target_cust = request.POST.getlist("target_cust[]")
        target_name = request.POST.getlist("target_customer_name[]")
        target_promo = request.POST.getlist("target_promo_name[]")
        target_earn = request.POST.getlist("target_earn_master[]")
        target_amount = request.POST.getlist("target_amount[]")

        # ---------------- BUILD ITEMS ----------------
        items = []
        for i in range(len(source_cust)):
            if not (amount[i] or target_amount[i]):
                continue

            items.append({
                "source": {
                    "cust": source_cust[i],
                    "name": source_name[i],
                    "promo": promo_info[i],
                    "earn_master": earn_master[i],
                    "amount": float(amount[i] or 0),
                },
                "target": {
                    "cust": target_cust[i],
                    "name": target_name[i],
                    "promo": target_promo[i],
                    "earn_master": target_earn[i],
                    "amount": float(target_amount[i] or 0),
                }
            })

        if not items:
            return render(request, "tickets_form/adjust_form.html", {
                "error": "กรุณากรอกอย่างน้อย 1 รายการ"
            })

        # ---------------- INSERT TICKET ----------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.tickets
                (title, description, user_id, status_id, ticket_type_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [title, description, user_id, status_id, ticket_type_id])
            ticket_id = cursor.fetchone()[0]

        # ---------------- INSERT ADJUST DATA ----------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_adjust
                (ticket_id, adj_category, items)
                VALUES (%s, %s, %s)
            """, [ticket_id, adj_category, json.dumps(items)])

        # ---------------- FILE UPLOAD ----------------
        files = request.FILES.getlist("attachments[]")
        upload_dir = f"media/uploads/adjust/{ticket_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            file_path = f"{upload_dir}/{f.name}"
            with open(file_path, "wb+") as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.ticket_files
                    (ticket_id, ref_type, file_name, file_path, file_type, file_size, uploaded_by, create_at)
                    VALUES (%s,'ADJUST',%s,%s,%s,%s,%s,%s)
                """, [
                    ticket_id,
                    f.name,
                    file_path,
                    f.content_type,
                    f.size,
                    user_id,
                    timezone.now()
                ])
                create_ticket_approval_by_ticket_type(
    ticket_id=ticket_id,
    ticket_type_id=ticket_type_id,
    requester_user_id=user_id
)
        return redirect("ticket_success")
    return render(request, "tickets_form/adjust_form.html")

def app_form(request):
    # =========================
    # CHECK LOGIN
    # =========================
    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]
    requester_name = user.get("full_name") or user.get("username", "")

    # =========================
    # POST
    # =========================
    if request.method == "POST":

        app_type = request.POST.get("app_type")           # new / update
        department = request.POST.get("department", "").strip()
        app_detail = request.POST.get("app_detail", "").strip()
        objective = request.POST.get("objective", "").strip()
        deadline_raw = request.POST.get("deadline")

        if not department:
            messages.error(request, "กรุณาระบุแผนก")
            return render(request, "tickets_form/app_form.html")

        # =========================
        # TITLE + TYPE
        # =========================
        if app_type == "new":
            title = "Request Application (New)"
            app_new = True
            app_edit = False
            ticket_type_id = 9
        elif app_type == "update":
            title = "Request Application (Update)"
            app_new = False
            app_edit = True
            ticket_type_id = 10
        else:
            messages.error(request, "ประเภทคำขอไม่ถูกต้อง")
            return render(request, "tickets_form/app_form.html")

        status_id = 1  # Waiting

        # =========================
        # DESCRIPTION
        # =========================
        # เก็บเฉพาะรายละเอียด application
        description = app_detail

        # =========================
        # DUE DATE
        # =========================
        due_date = None
        if deadline_raw:
            try:
                naive_dt = datetime.strptime(deadline_raw, "%Y-%m-%dT%H:%M")
                due_date = timezone.make_aware(
                    naive_dt,
                    timezone.get_current_timezone()
                )
            except ValueError:
                messages.error(request, "รูปแบบวันเวลาไม่ถูกต้อง")
                return render(request, "tickets_form/app_form.html")

        with connection.cursor() as cursor:

            # =========================
            # 1) INSERT tickets.tickets
            # =========================
            cursor.execute("""
                INSERT INTO tickets.tickets
                (
                    title,
                    description,
                    user_id,
                    status_id,
                    ticket_type_id,
                    department,
                    create_at,
                    due_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                title,
                description,
                user_id,          # ✅ user จริง
                status_id,
                ticket_type_id,
                department,
                timezone.now(),
                due_date
            ])

            ticket_id = cursor.fetchone()[0]
            create_ticket_approval_by_ticket_type(
    ticket_id=ticket_id,
    ticket_type_id=ticket_type_id,
    requester_user_id=user_id
)
            # =========================
            # 2) INSERT ticket_data_erp_app
            # =========================
            cursor.execute("""
                INSERT INTO tickets.ticket_data_erp_app
                (
                    ticket_id,
                    app_new,
                    app_edit,
                    old_value,
                    new_value,
                    end_date
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                ticket_id,
                app_new,
                app_edit,
                None,                 # ❌ ไม่ใช้ old_value
                objective or None,    # ✅ เก็บ objective ไว้ใน new_value
                timezone.now().date()
            ])

        messages.success(request, "ส่งคำร้อง Request Application เรียบร้อยแล้ว")
        return redirect("ticket_success")

    # =========================
    # GET
    # =========================
    return render(request, "tickets_form/app_form.html")

def report_form(request):

    # =========================
    # CHECK LOGIN
    # =========================
    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]
    requester_name = user.get("full_name") or user.get("username", "")

    # =========================
    # POST
    # =========================
    if request.method == "POST":

        department = request.POST.get("department", "").strip()
        report_detail = request.POST.get("report_detail", "").strip()
        report_objective = request.POST.get("report_objective", "").strip()
        report_fields = request.POST.get("report_fields", "").strip()

        if not department:
            messages.error(request, "กรุณาระบุแผนก")
            return render(request, "tickets_form/report_form.html")

        # =========================
        # BASIC TICKET INFO
        # =========================
        title = "Request Report / ERP Data"
        status_id = 1        # Waiting
        ticket_type_id = 11  # Report

        # description เก็บเฉพาะ report_detail
        description = report_detail

        with connection.cursor() as cursor:

            # =========================
            # 1) INSERT tickets.tickets
            # =========================
            cursor.execute("""
                INSERT INTO tickets.tickets
                (
                    title,
                    description,
                    user_id,
                    status_id,
                    ticket_type_id,
                    department,
                    create_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                title,
                description,
                user_id,
                status_id,
                ticket_type_id,
                department,
                timezone.now()
            ])

            ticket_id = cursor.fetchone()[0]

            # =========================
            # 2) INSERT ticket_data_erp_app
            # =========================
            cursor.execute("""
                INSERT INTO tickets.ticket_data_erp_app
                (
                    ticket_id,
                    report_access,
                    old_value,
                    new_value,
                    target_date
                )
                VALUES (%s, %s, %s, %s, %s)
            """, [
                ticket_id,
                True,                       # report_access
                report_fields or None,      # old_value
                report_detail or None,      # new_value
                timezone.now().date()
            ])
            create_ticket_approval_by_ticket_type(
    ticket_id=ticket_id,
    ticket_type_id=ticket_type_id,
    requester_user_id=user_id
)

        messages.success(request, "ส่งคำร้องขอรายงานเรียบร้อยแล้ว")
        return redirect("ticket_success")

    # =========================
    # GET
    # =========================
    return render(request, "tickets_form/report_form.html")

def active_promotion_form(request):

    # =====================
    # CHECK LOGIN
    # =====================
    if "user" not in request.session:
        return redirect("login")

    user_id = request.session["user"]["id"]

    # =====================
    # SUBMIT FORM
    # =====================
    if request.method == "POST":

        promo_name  = request.POST.get("promo_name", "").strip()
        start_raw   = request.POST.get("start_date")
        end_raw     = request.POST.get("end_date")
        department = request.POST.get("department", "").strip()
        reason     = request.POST.get("reason", "").strip()

        if not all([promo_name, start_raw, end_raw, department, reason]):
            messages.error(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
            return render(request, "tickets_form/active_promotion_form.html")

        # =====================
        # PARSE DATE (d/m/Y)
        # =====================
        try:
            start_date = datetime.strptime(start_raw, "%d/%m/%Y").date()
            end_date   = datetime.strptime(end_raw, "%d/%m/%Y").date()
        except ValueError:
            messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง")
            return render(request, "tickets_form/active_promotion_form.html")

        # =====================
        # PREPARE TICKET
        # =====================
        title = "Active Promotion Package"
        description = f"""
Promotion: {promo_name}
แผนก: {department}
ช่วงเวลา: {start_raw} - {end_raw}

เหตุผล:
{reason}
""".strip()

        status_id = 1
        ticket_type_id = 12   # Active Promotion

        # =====================
        # INSERT tickets
        # =====================
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_erp_app
                (
                    ticket_id,
                    promo_name,
                    start_date,
                    end_date,
                    department,
                    reason
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                ticket_id,
                promo_name,
                start_date,
                end_date,
                department,
                reason
            ])

            ticket_id = cursor.fetchone()[0]
        # =====================
        # INSERT ticket_data_erp_app
        # =====================
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_erp_app
                (
                    ticket_id,
                    promo_name,
                    start_date,
                    end_date
                )
                VALUES (%s, %s, %s, %s)
            """, [
                ticket_id,
                promo_name,
                start_date,
                end_date
            ])

        # =====================
        # SAVE FILES (FIXED)
        # =====================
        files = request.FILES.getlist("files")

        # path สำหรับเก็บไฟล์จริง
        upload_dir = os.path.join(
            settings.MEDIA_ROOT,
            "tickets",
            str(ticket_id)
        )
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            real_path = os.path.join(upload_dir, f.name)

            with open(real_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

            # path สำหรับเก็บลง DB (relative only)
            db_file_path = f"tickets/{ticket_id}/{f.name}"

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.ticket_files
                    (
                        ticket_id,
                        ref_type,
                        file_name,
                        file_path,
                        file_type,
                        file_size,
                        uploaded_by,
                        create_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    ticket_id,
                    "ACTIVE_PROMOTION",
                    f.name,
                    db_file_path,
                    f.content_type,
                    f.size,
                    user_id,              # users.id (ไม่มี FK แล้ว)
                    timezone.now()
                ])
                create_ticket_approval_by_ticket_type(
        ticket_id=ticket_id,
        ticket_type_id=ticket_type_id,
        requester_user_id=user_id
    )
        messages.success(request, "ส่งคำร้อง Active Promotion เรียบร้อยแล้ว")
        return redirect("ticket_success")

    # =====================
    # LOAD PAGE
    # =====================
    return render(request, "tickets_form/active_promotion_form.html")

    

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]



def setting_team(request):

    user = request.session.get("user")
    if not user:
        return redirect("login")

    user_id = user["id"]
    role_id = user["role_id"]

    # =========================
    # GET DATA
    # =========================
    with connection.cursor() as cursor:

        # -------- departments --------
        cursor.execute("""
            SELECT id, dept_name
            FROM tickets.department
            ORDER BY dept_name
        """)
        departments = dictfetchall(cursor)

        # -------- teams --------
        if role_id in [1, 2]:  # admin
            cursor.execute("""
                SELECT
                    t.id,
                    t.name AS team_name,
                    d.dept_name,
                    t.department_id,
                    (
                        SELECT COUNT(*)
                        FROM tickets.team_members tm
                        WHERE tm.team_id = t.id
                    ) AS member_count
                FROM tickets.team t
                LEFT JOIN tickets.department d ON d.id = t.department_id
                ORDER BY d.dept_name, t.name
            """)
        else:  # user → เห็นเฉพาะทีมที่ตัวเองอยู่
            cursor.execute("""
                SELECT DISTINCT
                    t.id,
                    t.name AS team_name,
                    d.dept_name,
                    t.department_id,
                    (
                        SELECT COUNT(*)
                        FROM tickets.team_members tm
                        WHERE tm.team_id = t.id
                    ) AS member_count
                FROM tickets.team t
                JOIN tickets.team_members tm ON tm.team_id = t.id
                LEFT JOIN tickets.department d ON d.id = t.department_id
                WHERE tm.user_id = %s
                ORDER BY d.dept_name, t.name
            """, [user_id])

        teams = dictfetchall(cursor)

        # =========================
        # CREATE TEAM (admin + user)
        # =========================
        if request.method == "POST" and request.POST.get("action") == "create":

            team_name = request.POST.get("team_name")
            department_id = request.POST.get("department_id")

            if not team_name or not department_id:
                messages.error(request, "กรุณากรอกข้อมูลให้ครบ")
                return redirect("setting_team")

            with connection.cursor() as cursor:

                # 1️⃣ สร้างทีม
                cursor.execute("""
                    INSERT INTO tickets.team (name, department_id)
                    VALUES (%s, %s)
                    RETURNING id
                """, [team_name, department_id])

                team_id = cursor.fetchone()[0]

                # 2️⃣ ใส่คนสร้างเป็นสมาชิกทีมทันที
                cursor.execute("""
                    INSERT INTO tickets.team_members (team_id, user_id)
                    VALUES (%s, %s)
                """, [team_id, user_id])

            messages.success(request, "สร้างทีมเรียบร้อยแล้ว")
            return redirect("setting_team")


    # =========================
    # UPDATE TEAM
    # =========================
    if request.method == "POST" and request.POST.get("action") == "update":

        team_id = request.POST.get("team_id")
        team_name = request.POST.get("team_name")
        department_id = request.POST.get("department_id")

        with connection.cursor() as cursor:

            if role_id in [1, 2]:  # admin แก้ได้ทุกทีม
                cursor.execute("""
                    UPDATE tickets.team
                    SET name = %s,
                        department_id = %s
                    WHERE id = %s
                """, [team_name, department_id, team_id])
            else:  # user → แก้ได้เฉพาะทีมที่ตัวเองอยู่
                cursor.execute("""
                    UPDATE tickets.team
                    SET name = %s,
                        department_id = %s
                    WHERE id = %s
                      AND EXISTS (
                          SELECT 1
                          FROM tickets.team_members
                          WHERE team_id = %s
                            AND user_id = %s
                      )
                """, [team_name, department_id, team_id, team_id, user_id])

        messages.success(request, "อัปเดตทีมเรียบร้อยแล้ว")
        return redirect("setting_team")

    # =========================
    # DELETE TEAM
    # =========================
    if request.method == "POST" and request.POST.get("action") == "delete":

        team_id = request.POST.get("team_id")

        with connection.cursor() as cursor:

            if role_id in [1, 2]:  # admin
                cursor.execute("""
                    DELETE FROM tickets.team_members
                    WHERE team_id = %s
                """, [team_id])

                cursor.execute("""
                    DELETE FROM tickets.team
                    WHERE id = %s
                """, [team_id])
            else:  # user → ลบได้เฉพาะทีมที่ตัวเองอยู่
                cursor.execute("""
                    DELETE FROM tickets.team
                    WHERE id = %s
                      AND EXISTS (
                          SELECT 1
                          FROM tickets.team_members
                          WHERE team_id = %s
                            AND user_id = %s
                      )
                """, [team_id, team_id, user_id])

        messages.success(request, "ลบทีมเรียบร้อยแล้ว")
        return redirect("setting_team")

    return render(request, "setting_team.html", {
        "departments": departments,
        "teams": teams
    })

def team_adduser(request, team_id):

    with connection.cursor() as cursor:

        # team info
        cursor.execute("""
            SELECT
                t.id,
                t.name AS team_name,
                d.dept_name,
                u1.full_name AS approver_lv1,
                u2.full_name AS approver_lv2
            FROM tickets.team t
            LEFT JOIN tickets.department d ON d.id = t.department_id
            LEFT JOIN tickets.users u1 ON u1.id = t.approver_lv1
            LEFT JOIN tickets.users u2 ON u2.id = t.approver_lv2
            WHERE t.id = %s
        """, [team_id])

        row = cursor.fetchone()
        if not row:
            messages.error(request, "ไม่พบทีม")
            return redirect("setting_team")

        team = {
            "id": row[0],
            "team_name": row[1],
            "dept_name": row[2],
            "approver_lv1": row[3],
            "approver_lv2": row[4],
        }

        # members
        cursor.execute("""
            SELECT
                tm.user_id,
                u.full_name,
                u.username
            FROM tickets.team_members tm
            JOIN tickets.users u ON u.id = tm.user_id
            WHERE tm.team_id = %s
            ORDER BY u.full_name
        """, [team_id])
        members = dictfetchall(cursor)

        # users not in team
        cursor.execute("""
            SELECT id, full_name, username
            FROM tickets.users
            WHERE is_active = true
              AND id NOT IN (
                SELECT user_id FROM tickets.team_members WHERE team_id = %s
              )
            ORDER BY full_name
        """, [team_id])
        users = dictfetchall(cursor)

    if request.method == "POST":
        user_id = request.POST.get("user_id")

        if not user_id:
            messages.error(request, "กรุณาเลือกผู้ใช้งาน")
            return redirect("team_adduser", team_id=team_id)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.team_members (team_id, user_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, [team_id, user_id])

        messages.success(request, "เพิ่มสมาชิกเข้าทีมเรียบร้อยแล้ว")
        return redirect("team_adduser", team_id=team_id)

    return render(request, "team_adduser.html", {
        "team": team,
        "members": members,
        "users": users
    })

def team_removeuser(request, team_id, member_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM tickets.team_members
            WHERE team_id = %s
              AND user_id = %s
        """, [team_id, member_id])

    messages.success(request, "ลบสมาชิกออกจากทีมเรียบร้อยแล้ว")
    return redirect("team_adduser", team_id=team_id)

def add_approve_line(request):

    user = request.session.get("user")
    if not user:
        return redirect("login")

    user_id = user["id"]
    role_id = user["role_id"]

    # =========================
    # SAVE APPROVE LINE
    # =========================
    if request.method == "POST":
        category_id = request.POST.get("category_id")
        team_id = request.POST.get("team_id")
        approvers = request.POST.getlist("approver[]")

        if not category_id or not team_id or not approvers:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบ")
            return redirect("add_approve_line")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(MAX(flow_no), 0) + 1
                FROM tickets.approve_line
                WHERE category_id = %s
                  AND team_id = %s
            """, [category_id, team_id])
            flow_no = cursor.fetchone()[0]

            for level, approve_user_id in enumerate(approvers, start=1):
                cursor.execute("""
                    INSERT INTO tickets.approve_line
                    (category_id, team_id, flow_no, level, user_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, [
                    category_id,
                    team_id,
                    flow_no,
                    level,
                    approve_user_id
                ])

        messages.success(request, "บันทึกสายอนุมัติเรียบร้อยแล้ว")
        return redirect("add_approve_line")

    # =========================
    # GET FLOW SUMMARY
    # =========================
    with connection.cursor() as cursor:

        # ---------- FLOW LIST ----------
        if role_id == 1:  # ADMIN
            cursor.execute("""
                SELECT
                    c.name AS category_name,
                    t.name AS team_name,
                    al.category_id,
                    al.team_id,
                    al.flow_no,
                    COUNT(*) AS total_levels
                FROM tickets.approve_line al
                JOIN tickets.category c ON c.id = al.category_id
                JOIN tickets.team t ON t.id = al.team_id
                GROUP BY c.name, t.name, al.category_id, al.team_id, al.flow_no
                ORDER BY c.name, t.name, al.flow_no
            """)

        elif role_id == 2:  # MANAGER → เฉพาะ flow ที่ตัวเองอยู่
            cursor.execute("""
                SELECT DISTINCT
                    c.name AS category_name,
                    t.name AS team_name,
                    al.category_id,
                    al.team_id,
                    al.flow_no,
                    COUNT(*) OVER (
                        PARTITION BY al.category_id, al.team_id, al.flow_no
                    ) AS total_levels
                FROM tickets.approve_line al
                JOIN tickets.category c ON c.id = al.category_id
                JOIN tickets.team t ON t.id = al.team_id
                WHERE EXISTS (
                    SELECT 1
                    FROM tickets.approve_line x
                    WHERE x.category_id = al.category_id
                      AND x.team_id = al.team_id
                      AND x.flow_no = al.flow_no
                      AND x.user_id = %s
                )
                ORDER BY c.name, t.name, al.flow_no
            """, [user_id])

        else:  # USER → เฉพาะทีมตัวเอง
            cursor.execute("""
                SELECT
                    c.name AS category_name,
                    t.name AS team_name,
                    al.category_id,
                    al.team_id,
                    al.flow_no,
                    COUNT(*) AS total_levels
                FROM tickets.approve_line al
                JOIN tickets.category c ON c.id = al.category_id
                JOIN tickets.team t ON t.id = al.team_id
                JOIN tickets.team_members tm ON tm.team_id = t.id
                WHERE tm.user_id = %s
                GROUP BY c.name, t.name, al.category_id, al.team_id, al.flow_no
                ORDER BY c.name, t.name, al.flow_no
            """, [user_id])

        flow_summary = dictfetchall(cursor)

        # ---------- FILTER / DROPDOWN ----------
        cursor.execute("SELECT id, name FROM tickets.category ORDER BY name")
        categories = dictfetchall(cursor)

        if role_id == 1:
            cursor.execute("SELECT id, name FROM tickets.team ORDER BY name")
        else:
            cursor.execute("""
                SELECT t.id, t.name
                FROM tickets.team t
                JOIN tickets.team_members tm ON tm.team_id = t.id
                WHERE tm.user_id = %s
                ORDER BY t.name
            """, [user_id])
        teams = dictfetchall(cursor)

        cursor.execute("""
            SELECT id, full_name
            FROM tickets.users
            WHERE is_active = true
            ORDER BY full_name
        """)
        users = dictfetchall(cursor)

        cursor.execute("SELECT DISTINCT name FROM tickets.category ORDER BY name")
        category_filters = dictfetchall(cursor)

    return render(request, "add_approve_line.html", {
        "flow_summary": flow_summary,
        "categories": categories,
        "teams": teams,
        "users": users,
        "category_filters": category_filters,
    })

    
def approval_flow_detail(request, category_id, team_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                al.flow_no,
                al.level,
                u.full_name,
                c.name AS category_name,
                t.name AS team_name
            FROM tickets.approve_line al
            JOIN tickets.users u ON u.id = al.user_id
            JOIN tickets.category c ON c.id = al.category_id
            JOIN tickets.team t ON t.id = al.team_id
            WHERE al.category_id = %s
              AND al.team_id = %s
            ORDER BY al.flow_no, al.level
        """, [category_id, team_id])

        flows = dictfetchall(cursor)

    if not flows:
        raise Http404("ไม่พบสายอนุมัติ")

    return render(request, "approval_flow_detail.html", {
        "flows": flows,
        "category_name": flows[0]["category_name"],
        "team_name": flows[0]["team_name"],
        "category_id": category_id,
        "team_id": team_id,
    })

# เปลี่ยนlevelของapprove line

# status ฝั่ง approve_line
APPROVE_PENDING = 7    # ถึงคิว ต้องกด approve
APPROVE_WAITING = 6    # รอ (ยังไม่ถึงคิว) / ผ่านแล้ว

# status ฝั่งเอกสาร (tickets)
DOC_WAITING_APPROVE = 1
DOC_IN_PROGRESS = 4
DOC_COMPLETED = 5


# ==================================================
# CREATE APPROVAL FLOW
# ==================================================

def create_ticket_approval_by_ticket_type(
    *,
    ticket_id: int,
    ticket_type_id: int,
    requester_user_id: int,
    flow_no: int = 1
):
    """
    สร้าง ticket_approval_status จาก approve_line

    - category มาจาก ticket_type
    - team มาจาก team ที่ requester อยู่
    - รองรับ user อยู่หลาย team
    """

    with connection.cursor() as cursor:

        # ---------------------------------------------
        # 1) ดึง category ของ ticket_type
        # ---------------------------------------------
        cursor.execute("""
            SELECT category
            FROM tickets.ticket_type
            WHERE id = %s
        """, [ticket_type_id])

        row = cursor.fetchone()
        if not row:
            raise Exception("ไม่พบ ticket_type")

        category_id = row[0]

        # ---------------------------------------------
        # 2) หา team ของ requester ที่มี approve_line
        # ---------------------------------------------
        cursor.execute("""
            SELECT DISTINCT tm.team_id
            FROM tickets.team_members tm
            JOIN tickets.approve_line al
              ON al.team_id = tm.team_id
             AND al.category_id = %s
             AND al.flow_no = %s
            WHERE tm.user_id = %s
            ORDER BY tm.team_id
            LIMIT 1
        """, [
            category_id,
            flow_no,
            requester_user_id
        ])

        team_row = cursor.fetchone()
        if not team_row:
            raise Exception("ไม่พบ team ที่รองรับสายอนุมัตินี้")

        team_id = team_row[0]

        # ---------------------------------------------
        # 3) หา level แรก
        # ---------------------------------------------
        cursor.execute("""
            SELECT MIN(level)
            FROM tickets.approve_line
            WHERE category_id = %s
              AND team_id = %s
              AND flow_no = %s
        """, [category_id, team_id, flow_no])

        first_level = cursor.fetchone()[0]
        if first_level is None:
            raise Exception("ไม่พบ approve_line")

        # ---------------------------------------------
        # 4) กัน insert ซ้ำ
        # ---------------------------------------------
        cursor.execute("""
            SELECT 1
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
            LIMIT 1
        """, [ticket_id])

        if cursor.fetchone():
            return

        # ---------------------------------------------
        # 5) INSERT ticket_approval_status
        # ---------------------------------------------
        cursor.execute("""
            INSERT INTO tickets.ticket_approval_status
            (
                ticket_id,
                approve_line_id,
                level,
                user_id,
                status_id
            )
            SELECT
                %s,
                al.id,
                al.level,
                al.user_id,
                CASE
                    WHEN al.level = %s THEN %s   -- Pending
                    ELSE %s                      -- Waiting
                END
            FROM tickets.approve_line al
            WHERE al.category_id = %s
              AND al.team_id = %s
              AND al.flow_no = %s
            ORDER BY al.level
        """, [
            ticket_id,
            first_level,
            APPROVE_PENDING,
            APPROVE_WAITING,
            category_id,
            team_id,
            flow_no
        ])
def approve_ticket_flow(
    *,
    ticket_id: int,
    approver_user_id: int,
    remark: str | None = None
):
    """
    ใช้กด Approve
    - ปิด level ปัจจุบัน
    - เปิด level ถัดไป
    - อัปเดต status เอกสาร
    """

    with transaction.atomic():
        with connection.cursor() as cursor:

            # ---------------------------------------------
            # 1) หา row ที่ถึงคิว approve
            # ---------------------------------------------
            cursor.execute("""
                SELECT id, level
                FROM tickets.ticket_approval_status
                WHERE ticket_id = %s
                  AND user_id = %s
                  AND status_id = %s
                FOR UPDATE
            """, [
                ticket_id,
                approver_user_id,
                APPROVE_PENDING
            ])

            row = cursor.fetchone()
            if not row:
                raise Exception("ไม่ถึงคิว approve หรือไม่มีสิทธิ์")

            tas_id, current_level = row

            # ---------------------------------------------
            # 2) ปิด level ปัจจุบัน
            # ---------------------------------------------
            cursor.execute("""
                UPDATE tickets.ticket_approval_status
                SET status_id = %s,
                    action_time = %s,
                    remark = %s
                WHERE id = %s
            """, [
                APPROVE_WAITING,
                timezone.now(),
                remark,
                tas_id
            ])

            # ---------------------------------------------
            # 3) หา level ถัดไป
            # ---------------------------------------------
            cursor.execute("""
                SELECT id
                FROM tickets.ticket_approval_status
                WHERE ticket_id = %s
                  AND level = %s
                LIMIT 1
            """, [
                ticket_id,
                current_level + 1
            ])

            next_row = cursor.fetchone()

            if next_row:
                # -----------------------------------------
                # เปิด level ถัดไป
                # -----------------------------------------
                cursor.execute("""
                    UPDATE tickets.ticket_approval_status
                    SET status_id = %s
                    WHERE id = %s
                """, [
                    APPROVE_PENDING,
                    next_row[0]
                ])

                # -----------------------------------------
                # เอกสารกำลังดำเนินการ
                # -----------------------------------------
                cursor.execute("""
                    UPDATE tickets.tickets
                    SET status_id = %s
                    WHERE id = %s
                """, [
                    DOC_IN_PROGRESS,
                    ticket_id
                ])

                return {
                    "result": "NEXT_LEVEL",
                    "level": current_level + 1
                }

            else:
                # -----------------------------------------
                # ไม่มี level ถัดไป → ปิดเอกสาร
                # -----------------------------------------
                cursor.execute("""
                    UPDATE tickets.tickets
                    SET status_id = %s
                    WHERE id = %s
                """, [
                    DOC_COMPLETED,
                    ticket_id
                ])

                return {
                    "result": "COMPLETED",
                    "final_level": current_level
                }

@require_POST
def approve_ticket(request, ticket_id):
    user_id = request.session["user"]["id"]
    remark = request.POST.get("remark", "")

    try:
        approve_ticket_flow(
            ticket_id=ticket_id,
            approver_user_id=user_id,
            remark=remark
        )
        messages.success(request, "อนุมัติเรียบร้อยแล้ว")
    except Exception as e:
        messages.error(request, str(e))

    return redirect("tickets_list")