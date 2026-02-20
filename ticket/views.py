from datetime import date, datetime, time, timedelta
from django.shortcuts import render, redirect
from django.db import connection ,transaction
from django.utils import timezone
from django.contrib import messages
from django.utils.dateparse import parse_date
from datetime import timezone as dt_timezone
from django.views.decorators.clickjacking import xframe_options_exempt
import os,json
from django.http import Http404
from .decorators import login_required_custom
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import requests
from functools import wraps
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from ticket.services.erp import call_erp_user_info
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import calendar
from collections import Counter
from django.db import connection
from django.shortcuts import render
from django.http import HttpResponse, Http404,FileResponse
from django.utils import timezone
from django.http import HttpResponse
import xlsxwriter
from ticket.templatetags.page_permission import page_permission_required
import json
from collections import defaultdict
from django.db import connection
from django.shortcuts import render
from django.http import Http404

ERP_API_URL = "http://172.17.1.55:8111/erpAuth/"

DOC_WAITING_APPROVE = 1

class ApprovalTeamNotFound(Exception):
    pass

def handle_approval_error(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)  # เด้งกลับหน้าเดิมอัตโนมัติ
    return wrapper


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

@page_permission_required
@login_required_custom
def manage_user(request):

    session_user = request.session.get("user")

    # =====================
    # POST
    # =====================
    if request.method == "POST":

        action = request.POST.get("action")

        # ==================================================
        # ADD USER FROM ERP
        # ==================================================
        if action == "add_user_from_erp":

            erp_username = request.POST.get("erp_username", "").strip()
            role_id = request.POST.get("role_id")
            is_active = request.POST.get("is_active") == "1"

            if not erp_username:
                messages.error(request, "กรุณาระบุ ERP Username")
                return redirect("manage_user")

            erp_data = call_erp_user_info(erp_username)

            if not erp_data:
                messages.error(request, "ไม่พบผู้ใช้งานใน ERP")
                return redirect("manage_user")

            erp_login = erp_data.get("login")

            if not erp_login:
                messages.error(request, "ERP ไม่ส่งข้อมูล Username กลับมา")
                return redirect("manage_user")

            if erp_login.lower().strip() != erp_username.lower().strip():
                messages.error(
                    request,
                    f"Username ไม่ตรงกับ ERP (ERP = {erp_login})"
                )
                return redirect("manage_user")

            with connection.cursor() as cursor:

                # duplicate username
                cursor.execute("""
                    SELECT id FROM tickets.users
                    WHERE LOWER(username) = LOWER(%s)
                """, [erp_login])

                if cursor.fetchone():
                    messages.error(request, "Username นี้มีอยู่ในระบบแล้ว")
                    return redirect("manage_user")

                # duplicate ERP ID
                cursor.execute("""
                    SELECT id FROM tickets.users
                    WHERE erp_user_id = %s
                """, [erp_data["user_id"]])

                if cursor.fetchone():
                    messages.error(request, "ผู้ใช้งาน ERP นี้ถูกเพิ่มไว้แล้ว")
                    return redirect("manage_user")

                # UPSERT department
                if erp_data.get("department_id"):

                    cursor.execute("""
                        SELECT id
                        FROM tickets.department
                        WHERE id = %s
                    """, [erp_data["department_id"]])

                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO tickets.department (id, dept_name)
                            VALUES (%s, %s)
                        """, [
                            erp_data["department_id"],
                            erp_data.get("department_name")
                        ])

                # INSERT user
                cursor.execute("""
                    INSERT INTO tickets.users
                        (erp_user_id, username, full_name,
                         role_id, is_active, department_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [
                    erp_data["user_id"],
                    erp_login,
                    erp_data.get("name"),
                    role_id,
                    is_active,
                    erp_data.get("department_id")
                ])

            messages.success(request, "เพิ่มผู้ใช้งานจาก ERP เรียบร้อยแล้ว")
            return redirect("manage_user")

        # ==================================================
        # UPDATE USER
        # ==================================================
        if action == "update_user":

            user_id = request.POST.get("user_id")
            role_id = request.POST.get("role_id")
            is_active = request.POST.get("is_active") == "1"

            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE tickets.users
                    SET role_id = %s,
                        is_active = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, [role_id, is_active, user_id])

            messages.success(request, "อัปเดตผู้ใช้งานเรียบร้อยแล้ว")
            return redirect("manage_user")

    # =====================
    # GET
    # =====================
    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT
                u.id,
                u.erp_user_id,
                u.username,
                u.full_name,
                u.is_active,
                r.role_name,
                d.dept_name AS department_name
            FROM tickets.users u
            LEFT JOIN tickets.roles r
                ON r.id = u.role_id
            LEFT JOIN tickets.department d
                ON d.id = u.department_id
            ORDER BY u.id
        """)
        users = dictfetchall(cursor)

        cursor.execute("""
            SELECT id, role_name
            FROM tickets.roles
            ORDER BY id
        """)
        roles = dictfetchall(cursor)

        cursor.execute("""
            SELECT DISTINCT dept_name AS department_name
            FROM tickets.department
            ORDER BY dept_name
        """)
        departments = dictfetchall(cursor)

    return render(request, "admin/manage_user.html", {
        "users": users,
        "roles": roles,
        "departments": departments,
        "current_user_id": session_user.get("id"),
    })

@login_required_custom
@page_permission_required
def ticket_success(request):
    return render(request, "tickets_form/ticket_success.html")


def logout_view(request):
    request.session.flush()
    return redirect("login")    


@login_required_custom
@page_permission_required
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
        today = date.today()
        start_date = today.replace(day=1)   # วันที่ 1 ของเดือนปัจจุบัน
        end_date = today
    else:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)

    # แปลงวันที่เป็นภาษาไทย (สำหรับแสดงผล)
    start_date_th = thai_date(start_date)
    end_date_th = thai_date(end_date)

    # ⚠️ สำคัญ: แปลงเป็น datetime ให้ครอบคลุมทั้งวัน
    start_dt = datetime.combine(start_date, time.min)
    end_dt   = datetime.combine(end_date, time.max)

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
        """, [start_dt, end_dt])

        rows = cursor.fetchall()
        status_counts = {sid: cnt for sid, cnt in rows}

        waiting_approve = status_counts.get(1, 0)
        approved        = status_counts.get(2, 0)
        rejected        = status_counts.get(3, 0)
        in_progress     = status_counts.get(4, 0)
        completed       = status_counts.get(5, 0)
        accepting_work  = status_counts.get(8, 0)

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
        """, [start_dt, end_dt])

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
        """, [start_dt, end_dt])

        category_rows = cursor.fetchall()
        chart_labels = [row[0] for row in category_rows]
        chart_values = [row[1] for row in category_rows]

    # =====================
    # CONTEXT
    # =====================
    context = {
        # DATE (input)
        "start_date": start_date,
        "end_date": end_date,

        # DATE (display)
        "start_date_th": start_date_th,
        "end_date_th": end_date_th,

        # STATUS
        "waiting_approve": waiting_approve,
        "approved": approved,
        "rejected": rejected,
        "in_progress": in_progress,
        "accepting_work": accepting_work,
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
@page_permission_required
def tickets_list(request):

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]

    search = request.GET.get("search", "")
    date_range = request.GET.get("date_range", "")

    query = """
        SELECT
            t.id,
            t.title,
            t.description,
            c.name        AS category,
            tt.name       AS ticket_type,
            t.ticket_type_id,
            u.username    AS requester,
            t.create_at,
            s.name        AS ticket_status,
            t.user_id     AS ticket_owner_id,

            -- คนที่มีสิทธิ์กด approve ตอนนี้ (status_id = 7)
            (
                SELECT STRING_AGG(DISTINCT u2.full_name, ', ')
                FROM tickets.ticket_approval_status tas2
                JOIN tickets.users u2 ON u2.id = tas2.user_id
                WHERE tas2.ticket_id = t.id
                AND tas2.status_id = 7
            ) AS current_assignees,

            -- level ที่ user อยู่
            (
                SELECT tas.level
                FROM tickets.ticket_approval_status tas
                WHERE tas.ticket_id = t.id
                AND tas.user_id = %s
                AND tas.status_id = %s
                LIMIT 1
            ) AS approve_level,

            -- เคย approve แล้วหรือไม่
            EXISTS (
                SELECT 1
                FROM tickets.ticket_approval_status tas
                WHERE tas.ticket_id = t.id
                AND tas.user_id = %s
                AND tas.status_id = 2
            ) AS has_approved,

            -- ลบได้หรือไม่
            (
                t.user_id = %s
                AND t.status_id = %s
            ) AS can_delete

        FROM tickets.tickets t
        JOIN tickets.users u ON u.id = t.user_id
        JOIN tickets.ticket_type tt ON tt.id = t.ticket_type_id
        JOIN tickets.category c ON c.id = tt.category
        JOIN tickets.status s ON s.id = t.status_id
    """

    params = [
        user_id,            # approve_level
        APPROVE_PENDING,
        user_id,            # has_approved
        user_id,            # can_delete
        DOC_WAITING_APPROVE
    ]


    # ===============================
    # ROLE-BASED VISIBILITY
    # ===============================
    if role_id == 1:
        # ADMIN เห็นทั้งหมด
        query += " WHERE 1=1 "

    else:
        query += """
            WHERE
            (
                -- เจ้าของคำขอ
                t.user_id = %s

                OR

                -- เคย approve แล้ว (เก็บประวัติ)
                EXISTS (
                    SELECT 1
                    FROM tickets.ticket_approval_status tas
                    WHERE tas.ticket_id = t.id
                      AND tas.user_id = %s
                )
            )
        """
        params.extend([user_id, user_id])

    # ===============================
    # SEARCH
    # ===============================
    if search:
        query += " AND (t.id::text ILIKE %s OR t.title ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    # ===============================
    # DATE RANGE
    # ===============================
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

    # ===============================
    # ORDER
    # คำขอของฉันขึ้นบนสุด แล้วเรียงใหม่ → เก่า
    # ===============================
    query += """
        ORDER BY 
            (t.user_id = %s) DESC,
            t.create_at DESC
    """
    params.append(user_id)

    # ===============================
    # EXECUTE
    # ===============================
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
            "status": row[8],
            "ticket_owner_id": row[9],
            "assignee": row[10],   
        })


    return render(
        request,
        "tickets_list.html",
        {
            "tickets": tickets_data,
            "is_user": role_id != 1
        }
    )

@login_required_custom
@page_permission_required
def tickets_create(req):
    return render(req,'tickets_create.html')

@page_permission_required
@handle_approval_error
def erp_perm(request):

    if request.method == "POST":

        try:
            with transaction.atomic():

                # -----------------------------
                # REQUEST TYPE
                # -----------------------------
                request_type = request.POST.get("request_type")

                title = "คำร้อง ERP"
                ticket_type_id = 1
                status_id = 1

                if request_type == "open_user":
                    title = "ขอเปิด User ใหม่"
                    ticket_type_id = 2

                elif request_type == "adjust_perm":
                    title = "ปรับปรุงสิทธิ์เดิม"
                    ticket_type_id = 1

                description = request.POST.get("remark", "")
                user_id = request.session["user"]["id"]
                departments = request.POST.getlist("department[]")
                department = ", ".join(departments)

                # -----------------------------
                # INSERT TICKET
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
                        department
                    ])
                    ticket_id = cursor.fetchone()[0]

                # -----------------------------
                # CREATE APPROVAL
                # -----------------------------
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

                names = request.POST.getlist("name_en[]")
                requester_names = "\n".join([n.strip() for n in names if n.strip()])

                modules = request.POST.getlist("erp_module[]")
                requested_modules = "\n".join([m.strip() for m in modules if m.strip()])

                # -----------------------------
                # INSERT ERP DATA
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
                # FILE UPLOAD (STANDARD)
                # -----------------------------
                files = request.FILES.getlist("files")

                if files:

                    upload_root = os.path.join(
                        settings.MEDIA_ROOT,
                        "uploads",
                        "erp",
                        str(ticket_id)
                    )

                    os.makedirs(upload_root, exist_ok=True)

                    with connection.cursor() as cursor:
                        for f in files:

                            file_path = os.path.join(upload_root, f.name)

                            with open(file_path, "wb+") as destination:
                                for chunk in f.chunks():
                                    destination.write(chunk)

                            relative_path = f"uploads/erp/{ticket_id}/{f.name}"

                            cursor.execute("""
                                INSERT INTO tickets.ticket_files
                                (ticket_id, ref_type, ref_id,
                                file_name, file_path,
                                file_type, file_size,
                                uploaded_by, create_at)
                                VALUES (%s, %s, %s,
                                        %s, %s,
                                        %s, %s,
                                        %s, %s)
                            """, [
                                ticket_id,
                                "ERP_APP",
                                ticket_id,
                                f.name,
                                relative_path,
                                f.content_type,
                                f.size,
                                user_id,          # ✅ ตรงกับ uploaded_by
                                timezone.now()
                            ])


        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)

        messages.success(request, "สร้างคำร้องสำเร็จ")
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

@page_permission_required
@handle_approval_error
def vpn(request):

    if request.method == "POST":

        try:
            with transaction.atomic():

                # -----------------------------
                # BASIC TICKET INFO
                # -----------------------------
                title = "ขออนุมัติใช้งาน Virtual Private Network (VPN)"
                description = request.POST.get("reason", "")
                ticket_type_id = 3
                status_id = 1
                user_id = request.session["user"]["id"]

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

                # -----------------------------
                # CREATE APPROVAL (ถ้าไม่มีจะ raise)
                # -----------------------------
                create_ticket_approval_by_ticket_type(
                    ticket_id=ticket_id,
                    ticket_type_id=ticket_type_id,
                    requester_user_id=user_id
                )

                # -----------------------------
                # UPLOAD FILES
                # -----------------------------
                files = request.FILES.getlist("order_file")
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

        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)

        return redirect("ticket_success")

    return render(request, "tickets_form/vpn.html")

@page_permission_required
@handle_approval_error
def borrow(request):

    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]
    department = user.get("department", "")

    if request.method == "POST":

        try:
            with transaction.atomic():

                # -----------------------------
                # BASIC TICKET
                # -----------------------------
                title = "คำร้องขอยืมอุปกรณ์"
                description = request.POST.get("remark", "")
                ticket_type_id = 14
                status_id = 1

                with connection.cursor() as cursor:
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
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
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

                # -----------------------------
                # DATE CONVERT
                # -----------------------------
                borrow_date = datetime.strptime(
                    request.POST.get("borrow_date"),
                    "%d/%m/%Y"
                ).date()

                return_date = datetime.strptime(
                    request.POST.get("return_date"),
                    "%d/%m/%Y"
                ).date()

                # -----------------------------
                # 🔥 GET ITEMS FROM TABLE
                # -----------------------------
                item_names = request.POST.getlist("item_name[]")
                details = request.POST.getlist("details[]")
                quantities = request.POST.getlist("quantity[]")

                item_lines = []

                for i in range(len(item_names)):
                    name = item_names[i]
                    detail = details[i]
                    qty = quantities[i]

                    line = f"{i+1}. {name} ({detail}) x {qty}"
                    item_lines.append(line)

                request_item_text = "\n".join(item_lines)

                # -----------------------------
                # INSERT borrow_requests
                # -----------------------------
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.borrow_requests
                        (
                            ticket_id,
                            user_id,
                            remark,
                            request_item,
                            borrow_date,
                            return_date
                        )
                        VALUES (%s,%s,%s,%s,%s,%s)
                        RETURNING id
                    """, [
                        ticket_id,
                        user_id,
                        description,
                        request_item_text,   # 🔥 เก็บรายการตรงนี้
                        borrow_date,
                        return_date
                    ])
                    borrow_request_id = cursor.fetchone()[0]

                # -----------------------------
                # APPROVAL FLOW
                # -----------------------------
                create_ticket_approval_by_ticket_type(
                    ticket_id=ticket_id,
                    ticket_type_id=ticket_type_id,
                    requester_user_id=user_id
                )

                # -----------------------------
                # FILE UPLOAD
                # -----------------------------
                files = request.FILES.getlist("order_file[]")

                if files:

                    upload_root = os.path.join(
                        settings.MEDIA_ROOT,
                        "uploads",
                        "borrows",
                        str(ticket_id)
                    )

                    os.makedirs(upload_root, exist_ok=True)

                    with connection.cursor() as cursor:
                        for f in files:

                            file_path = os.path.join(upload_root, f.name)

                            with open(file_path, "wb+") as destination:
                                for chunk in f.chunks():
                                    destination.write(chunk)

                            relative_path = f"uploads/borrows/{ticket_id}/{f.name}"

                            cursor.execute("""
                                INSERT INTO tickets.ticket_files
                                (
                                    ticket_id,
                                    ref_type,
                                    ref_id,
                                    file_name,
                                    file_path,
                                    file_type,
                                    file_size,
                                    uploaded_by,
                                    create_at
                                )
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """, [
                                ticket_id,
                                "BORROW",
                                borrow_request_id,
                                f.name,
                                relative_path,
                                f.content_type,
                                f.size,
                                user_id,
                                timezone.now()
                            ])


            messages.success(request, "ส่งคำร้องขอยืมอุปกรณ์เรียบร้อยแล้ว")
            return redirect("ticket_success")

        except Exception as e:
            raise e

    today = timezone.localdate()

    return render(
        request,
        "tickets_form/borrows.html",
        {
            "today": today,
            "department": department,
        }
    )

def dictfetchone(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


APPROVE_PENDING = 7

@login_required_custom
@page_permission_required
def tickets_detail_erp(request, ticket_id):

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]
    is_admin = (role_id == 1)

    # -----------------------------
    # ticket
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id,
                t.title,
                t.description,
                u.username,
                t.create_at,
                s.name AS status_name,
                t.status_id
            FROM tickets.tickets t
            JOIN tickets.users u ON u.id = t.user_id
            JOIN tickets.status s ON s.id = t.status_id
            WHERE t.id = %s

        """, [ticket_id])

        row = cursor.fetchone()

    if not row:
        raise Http404("Ticket not found")

    ticket = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "user_name": row[3],
        "create_at": row[4],
        "status": row[5],      # ← ชื่อสถานะ
        "status_id": row[6],
    }


    # -----------------------------
    # current pending level
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT level
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
              AND status_id = %s   -- PENDING
            ORDER BY level
            LIMIT 1
        """, [ticket_id, APPROVE_PENDING])

        row = cursor.fetchone()

    current_level = row[0] if row else None

    # -----------------------------
    # check approver (ตามสาย)
    # -----------------------------
    can_approve = False
    my_level = None

    if current_level:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    c.id AS category_id,
                    tm.team_id
                FROM tickets.tickets t
                JOIN tickets.ticket_type tt ON tt.id = t.ticket_type_id
                JOIN tickets.category c ON c.id = tt.category
                JOIN tickets.team_members tm ON tm.user_id = t.user_id
                WHERE t.id = %s
                LIMIT 1
            """, [ticket_id])

            row = cursor.fetchone()

        if row:
            category_id, team_id = row
            flow = get_approve_line_dict_all_flows(category_id, team_id)

            if user_id in flow.get(current_level, []):
                can_approve = True
                my_level = current_level

    # -----------------------------
    # has pending approve (ADMIN)
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 1
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
            AND status_id IN (6, 7)   -- Waiting / Pending เท่านั้น
            LIMIT 1
        """, [ticket_id])

        has_pending_approve = cursor.fetchone() is not None

    # -----------------------------
    # FILES
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, file_name, file_path, file_type
            FROM tickets.ticket_files
            WHERE ticket_id = %s
            ORDER BY id
        """, [ticket_id])

        files = []

        for f in cursor.fetchall():
            files.append({
                "id": f[0],
                "file_name": f[1],
                "file_path": f[2].replace("\\", "/"),  # กัน windows path
                "file_type": f[3],
            })

    # -----------------------------
    # ERP DATA
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT module_access,
                perm_change,
                requester_names,
                module_name
            FROM tickets.ticket_data_erp_app
            WHERE ticket_id = %s
        """, [ticket_id])

        row = cursor.fetchone()

    erp_data = None
    if row:
        erp_data = {
            "module_access": row[0],
            "perm_change": row[1],
            "requester_names": row[2],
            "module_name": row[3],
        }


    return render(
        request,
        "tickets_form/tickets_detail_erp.html",
        {
            "ticket": ticket,
            "can_approve": can_approve,
            "my_level": my_level,
            "is_admin": is_admin,
            "has_pending_approve": has_pending_approve,

            # ✅ เพิ่มสองตัวนี้
            "files": files,
            "erp_data": erp_data,
        }
    )

    
@page_permission_required
def borrow_detail(request, ticket_id):

    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]

    with connection.cursor() as cursor:

        # -------------------------
        # BORROW HEADER + USER NAME
        # -------------------------
        cursor.execute("""
            SELECT 
                b.id,
                b.borrow_date,
                b.return_date,
                b.remark,
                b.request_item,
                d.dept_name,
                t.create_at,
                u.full_name,
                t.status_id
            FROM tickets.borrow_requests b
            JOIN tickets.tickets t ON t.id = b.ticket_id
            JOIN tickets.users u ON u.id = b.user_id
            LEFT JOIN tickets.department d ON d.id = u.department_id 
            WHERE b.ticket_id = %s
        """, [ticket_id])

        row = cursor.fetchone()

        if not row:
            return redirect("dashboard")

        borrow = {
            "id": row[0],
            "borrow_date": row[1],
            "return_date": row[2],
            "remark": row[3],
            "request_item": row[4],
            "department": row[5],
            "create_at": row[6],
            "full_name": row[7],
            "status_id": row[8],
        }

        # -------------------------
        # PARSE ITEMS
        # -------------------------
        items = []

        if borrow["request_item"]:
            lines = borrow["request_item"].split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if ". " in line:
                    line = line.split(". ", 1)[1]

                qty = ""
                if " x " in line:
                    parts = line.rsplit(" x ", 1)
                    line = parts[0]
                    qty = parts[1].strip()

                name = line
                spec = ""

                if "(" in line and ")" in line:
                    name = line.split("(", 1)[0].strip()
                    spec = line.split("(", 1)[1].rsplit(")", 1)[0].strip()

                items.append({
                    "name": name,
                    "spec": spec,
                    "qty": qty
                })
                
        cursor.execute("""
            SELECT id, file_name, file_path, file_type
            FROM tickets.ticket_files
            WHERE ticket_id = %s
            AND ref_type = 'BORROW'
            ORDER BY id
        """, [ticket_id])

        files = []

        for f in cursor.fetchall():
            files.append({
                "id": f[0],
                "file_name": f[1],
                "file_path": f[2].replace("\\", "/"),
                "file_type": f[3],
            })

    is_admin = (role_id == 1)

    can_approve_flag = False
    my_level = None

    if not is_admin:
        can_approve_flag, my_level = can_user_approve_ticket(
            ticket_id=ticket_id,
            user_id=user_id
        )
    else:
        can_approve_flag = True

    return render(
        request,
        "tickets_form/borrow_detail.html",
        {
            "borrow": borrow,
            "files": files,
            "items": items,
            "can_approve": can_approve_flag,
            "my_level": my_level,
            "is_admin": is_admin,
            "ticket": {"id": ticket_id, "status_id": borrow["status_id"]},
        }
    )
@login_required_custom
@page_permission_required
def tickets_detail_vpn(request, ticket_id):

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]

    is_admin = (role_id == 1)

    # -----------------------------
    # VPN + TICKET
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id                AS ticket_id,
                t.title,
                t.description,
                t.create_at,
                t.status_id,
                s.name              AS status_name,

                u.full_name,
                d.dept_name,

                v.uservpn,
                v.vpn_reason
            FROM tickets.ticket_data_vpn v
            JOIN tickets.tickets t
                ON t.id = v.ticket_id
            JOIN tickets.users u
                ON u.id = t.user_id
            JOIN tickets.status s
                ON s.id = t.status_id
            LEFT JOIN tickets.department d
                ON d.id = u.department_id
            WHERE t.id = %s
        """, [ticket_id])

        data = dictfetchone(cursor)

    if not data:
        raise Http404("VPN Ticket not found")

    # -----------------------------
    # VPN USERS (parse)
    # -----------------------------
    vpn_users = []
    if data.get("uservpn"):
        vpn_user_list = [u.strip() for u in data["uservpn"].splitlines() if u.strip()]
        for name in vpn_user_list:
            vpn_users.append({
                "name": name
            })

    # -----------------------------
    # APPROVE PERMISSION
    # -----------------------------
    can_approve = False
    my_level = None

    if not is_admin:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT level, status_id
                FROM tickets.ticket_approval_status
                WHERE ticket_id = %s
                AND user_id = %s
                LIMIT 1
            """, [ticket_id, user_id])

            row = cursor.fetchone()

        if row:
            my_level = row[0]
            can_approve = (row[1] == APPROVE_PENDING)
    else:
        can_approve = True

    # -----------------------------
    # HIDE ACTION (🔥 สำคัญ)
    # -----------------------------
    hide_action = data["status_id"] in (3, 5, 8)

    # -----------------------------
    # FILES
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                id,
                file_name,
                file_path,
                file_type
            FROM tickets.ticket_files
            WHERE ticket_id = %s
            ORDER BY id
        """, [ticket_id])

        files = dictfetchall(cursor)

    # -----------------------------
    # RENDER
    # -----------------------------
    return render(
        request,
        "tickets_form/tickets_detail_vpn.html",
        {
            "ticket": {
                "id": data["ticket_id"],
                "title": data["title"],
                "description": data["description"],
                "create_at": data["create_at"],
                "status_id": data["status_id"],
                "status_name": data["status_name"],
                "user_name": data["full_name"],
                "department": data["dept_name"],
            },
            "detail": {
                "vpn_users": vpn_users,
                "vpn_reason": data["vpn_reason"],
            },
            "files": files,
            "can_approve": can_approve,
            "my_level": my_level,
            "is_admin": is_admin,
            "hide_action": hide_action,   # 🔥 ส่งไปให้ template
        }
    )
    

@login_required_custom
@page_permission_required
def tickets_detail_repairs(request, ticket_id):

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]
    is_admin = (role_id == 1)

    # -----------------------------
    # ดึง ticket + repair detail
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id,
                t.title,
                t.description,
                t.create_at,
                u.full_name,
                t.department,
                t.ticket_type_id,
                s.name,               -- ✅ ใช้ name
                b.problem_detail,
                b.building,
                t.status_id
            FROM tickets.tickets t
            JOIN tickets.ticket_data_building_repair b
                ON t.id = b.ticket_id
            JOIN tickets.users u
                ON u.id = t.user_id
            JOIN tickets.status s
                ON s.id = t.status_id
            WHERE t.id = %s
        """, [ticket_id])

        row = cursor.fetchone()


    if not row:
        raise Http404("Ticket not found")

    ticket = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "created_at": row[3],
        "user_name": row[4],
        "department": row[5],
        "ticket_type_id": row[6],
        "status_name": row[7],   # ✅ ชื่อสถานะ
        "status_id": row[10],    # ✅ id สถานะ
    }

    detail = {
        "problem_detail": row[8],
        "building": row[9],
    }


    # -----------------------------
    # FILES
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, file_name, file_path, file_type
            FROM tickets.ticket_files
            WHERE ticket_id = %s
            ORDER BY id
        """, [ticket_id])

        files = []
        for f in cursor.fetchall():
            files.append({
                "id": f[0],
                "file_name": f[1],
                "file_path": f[2].replace("\\", "/"),
                "file_type": f[3],
            })

    # -----------------------------
    # APPROVE CHECK
    # -----------------------------
    can_approve = False
    my_level = None

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT level, status_id
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
              AND user_id = %s
            LIMIT 1
        """, [ticket_id, user_id])

        approval_row = cursor.fetchone()

    if approval_row:
        my_level = approval_row[0]
        can_approve = (approval_row[1] == APPROVE_PENDING)

    if is_admin:
        can_approve = True

    return render(
        request,
        "tickets_form/tickets_detail_repairs.html",
        {
            "ticket": ticket,
            "detail": detail,
            "files": files,
            "can_approve": can_approve,
            "my_level": my_level,
            "is_admin": is_admin,
        }
    )
    

@login_required_custom
@page_permission_required
def tickets_detail_report(request, ticket_id):

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]

    # -----------------------------
    # เช็ค admin
    # -----------------------------
    is_admin = (role_id == 1)

    # -----------------------------
    # ดึงข้อมูล report ticket
    # -----------------------------
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id            AS ticket_id,
                t.title,
                t.description,
                t.create_at     AS ticket_create_at,
                COALESCE(u.full_name, '-') AS full_name,
                d.dept_name AS department,
                t.ticket_type_id,
                t.status_id,   
                e.old_value,
                e.new_value
            FROM tickets.ticket_data_erp_app e
            JOIN tickets.tickets t 
                ON t.id = e.ticket_id
            LEFT JOIN tickets.users u 
                ON u.id = t.user_id
            LEFT JOIN tickets.department d
                ON d.id = u.department_id
            WHERE e.report_access IS TRUE
              AND t.id = %s
            ORDER BY e.id DESC
            LIMIT 1
        """, [ticket_id])

        data = dictfetchone(cursor)

    if not data:
        raise Http404("Report ticket not found")

    # -----------------------------
    # timezone
    # -----------------------------
    created_at = data["ticket_create_at"]
    if created_at and timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at, dt_timezone.utc)
    created_at = timezone.localtime(created_at)

    ticket = {
        "id": data["ticket_id"],
        "title": data["title"],
        "description": data["description"],
        "create_at": created_at,
        "user_name": data["full_name"],
        "department": data["department"],
        "ticket_type_id": data["ticket_type_id"],
        "status_id": data["status_id"],
    }

    detail = {
        "old_value": data["old_value"],
        "new_value": data["new_value"],
    }

    # -----------------------------
    # ตรวจสิทธิ์ approve (ตามสาย)
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

    can_approve = False
    my_level = None

    if approval_row:
        my_level = approval_row[0]
        can_approve = (approval_row[1] == APPROVE_PENDING)

    # -----------------------------
    # ADMIN OVERRIDE
    # -----------------------------
    if is_admin:
        can_approve = True

    return render(
        request,
        "tickets_form/tickets_detail_report.html",
        {
            "ticket": ticket,
            "detail": detail,
            "can_approve": can_approve,
            "my_level": my_level,
            "is_admin": is_admin,
        }
    )


@login_required_custom
@page_permission_required
def tickets_detail_newapp(request, ticket_id):

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]

    # -----------------------------
    # เช็ค admin
    # -----------------------------
    is_admin = (role_id == 1)

    # -----------------------------
    # ดึงข้อมูล New App
    # -----------------------------
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
                t.status_id,  
                n.new_value 
            FROM tickets.ticket_data_erp_app n
            JOIN tickets.tickets t ON t.id = n.ticket_id
            JOIN tickets.users u ON u.id = t.user_id
            WHERE t.id = %s
        """, [ticket_id])

        data = dictfetchone(cursor)

    if not data:
        raise Http404("New App ticket not found")

    # -----------------------------
    # timezone
    # -----------------------------
    created_at = data["ticket_create_at"]
    if created_at and timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at, dt_timezone.utc)
    created_at = timezone.localtime(created_at)

    ticket = {
        "id": data["ticket_id"],
        "title": data["title"],
        "description": data["description"],
        "create_at": created_at,
        "user_name": data["full_name"],
        "department": data["department"],
        "ticket_type_id": data["ticket_type_id"],
        "status_id": data["status_id"], 
    }

    detail = {
        "new_value": data["new_value"],
    }

    # -----------------------------
    # ตรวจสิทธิ์ approve (ตามสาย)
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

    can_approve = False
    my_level = None

    if approval_row:
        my_level = approval_row[0]
        can_approve = (approval_row[1] == APPROVE_PENDING)

    # -----------------------------
    # ADMIN OVERRIDE
    # -----------------------------
    if is_admin:
        can_approve = True

    return render(
        request,
        "tickets_form/tickets_detail_newapp.html",
        {
            "ticket": ticket,
            "detail": detail,
            "can_approve": can_approve,
            "my_level": my_level,
            "is_admin": is_admin,
        }
    )
    
@page_permission_required
@handle_approval_error
def repairs_form(request):

    if request.method == "POST":

        try:
            with transaction.atomic():

                # -----------------------------
                # BASIC TICKET INFO
                # -----------------------------
                title = "แจ้งซ่อมอาคาร"
                description = request.POST.get("problem_detail")
                user_id = request.session["user"]["id"]

                status_id = 1
                ticket_type_id = 4

                building = request.POST.get("building")
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

                # -----------------------------
                # INSERT detail table
                # -----------------------------
                type_id = 2  # อาคาร

                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.ticket_data_building_repair
                        (ticket_id, user_id, type_id, problem_detail, building, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [
                        ticket_id,
                        user_id,
                        type_id,
                        description,
                        building,
                        timezone.now()
                    ])

                # -----------------------------
                # CREATE APPROVAL
                # ถ้าไม่มี team จะ raise แล้ว rollback ทั้งหมด
                # -----------------------------
                create_ticket_approval_by_ticket_type(
                    ticket_id=ticket_id,
                    ticket_type_id=ticket_type_id,
                    requester_user_id=user_id
                )

                # -----------------------------
                # FILE UPLOAD (STANDARD)
                # -----------------------------
                files = request.FILES.getlist("attachments[]")

                if files:

                    upload_root = os.path.join(
                        settings.MEDIA_ROOT,
                        "uploads",
                        "repairs",
                        str(ticket_id)
                    )

                    os.makedirs(upload_root, exist_ok=True)

                    with connection.cursor() as cursor:
                        for f in files:

                            file_path = os.path.join(upload_root, f.name)

                            with open(file_path, "wb+") as destination:
                                for chunk in f.chunks():
                                    destination.write(chunk)

                            relative_path = f"uploads/repairs/{ticket_id}/{f.name}"

                            cursor.execute("""
                                INSERT INTO tickets.ticket_files
                                (ticket_id, ref_type, ref_id,
                                file_name, file_path,
                                file_type, file_size,
                                uploaded_by, create_at)
                                VALUES (%s, %s, %s,
                                        %s, %s,
                                        %s, %s,
                                        %s, %s)
                            """, [
                                ticket_id,
                                "BUILDING_REPAIR",
                                ticket_id,
                                f.name,
                                relative_path,
                                f.content_type,
                                f.size,
                                user_id,
                                timezone.now()
                            ])


        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)

        return redirect("ticket_success")

    return render(request, "tickets_form/repairs_form.html")
@login_required_custom
@page_permission_required
@handle_approval_error
def active_promotion_detail(request, ticket_id):

    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]

    is_admin = (role_id == 1)

    with connection.cursor() as cursor:

        # ================= TICKET =================
        cursor.execute("""
            SELECT
                t.id,
                t.description,
                t.create_at,
                u.full_name AS user_name,
                t.status_id,
                s.name AS status_name
            FROM tickets.tickets t
            LEFT JOIN tickets.users u ON t.user_id = u.id
            LEFT JOIN tickets.status s ON t.status_id = s.id
            WHERE t.id = %s
        """, [ticket_id])

        row = cursor.fetchone()

        if not row:
            return redirect("tickets_list")

        ticket = {
            "id": row[0],
            "description": row[1],
            "create_at": row[2],
            "user_name": row[3],
            "status_id": row[4],
            "status_name": row[5],
        }

        # ================= PROMOTION =================
        cursor.execute("""
            SELECT promo_name, start_date, end_date
            FROM tickets.ticket_data_erp_app
            WHERE ticket_id = %s
        """, [ticket_id])

        promo = cursor.fetchone()

        promotion = {
            "promo_name": promo[0],
            "start_date": promo[1],
            "end_date": promo[2],
        } if promo else None

        # ================= FILES =================
        cursor.execute("""
            SELECT id, file_name, file_path, file_type
            FROM tickets.ticket_files
            WHERE ticket_id = %s
            ORDER BY id
        """, [ticket_id])

        files = [{
            "id": f[0],
            "file_name": f[1],
            "file_path": f[2].replace("media/", ""),
            "file_type": f[3],
        } for f in cursor.fetchall()]

    # ================= APPROVAL PERMISSION =================
    can_approve = False
    my_level = None

    if not is_admin:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT level, status_id
                FROM tickets.ticket_approval_status
                WHERE ticket_id = %s
                  AND user_id = %s
                LIMIT 1
            """, [ticket_id, user_id])

            approval_row = cursor.fetchone()

        if approval_row:
            my_level = approval_row[0]
            can_approve = (approval_row[1] == APPROVE_PENDING)
    else:
        can_approve = True

    return render(
        request,
        "tickets_form/active_promotion_detail.html",
        {
            "ticket": ticket,
            "promotion": promotion,
            "files": files,
            "can_approve": can_approve,
            "my_level": my_level,
            "is_admin": is_admin,
        }
    )
@login_required_custom
@page_permission_required
@handle_approval_error
def adjust_form(request):

    user = request.session.get("user")
    if not user:
        return redirect("login")

    if request.method == "POST":

        try:
            with transaction.atomic():

                # ---------------- BASIC INFO ----------------
                title = "ปรับยอดสะสม"
                description = request.POST.get("remark", "").strip()
                user_id = user["id"]
                status_id = 1

                adj_category = request.POST.get("adj_category")

                if not adj_category:
                    messages.error(request, "กรุณาเลือกประเภทการปรับยอด")
                    return redirect(request.path)

                ticket_type_id = int(adj_category)

                CATEGORY_MAP = {
                    5: "ยอดยกจากเดิม",
                    6: "แก้ไขยอด",
                    7: "โอนระหว่างร้าน",
                    8: "โอนระหว่างโปรโมชั่น",
                }

                category_name = CATEGORY_MAP.get(ticket_type_id)

                if not category_name:
                    messages.error(request, "ประเภทไม่ถูกต้อง")
                    return redirect(request.path)
                
                # ---------------- GET SOURCE ----------------
                source_cust = request.POST.getlist("source_cust[]")
                source_name = request.POST.getlist("source_customer_name[]")
                promo_code = request.POST.getlist("promo_code[]")
                promo_name = request.POST.getlist("promo_name[]")
                earn_master = request.POST.getlist("earn_master[]")
                amount = request.POST.getlist("amount[]")

                # บังคับต้องมี 1 รายการ
                if not source_cust or not source_cust[0].strip():
                    messages.error(request, "กรุณากรอกข้อมูลต้นทางให้ครบ")
                    return redirect(request.path)
                
                items = []

                for i in range(len(source_cust)):

                    if not all([
                        source_cust[i].strip(),
                        source_name[i].strip(),
                        promo_code[i].strip(),
                        promo_name[i].strip(),
                        earn_master[i].strip(),
                        amount[i].strip()
                    ]):
                        messages.error(request, "กรุณากรอกข้อมูลต้นทางให้ครบทุกช่อง")
                        return redirect(request.path)

                    # ✅ แปลง amount เป็น float แบบปลอดภัย

                    items.append({
                        "type": "source",
                        "cust_code": source_cust[i],
                        "customer_name": source_name[i],
                        "promo_code": promo_code[i],
                        "promo_name": promo_name[i],
                        "earn_master": earn_master[i],
                        "amount": amount[i].strip()
                    })

                # ---------------- TARGET (เฉพาะโอน) ----------------
                if ticket_type_id in [7, 8]:

                    target_cust = request.POST.getlist("target_cust[]")
                    target_name = request.POST.getlist("target_customer_name[]")
                    target_promo_code = request.POST.getlist("target_promo_code[]")
                    target_promo_name = request.POST.getlist("target_promo_name[]")
                    target_earn = request.POST.getlist("target_earn_master[]")
                    target_amount = request.POST.getlist("target_amount[]")

                    if not target_cust or not target_cust[0].strip():
                        messages.error(request, "กรุณากรอกข้อมูลปลายทาง")
                        return redirect(request.path)

                    for i in range(len(target_cust)):

                        if not all([
                            target_cust[i].strip(),
                            target_name[i].strip(),
                            target_promo_code[i].strip(),
                            target_promo_name[i].strip(),
                            target_earn[i].strip(),
                            target_amount[i].strip()
                        ]):
                            messages.error(request, "กรุณากรอกข้อมูลปลายทางให้ครบทุกช่อง")
                            return redirect(request.path)

                        # ✅ แปลง target amount

                        items.append({
                            "type": "target",
                            "cust_code": target_cust[i],
                            "customer_name": target_name[i],
                            "promo_code": target_promo_code[i],
                            "promo_name": target_promo_name[i],
                            "earn_master": target_earn[i],
                            "amount": target_amount[i].strip()
                        })

                # ---------------- INSERT TICKET ----------------
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.tickets
                        (title, description, user_id, status_id, ticket_type_id, create_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, [
                        title,
                        description,
                        user_id,
                        status_id,
                        ticket_type_id,
                        timezone.now()
                    ])
                    ticket_id = cursor.fetchone()[0]

                # ---------------- INSERT ADJUST DATA ----------------
                # บันทึกหัวข้อมูลก่อน
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.ticket_data_adjust
                        (ticket_id, adj_category)
                        VALUES (%s, %s)
                        RETURNING id
                    """, [
                        ticket_id,
                        category_name
                    ])
                    adjust_id = cursor.fetchone()[0]   # ✅ ต้องอยู่ตรงนี้

                # บันทึกรายการ
                with connection.cursor() as cursor:
                    for item in items:
                        cursor.execute("""
                            INSERT INTO tickets.ticket_data_adjust_item
                            (ticket_id, item_type, cust_code, customer_name,
                            promo_code, promo_name, earn_master, amount)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        """, [
                            ticket_id,
                            item["type"],
                            item["cust_code"],
                            item["customer_name"],
                            item["promo_code"],
                            item["promo_name"],
                            item["earn_master"],
                            item["amount"]
                        ])

                # ---------------- CREATE APPROVAL ----------------
                create_ticket_approval_by_ticket_type(
                    ticket_id=ticket_id,
                    ticket_type_id=ticket_type_id,
                    requester_user_id=user_id
                )

                # ---------------- FILE UPLOAD ----------------
                files = request.FILES.getlist("attachments[]")

                if files:
                    upload_dir = os.path.join(
                        settings.MEDIA_ROOT,
                        "uploads",
                        "adjust",
                        str(ticket_id)
                    )
                    os.makedirs(upload_dir, exist_ok=True)

                    for f in files:

                        file_path = os.path.join(upload_dir, f.name)

                        with open(file_path, "wb+") as destination:
                            for chunk in f.chunks():
                                destination.write(chunk)

                        relative_path = f"uploads/adjust/{ticket_id}/{f.name}"

                        with connection.cursor() as cursor:
                            cursor.execute("""
                                INSERT INTO tickets.ticket_files
                                (
                                    ticket_id,
                                    ref_type,
                                    ref_id,
                                    file_name,
                                    file_path,
                                    file_type,
                                    file_size,
                                    uploaded_by,
                                    create_at
                                )
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """, [
                                ticket_id,
                                "ADJUST",
                                adjust_id,
                                f.name,
                                relative_path,
                                f.content_type,
                                f.size,
                                user_id,
                                timezone.now()
                            ])

                messages.success(request, "ส่งคำร้องปรับยอดเรียบร้อยแล้ว")
                return redirect("ticket_success")

        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)

        except Exception as e:
            raise e

    return render(request, "tickets_form/adjust_form.html")
@login_required_custom
@page_permission_required
def adjust_detail(request, ticket_id):

    user = request.session["user"]
    user_id = user["id"]
    role_id = user["role_id"]
    is_admin = (role_id == 1)

    # =============================
    # TICKET + ADJUST DATA
    # =============================
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id,
                t.title,
                t.description,
                t.create_at,
                u.full_name,
                s.name AS status_name,
                t.status_id,
                a.adj_category
            FROM tickets.tickets t
            JOIN tickets.users u ON u.id = t.user_id
            JOIN tickets.status s ON s.id = t.status_id
            JOIN tickets.ticket_data_adjust a ON a.ticket_id = t.id
            WHERE t.id = %s
        """, [ticket_id])

        row = cursor.fetchone()

    if not row:
        raise Http404("Ticket not found")

    ticket = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "create_at": row[3],
        "user_name": row[4],
        "status_name": row[5],
        "status_id": row[6],
        "adj_category": row[7],
    }

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT item_type, cust_code, customer_name,
                promo_code, promo_name, earn_master, amount
            FROM tickets.ticket_data_adjust_item
            WHERE ticket_id = %s
            ORDER BY id
        """, [ticket_id])

        items = []
        for r in cursor.fetchall():
            items.append({
                "type": r[0],
                "cust_code": r[1],
                "customer_name": r[2],
                "promo_code": r[3],
                "promo_name": r[4],
                "earn_master": r[5],
                "amount": r[6],
            })
    # =============================
    # FILES
    # =============================
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, file_name, file_path, file_type
            FROM tickets.ticket_files
            WHERE ticket_id = %s
            ORDER BY id
        """, [ticket_id])

        files = []
        for f in cursor.fetchall():
            files.append({
                "id": f[0],
                "file_name": f[1],
                "file_path": f[2].replace("\\", "/"),
                "file_type": f[3],
            })

    # =============================
    # APPROVE CHECK
    # =============================
    can_approve = False
    my_level = None

    can_approve, my_level = can_user_approve_ticket(ticket_id, user_id)

    if is_admin:
        can_approve = True

    return render(
        request,
        "tickets_form/adjust_detail.html",
        {
            "ticket": ticket,
            "items": items,
            "files": files,
            "can_approve": can_approve,
            "my_level": my_level,
            "is_admin": is_admin,
        }
    )
def build_adjust_items(request):
    source_cust = request.POST.getlist("source_cust[]")
    source_customer_name = request.POST.getlist("source_customer_name[]")
    promo_code = request.POST.getlist("promo_code[]")
    promo_name = request.POST.getlist("promo_name[]")
    earn_master = request.POST.getlist("earn_master[]")
    amount = request.POST.getlist("amount[]")

    target_cust = request.POST.getlist("target_cust[]")
    target_customer_name = request.POST.getlist("target_customer_name[]")
    target_promo_code = request.POST.getlist("target_promo_code[]")
    target_promo_name = request.POST.getlist("target_promo_name[]")
    target_earn_master = request.POST.getlist("target_earn_master[]")
    target_amount = request.POST.getlist("target_amount[]")

    items = []

    for i in range(len(source_cust)):
        if not source_cust[i]:
            continue

        items.append({
            "source_cust": source_cust[i],
            "source_customer_name": source_customer_name[i],
            "promo_code": promo_code[i],
            "promo_name": promo_name[i],
            "earn_master": earn_master[i],
            "amount": amount[i],
        })

    for i in range(len(target_cust)):
        if not target_cust[i]:
            continue

        items.append({
            "target_cust": target_cust[i],
            "target_customer_name": target_customer_name[i],
            "target_promo_code": target_promo_code[i],
            "target_promo_name": target_promo_name[i],
            "target_earn_master": target_earn_master[i],
            "target_amount": target_amount[i],
        })

    return items

@page_permission_required
@handle_approval_error
def app_form(request):

    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]

    if request.method == "POST":

        try:
            with transaction.atomic():

                app_type = request.POST.get("app_type")
                app_detail = request.POST.get("app_detail", "").strip()
                objective = request.POST.get("objective", "").strip()
                deadline_raw = request.POST.get("deadline")

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

                status_id = 1
                description = app_detail

                due_date = None
                if deadline_raw:
                    naive_dt = datetime.strptime(deadline_raw, "%Y-%m-%dT%H:%M")
                    due_date = timezone.make_aware(
                        naive_dt,
                        timezone.get_current_timezone()
                    )

                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.tickets
                        (title, description, user_id, status_id, ticket_type_id,
                          create_at, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, [
                        title,
                        description,
                        user_id,
                        status_id,
                        ticket_type_id,
                        timezone.now(),
                        due_date
                    ])
                    ticket_id = cursor.fetchone()[0]

                    cursor.execute("""
                        INSERT INTO tickets.ticket_data_erp_app
                        (ticket_id, app_new, app_edit,
                         old_value, new_value, end_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, [
                        ticket_id,
                        app_new,
                        app_edit,
                        None,
                        objective or None,
                        timezone.now().date()
                    ])

                create_ticket_approval_by_ticket_type(
                    ticket_id=ticket_id,
                    ticket_type_id=ticket_type_id,
                    requester_user_id=user_id
                )

        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)

        messages.success(request, "ส่งคำร้อง Request Application เรียบร้อยแล้ว")
        return redirect("ticket_success")

    return render(request, "tickets_form/app_form.html")

@page_permission_required
@handle_approval_error
def report_form(request):

    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]

    if request.method == "POST":

        try:
            with transaction.atomic():

                report_detail = request.POST.get("report_detail", "").strip()
                report_objective = request.POST.get("report_objective", "").strip()
                report_fields = request.POST.get("report_fields", "").strip()


                title = "Request Report / ERP Data"
                status_id = 1
                ticket_type_id = 11

                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.tickets
                        (title, description, user_id, status_id,
                         ticket_type_id, create_at)
                        VALUES (%s, %s, %s, %s,  %s, %s)
                        RETURNING id
                    """, [
                        title,
                        report_detail,
                        user_id,
                        status_id,
                        ticket_type_id,
                        timezone.now()
                    ])
                    ticket_id = cursor.fetchone()[0]

                    cursor.execute("""
                        INSERT INTO tickets.ticket_data_erp_app
                        (ticket_id, report_access,
                         old_value, new_value, target_date)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [
                        ticket_id,
                        True,
                        report_fields or None,
                        report_detail or None,
                        timezone.now().date()
                    ])

                create_ticket_approval_by_ticket_type(
                    ticket_id=ticket_id,
                    ticket_type_id=ticket_type_id,
                    requester_user_id=user_id
                )

        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)

        messages.success(request, "ส่งคำร้องขอรายงานเรียบร้อยแล้ว")
        return redirect("ticket_success")

    return render(request, "tickets_form/report_form.html")


# ================================
# REPORT DETAIL
# ================================

@login_required_custom
@page_permission_required
def report_detail(request, ticket_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id,
                t.title,
                t.description,
                t.department,
                u.full_name AS requester,
                t.create_at,
                s.name AS status_name
            FROM tickets.tickets t
            LEFT JOIN tickets.users u ON u.id = t.user_id
            LEFT JOIN tickets.status s ON s.id = t.status_id
            WHERE t.id = %s
        """, [ticket_id])

        report = dictfetchone(cursor)

    if not report:
        raise Http404("ไม่พบข้อมูล")

    return render(request, "report_detail.html", {
        "report": report
    })

@page_permission_required
@handle_approval_error
def active_promotion_form(request):

    if "user" not in request.session:
        return redirect("login")

    user_id = request.session["user"]["id"]

    if request.method == "POST":

        try:
            with transaction.atomic():

                promo_name = request.POST.get("promo_name", "").strip()
                start_raw = request.POST.get("start_date")
                end_raw = request.POST.get("end_date")
                reason = request.POST.get("reason", "").strip()

                start_date = datetime.strptime(start_raw, "%d/%m/%Y").date()
                end_date = datetime.strptime(end_raw, "%d/%m/%Y").date()

                title = "Active Promotion Package"
                status_id = 1
                ticket_type_id = 12

                # ================= INSERT TICKET =================
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.tickets
                        (title, description, user_id, status_id,
                         ticket_type_id,  create_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, [
                        title,
                        reason,
                        user_id,
                        status_id,
                        ticket_type_id,
                        timezone.now()
                    ])
                    ticket_id = cursor.fetchone()[0]

                    # ================= INSERT ERP DATA =================
                    cursor.execute("""
                        INSERT INTO tickets.ticket_data_erp_app
                        (ticket_id, promo_name, start_date, end_date)
                        VALUES (%s, %s, %s, %s)
                    """, [
                        ticket_id,
                        promo_name,
                        start_date,
                        end_date,
                    ])

                # ================= SAVE FILES =================
                files = request.FILES.getlist("files")

                if files:
                    upload_root = os.path.join(
                        settings.MEDIA_ROOT,
                        "uploads",
                        "active_promotion",
                        str(ticket_id)
                    )

                    os.makedirs(upload_root, exist_ok=True)

                    with connection.cursor() as cursor:
                        for f in files:

                            file_path = os.path.join(upload_root, f.name)

                            # save file
                            with open(file_path, "wb+") as destination:
                                for chunk in f.chunks():
                                    destination.write(chunk)

                            # relative path for DB
                            relative_path = os.path.join(
                                "media",
                                "uploads",
                                "active_promotion",
                                str(ticket_id),
                                f.name
                            )

                            cursor.execute("""
                                INSERT INTO tickets.ticket_files
                                (ticket_id, ref_type, ref_id,
                                 file_name, file_path,
                                 file_type, file_size, create_at)
                                VALUES (%s, %s, %s,
                                        %s, %s,
                                        %s, %s, %s)
                            """, [
                                ticket_id,
                                "ACTIVE_PROMOTION",   # ref_type
                                ticket_id,           # ref_id
                                f.name,
                                relative_path,
                                f.content_type,
                                f.size,
                                timezone.now()
                            ])

                # ================= CREATE APPROVAL =================
                create_ticket_approval_by_ticket_type(
                    ticket_id=ticket_id,
                    ticket_type_id=ticket_type_id,
                    requester_user_id=user_id
                )

        except ApprovalTeamNotFound as e:
            messages.error(request, str(e))
            return redirect(request.path)

        messages.success(request, "ส่งคำร้อง Active Promotion เรียบร้อยแล้ว")
        return redirect("ticket_success")

    return render(request, "tickets_form/active_promotion_form.html")
    

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@page_permission_required
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
    
@page_permission_required
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

@page_permission_required
def team_removeuser(request, team_id, member_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM tickets.team_members
            WHERE team_id = %s
              AND user_id = %s
        """, [team_id, member_id])

    messages.success(request, "ลบสมาชิกออกจากทีมเรียบร้อยแล้ว")
    return redirect("team_adduser", team_id=team_id)

@page_permission_required
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
            SELECT id, full_name, username
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

@page_permission_required
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

@page_permission_required
def delete_ticket(request, ticket_id):

    user = request.session.get("user")
    if not user:
        return redirect("login")

    user_id = user["id"]
    role_id = user["role_id"]

    with connection.cursor() as cursor:

        # ตรวจสอบสิทธิ์การลบ
        if role_id in [1, 2]:  # admin + manager ลบได้ทุก ticket
            cursor.execute("""
                DELETE FROM tickets.tickets
                WHERE id = %s
            """, [ticket_id])
        else:  # user → ลบได้เฉพาะ ticket ของตัวเองที่ยังไม่อนุมัติ
            cursor.execute("""
                DELETE FROM tickets.tickets
                WHERE id = %s
                  AND user_id = %s
                  AND status_id = 1  -- Waiting
            """, [ticket_id, user_id])

    messages.success(request, "ลบคำร้องเรียบร้อยแล้ว")
    return redirect("tickets_list")

def create_ticket_approval_by_ticket_type(
    *,
    ticket_id: int,
    ticket_type_id: int,
    requester_user_id: int
):
    with connection.cursor() as cursor:

        # 1) category จาก ticket_type
        cursor.execute("""
            SELECT category
            FROM tickets.ticket_type
            WHERE id = %s
        """, [ticket_type_id])
        row = cursor.fetchone()
        if not row:
            raise Exception("ไม่พบ ticket_type")
        category_id = row[0]

        # 2) team ของ requester
        cursor.execute("""
            SELECT tm.team_id
            FROM tickets.team_members tm
            JOIN tickets.approve_line al
              ON al.team_id = tm.team_id
             AND al.category_id = %s
            WHERE tm.user_id = %s
            LIMIT 1
        """, [category_id, requester_user_id])
        team_row = cursor.fetchone()
        if not team_row:
            raise ApprovalTeamNotFound(
        "ไม่พบ Team อนุมัติ กรุณาติดต่อผู้ดูแลระบบ"
    )
        team_id = team_row[0]

        # 3) หา level แรก
        cursor.execute("""
            SELECT MIN(level)
            FROM tickets.approve_line
            WHERE category_id = %s
              AND team_id = %s
        """, [category_id, team_id])
        first_level = cursor.fetchone()[0]

        # 4) INSERT ทุกคน ทุก level
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
                    WHEN al.level = %s THEN 7   -- ทุกคนใน level แรก = PENDING
                    ELSE 6                      -- level อื่น = WAITING
                END
            FROM tickets.approve_line al
            WHERE al.category_id = %s
              AND al.team_id = %s
            ORDER BY al.level
        """, [
            ticket_id,
            first_level,
            category_id,
            team_id
        ])



def get_approve_line_dict_all_flows(category_id, team_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT flow_no, level, user_id
            FROM tickets.approve_line
            WHERE category_id = %s
              AND team_id = %s
            ORDER BY flow_no, level
        """, [category_id, team_id])

        approve_lines = dictfetchall(cursor)

    flow_dict = {}
    for line in approve_lines:
        flow_no = line["flow_no"]
        level = line["level"]
        user_id = line["user_id"]

        if flow_no not in flow_dict:
            flow_dict[flow_no] = {}

        flow_dict[flow_no][level] = user_id

    return flow_dict

@require_POST
@page_permission_required
def approve_ticket(request, ticket_id):

    user = request.session.get("user")
    if not user:
        return redirect("login")

    is_admin = (user["role_id"] == 1)

    approve_ticket_flow(
        ticket_id=ticket_id,
        approver_user_id=user["id"],
        remark=request.POST.get("remark", ""),
        is_admin=is_admin
    )

    messages.success(request, "ดำเนินการเรียบร้อยแล้ว")
    return redirect("tickets_list")

@transaction.atomic
def approve_ticket_flow(
    *,
    ticket_id: int,
    approver_user_id: int,
    remark: str = "",
    is_admin: bool = False
):
    with connection.cursor() as cursor:


        if is_admin:
            cursor.execute("""
                UPDATE tickets.tickets
                SET status_id = 8   -- Accepting work
                WHERE id = %s
            """, [ticket_id])
            return

        cursor.execute("""
            SELECT level
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
              AND user_id = %s
              AND status_id = 7
            FOR UPDATE
        """, [ticket_id, approver_user_id])

        row = cursor.fetchone()
        if not row:
            raise Exception("คุณไม่มีสิทธิ์อนุมัติ")

        current_level = row[0]

        cursor.execute("""
            UPDATE tickets.ticket_approval_status
            SET status_id = 2,
                action_time = %s,
                remark = %s
            WHERE ticket_id = %s
              AND level = %s
              AND status_id = 7
        """, [
            timezone.now(),
            remark,
            ticket_id,
            current_level
        ])

        cursor.execute("""
            UPDATE tickets.ticket_approval_status
            SET status_id = 7
            WHERE ticket_id = %s
              AND level = %s
              AND status_id = 6
        """, [ticket_id, current_level + 1])

        cursor.execute("""
            SELECT 1
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
              AND status_id = 7
            LIMIT 1
        """, [ticket_id])

        if cursor.fetchone():
            cursor.execute("""
                UPDATE tickets.tickets
                SET status_id = 4   -- In Progress
                WHERE id = %s
            """, [ticket_id])
        else:
            cursor.execute("""
                UPDATE tickets.tickets
                SET status_id = 4   -- ยังไม่รับงาน
                WHERE id = %s
            """, [ticket_id])

                 
def get_approve_line_dict_all_flows(category_id, team_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT level, user_id
            FROM tickets.approve_line
            WHERE category_id = %s
              AND team_id = %s
            ORDER BY level
        """, [category_id, team_id])

        rows = cursor.fetchall()

    result = {}
    for level, user_id in rows:
        result.setdefault(level, []).append(user_id)

    return result

def can_user_approve_ticket(ticket_id, user_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT level
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
              AND user_id = %s
              AND status_id = 7  -- PENDING
            LIMIT 1
        """, [ticket_id, user_id])

        row = cursor.fetchone()

    if row:
        return True, row[0]

    return False, None

@require_POST
def admin_accept_work(request, ticket_id):
    user = request.session.get("user")
    if not user or user["role_id"] != 1:
        return redirect("login")

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tickets.tickets
            SET status_id = 8   -- Accepting work
            WHERE id = %s
        """, [ticket_id])

    messages.success(request, "รับงานเรียบร้อยแล้ว")
    return redirect("tickets_accepting_work")

@require_POST
def admin_complete_ticket(request, ticket_id):

    user = request.session.get("user")

    if not user or user.get("role_id") != 1:
        return HttpResponseForbidden("Admin only")

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tickets.tickets
            SET status_id = 5  -- Completed
            WHERE id = %s
        """, [ticket_id])

    messages.success(request, "ปิดงานเรียบร้อยแล้ว")
    return redirect("tickets_list")

#--------------หน้างานที่รับไปแล้ว--------------

@login_required_custom
@page_permission_required
def tickets_accepting_work(request):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id,
                t.title,
                t.description,
                t.create_at,
                t.status_id,
                u.username,
                tt.name AS ticket_type
            FROM tickets.tickets t
            JOIN tickets.users u ON u.id = t.user_id
            JOIN tickets.ticket_type tt ON tt.id = t.ticket_type_id
            WHERE t.status_id = 8   -- Accepting work
            ORDER BY t.create_at DESC
        """)

        tickets = dictfetchall(cursor)
        
        
        
    return render(
        request,
        "accepting_work/tickets_accepting_work.html",
        {
            "tickets": tickets
        }
    )
#--------------การจัดโมดูลสิทธิ์การดูหน้าและปุ่ม--------------
@login_required_custom
@page_permission_required
def manage_permission(request):

    selected_user_id = request.GET.get("user_id")

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT id, username
            FROM tickets.users
            ORDER BY username
        """)
        users = dictfetchall(cursor)

        cursor.execute("""
            SELECT id, code, url_name, description
            FROM tickets.permissions
            ORDER BY code
        """)
        permissions = dictfetchall(cursor)

        user_permission_ids = []

        if selected_user_id:
            cursor.execute("""
                SELECT permission_id
                FROM tickets.user_permissions
                WHERE user_id = %s
                AND allow = TRUE
            """, [selected_user_id])

            user_permission_ids = [row[0] for row in cursor.fetchall()]

    # ================= POST HANDLER =================
    if request.method == "POST":

        action = request.POST.get("action")

        # ------------------------------------------------
        # 1) SAVE USER PERMISSION
        # ------------------------------------------------
        if action == "save_user_permission":

            user_id = request.POST.get("user_id")
            selected_permissions = request.POST.getlist("permissions")

            if not user_id:
                messages.error(request, "ไม่พบ User")
                return redirect("/manage/permissions/")

            with connection.cursor() as cursor:

                cursor.execute("""
                    UPDATE tickets.user_permissions
                    SET allow = FALSE
                    WHERE user_id = %s
                """, [user_id])

                for perm_id in selected_permissions:
                    cursor.execute("""
                        INSERT INTO tickets.user_permissions
                        (user_id, permission_id, allow)
                        VALUES (%s, %s, TRUE)
                        ON CONFLICT (user_id, permission_id)
                        DO UPDATE SET allow = TRUE
                    """, [user_id, perm_id])

            messages.success(request, "บันทึกสิทธิ์เรียบร้อยแล้ว")
            return redirect(f"/manage/permissions/?user_id={user_id}")

        # ------------------------------------------------
        # 2) ADD / EDIT PERMISSION (MASTER TABLE)
        # ------------------------------------------------
        if action == "save_permission":

            perm_id = request.POST.get("perm_id")
            code = request.POST.get("code")
            url_name = request.POST.get("url_name")
            description = request.POST.get("description")

            with connection.cursor() as cursor:

                if perm_id:  # EDIT
                    cursor.execute("""
                        UPDATE tickets.permissions
                        SET code=%s, url_name=%s, description=%s
                        WHERE id=%s
                    """, [code, url_name, description, perm_id])

                    messages.success(request, "แก้ไข Permission เรียบร้อยแล้ว")

                else:  # ADD
                    cursor.execute("""
                        INSERT INTO tickets.permissions
                        (code, url_name, description)
                        VALUES (%s,%s,%s)
                    """, [code, url_name, description])

                    messages.success(request, "เพิ่ม Permission ใหม่เรียบร้อยแล้ว")

            return redirect("/manage/permissions/")

    return render(request, "admin/manage_permission.html", {
        "users": users,
        "permissions": permissions,
        "user_permission_ids": user_permission_ids,
        "selected_user_id": selected_user_id,
    })

@login_required_custom
@page_permission_required
def add_permission(request):

    if request.method == "POST":

        code = request.POST.get("code")
        url_name = request.POST.get("url_name")
        description = request.POST.get("description")

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.permissions (code, url_name, description)
                VALUES (%s, %s, %s)
            """, [code, url_name, description])

        messages.success(request, "เพิ่ม Permission เรียบร้อยแล้ว")

    return redirect("/manage/permissions/")

@login_required_custom
@page_permission_required
def edit_permission(request, perm_id):

    with connection.cursor() as cursor:

        if request.method == "POST":

            code = request.POST.get("code")
            url_name = request.POST.get("url_name")
            description = request.POST.get("description")

            cursor.execute("""
                UPDATE tickets.permissions
                SET code = %s,
                    url_name = %s,
                    description = %s
                WHERE id = %s
            """, [code, url_name, description, perm_id])

            messages.success(request, "แก้ไข Permission เรียบร้อยแล้ว")
            return redirect("/manage/permissions/")

        cursor.execute("""
            SELECT id, code, url_name, description
            FROM tickets.permissions
            WHERE id = %s
        """, [perm_id])

        perm = dictfetchone(cursor)

    return render(request, "admin/edit_permission.html", {
        "perm": perm
    })

# API สำหรับ Stocket IT ดึงรายชื่อ Admin

@require_GET
def api_admin_users(request):
    api_key = request.headers.get("X-API-KEY")

    if api_key != "passw0rd":
        return JsonResponse(
            {"error": "Unauthorized"},
            status=403
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, full_name 
                FROM tickets.users
                WHERE role_id = 1
            """)
            rows = cursor.fetchall()

        admin_list = [
            {
                "id": row[0],
                "username": row[1],
                "full_name": row[2],
            }
            for row in rows
        ]

        return JsonResponse(
            {"admins": admin_list},
            status=200
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )

@login_required_custom
@page_permission_required
def report_dashboard(request):

    today = timezone.localdate()

    selected_month = request.GET.get("month")
    selected_title = request.GET.get("title", "all")
    selected_status = request.GET.get("status", "all")

    if not selected_month:
        selected_month = today.strftime("%Y-%m")

    year, month = selected_month.split("-")

    query = """
        SELECT
            t.id,
            t.title,
            COALESCE(d.dept_name, 'ไม่ระบุ') AS department,
            u.full_name AS requester,
            t.create_at,
            s.name AS status_name,
            CASE 
                WHEN LOWER(s.name) = 'accepting work' THEN 'inprogress'
                ELSE s.name
            END AS display_status,
            (
                SELECT action_time
                FROM tickets.ticket_approval_status tas
                WHERE tas.ticket_id = t.id
                AND tas.status_id = 2
                ORDER BY action_time DESC
                LIMIT 1
            ) AS completed_at
        FROM tickets.tickets t
        LEFT JOIN tickets.users u ON u.id = t.user_id
        LEFT JOIN tickets.department d ON d.id = u.department_id
        LEFT JOIN tickets.status s ON s.id = t.status_id
        WHERE EXTRACT(YEAR FROM t.create_at) = %s
        AND EXTRACT(MONTH FROM t.create_at) = %s
    """


    params = [year, month]

    if selected_title != "all":
        query += " AND t.title = %s"
        params.append(selected_title)

    if selected_status != "all":
        query += " AND s.name = %s"
        params.append(selected_status)

    query += " ORDER BY t.create_at DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        reports = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ===== คำนวณวันดำเนินการ =====
    for r in reports:
        if r["completed_at"]:
            delta = r["completed_at"] - r["create_at"]
            r["process_days"] = delta.days
        else:
            r["process_days"] = None

    # ===== Dropdown =====
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT title FROM tickets.tickets ORDER BY title")
        titles = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT name FROM tickets.status ORDER BY name")
        statuses = [row[0] for row in cursor.fetchall()]

    # ===== Charts =====
    from collections import Counter

    status_counter = Counter(r["display_status"] for r in reports)
    title_counter = Counter(r["title"] for r in reports)
    dept_counter = Counter(r["department"] for r in reports)

    # ===== เดือนปี 2025 + ปีปัจจุบัน =====
    month_list = []
    for y in [2025, today.year]:
        for m in range(1, 13):
            month_list.append({
                "value": f"{y}-{str(m).zfill(2)}",
                "label": f"{calendar.month_name[m]} {y}"
            })

    return render(request, "report_dashboard.html", {
        "reports": reports,
        "titles": titles,
        "statuses": statuses,
        "selected_month": selected_month,
        "selected_title": selected_title,
        "selected_status": selected_status,
        "month_list": month_list,
        "chart_status_labels": json.dumps(list(status_counter.keys())),
        "chart_status_data": json.dumps(list(status_counter.values())),
        "chart_title_labels": json.dumps(list(title_counter.keys())),
        "chart_title_data": json.dumps(list(title_counter.values())),
        "chart_dept_labels": json.dumps(list(dept_counter.keys())),
        "chart_dept_data": json.dumps(list(dept_counter.values())),
    })


@login_required_custom
@page_permission_required
def report_export_excel(request):

    selected_month = request.GET.get("month")
    selected_title = request.GET.get("title", "all")
    selected_status = request.GET.get("status", "all")

    today = timezone.localdate()

    if not selected_month:
        selected_month = today.strftime("%Y-%m")

    year, month = selected_month.split("-")

    query = """
        SELECT
            t.id,
            t.title,
            COALESCE(d.dept_name, 'ไม่ระบุ') AS department,
            u.full_name,
            t.create_at,
            s.name
        FROM tickets.tickets t
        LEFT JOIN tickets.users u ON u.id = t.user_id
        LEFT JOIN tickets.department d ON d.id = u.department_id
        LEFT JOIN tickets.status s ON s.id = t.status_id
        WHERE EXTRACT(YEAR FROM t.create_at) = %s
        AND EXTRACT(MONTH FROM t.create_at) = %s
    """


    params = [year, month]

    if selected_title != "all":
        query += " AND t.title = %s"
        params.append(selected_title)

    if selected_status != "all":
        query += " AND s.name = %s"
        params.append(selected_status)

    query += " ORDER BY t.create_at DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="report.xlsx"'

    workbook = xlsxwriter.Workbook(response)
    worksheet = workbook.add_worksheet("Report")

    headers = ["ID", "Title", "Department", "Requester", "Created Date", "Status"]

    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    for row_num, row in enumerate(rows, 1):
        for col_num, value in enumerate(row):
            worksheet.write(row_num, col_num, str(value))

    workbook.close()
    return response



@page_permission_required
@handle_approval_error
def repairs_it_form(request):

    if "user" not in request.session:
        return redirect("login")

    user_id = request.session["user"]["id"]

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name 
            FROM tickets.it_category
            WHERE is_active = true
            ORDER BY name
        """)
        it_categories = cursor.fetchall()

    if request.method == "POST":

        it_category_id = request.POST.get("it_category_id")
        problem_detail = request.POST.get("problem_detail", "").strip()

        if not all([it_category_id, problem_detail]):
            messages.error(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
            return render(request, "tickets_form/repairs_it_form.html", {
                "it_categories": it_categories
            })

        with transaction.atomic():

            title = "แจ้งซ่อม IT"
            description = problem_detail
            status_id = 1
            ticket_type_id = 13
            type_id = 1  # IT

            # INSERT ticket
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.tickets
                    (title, description, user_id, status_id, ticket_type_id, create_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [
                    title,
                    description,
                    user_id,
                    status_id,
                    ticket_type_id,
                    timezone.now()
                ])
                ticket_id = cursor.fetchone()[0]

            # INSERT detail
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO tickets.ticket_data_building_repair
                    (ticket_id, user_id, type_id, it_category_id, problem_detail)
                    VALUES (%s, %s, %s, %s, %s)
                """, [
                    ticket_id,
                    user_id,
                    type_id,
                    it_category_id,
                    problem_detail
                ])

            # CREATE APPROVAL
            create_ticket_approval_by_ticket_type(
                ticket_id=ticket_id,
                ticket_type_id=ticket_type_id,
                requester_user_id=user_id
            )

            # ================= FILE UPLOAD =================
            files = request.FILES.getlist("attachments[]")

            upload_root = os.path.join(
                settings.MEDIA_ROOT,
                "uploads",
                "repairs_it",
                str(ticket_id)
            )
            os.makedirs(upload_root, exist_ok=True)

            for f in files:

                file_path = os.path.join(upload_root, f.name)

                with open(file_path, "wb+") as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)

                relative_path = f"uploads/repairs_it/{ticket_id}/{f.name}"

                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO tickets.ticket_files
                        (ticket_id, ref_type, ref_id,
                         file_name, file_path,
                         file_type, file_size,
                         uploaded_by, create_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, [
                        ticket_id,
                        "REPAIRS_IT",
                        ticket_id,
                        f.name,
                        relative_path,
                        f.content_type,
                        f.size,
                        user_id,
                        timezone.now()
                    ])

        messages.success(request, "ส่งคำร้องซ่อม IT เรียบร้อยแล้ว")
        return redirect("ticket_success")

    return render(request, "tickets_form/repairs_it_form.html", {
        "it_categories": it_categories
    })

@page_permission_required
def repairs_it_detail(request, ticket_id):

    if "user" not in request.session:
        return redirect("login")

    user = request.session["user"]
    user_id = user["id"]
    is_admin = (user["role_id"] == 1)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id,
                t.title,
                t.description,
                t.create_at,
                t.status_id,
                s.name AS status_name,
                u.username,
                d.dept_name,
                t.assign_id,
                assign_user.username AS assigned_to,
                td.it_category_id,
                ic.name AS it_category_name,
                td.problem_detail
            FROM tickets.tickets t
            JOIN tickets.users u ON u.id = t.user_id
            JOIN tickets.status s ON s.id = t.status_id
            JOIN tickets.ticket_data_building_repair td ON td.ticket_id = t.id
            LEFT JOIN tickets.it_category ic ON ic.id = td.it_category_id
            LEFT JOIN tickets.users assign_user ON assign_user.id = t.assign_id
            LEFT JOIN tickets.department d ON d.id = u.department_id
            
            WHERE t.id = %s
        """, [ticket_id])

        row = cursor.fetchone()

    if not row:
        raise Http404("ไม่พบคำร้อง")

    ticket = {
    "id": row[0],
    "title": row[1],

    # ข้อมูลการแจ้ง
    "description": row[2],          # t.description
    "problem_detail": row[12],      # td.problem_detail
    "it_category_id": row[10],      # td.it_category_id
    "it_category_name": row[11],    # ic.name

    # สถานะ
    "create_at": row[3],
    "status_id": row[4],
    "status_name": row[5],

    # ผู้แจ้ง / แผนก
    "username": row[6],
    "department": row[7],

    # ผู้รับงาน
    "assign_id": row[8],
    "assigned_to": row[9],
}


    # FILES
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, file_name, file_path, file_type
            FROM tickets.ticket_files
            WHERE ticket_id = %s
            ORDER BY id
        """, [ticket_id])

        files = []
        for f in cursor.fetchall():
            files.append({
                "id": f[0],
                "file_name": f[1],
                "file_path": f[2].replace("\\", "/"),
                "file_type": f[3],
            })

    can_approve, level = can_user_approve_ticket(ticket_id, user_id)
    
    return render(request, "tickets_form/repairs_it_detail.html", {
        "ticket": ticket,
        "files": files,
        "can_approve": can_approve,
        "level": level,
        "is_admin": is_admin,
    })


def preview_media(request, path):

    # path ที่ส่งมาเป็น uploads/erp/148/xxx.jpg
    full_path = os.path.join(settings.MEDIA_ROOT, path)

    if not os.path.exists(full_path):
        raise Http404("File not found")

    return FileResponse(open(full_path, "rb"))

# reject
@login_required_custom
@page_permission_required
def reject_ticket(request, ticket_id):

    if request.method != "POST":
        return redirect("borrow_detail", ticket_id=ticket_id)

    remark = request.POST.get("remark", "").strip()

    if not remark:
        messages.error(request, "กรุณาระบุเหตุผลในการ Reject")
        return redirect("borrow_detail", ticket_id=ticket_id)

    user = request.session["user"]
    user_id = user["id"]   

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tickets.tickets
            SET
                status_id = %s,
                reject_remark = %s,
                reject_by = %s,
                reject_at = NOW()
            WHERE id = %s
        """, [
            3,  #-- Rejected        
            remark,
            user_id,
            ticket_id
        ])

    messages.success(request, "Reject คำขอยืมอุปกรณ์เรียบร้อยแล้ว")
    return redirect("tickets_list")
