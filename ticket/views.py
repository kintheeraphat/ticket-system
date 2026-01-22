from django.shortcuts import render, redirect
from django.db import connection
from django.utils import timezone
from django.contrib import messages
from django.utils.dateparse import parse_date
from datetime import timezone as dt_timezone
from datetime import date, timedelta
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import os,json
from django.http import Http404
from .decorators import login_required_custom, role_required
from django.conf import settings

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


def login_view(request):

    if request.session.get("user"):
        role = request.session["user"]["role"]
        if role in ["admin", "manager"]:
            return redirect("/dashboard/")
        return redirect("/tickets/")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            return render(request, "login.html")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    u.id,
                    u.username,
                    u.full_name,
                    LOWER(TRIM(r.role_name)) AS role
                FROM tickets.users u
                JOIN tickets.roles r ON r.id = u.role_id
                WHERE u.username = %s
                  AND u.password = crypt(%s, u.password)
                  AND u.is_active = TRUE
            """, [username, password])

            row = cursor.fetchone()

        if not row:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            return render(request, "login.html")

        request.session["user"] = {
            "id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
        }

        if row[3] in ["admin", "manager"]:
            return redirect("/dashboard/")
        return redirect("/tickets/")

    return render(request, "login.html")



@login_required_custom
@role_required(["user","admin", "manager"])
def ticket_success(request):
    return render(request, "tickets_form/ticket_success.html")


def logout_view(request):
    request.session.flush()
    return redirect("login")    


@login_required_custom
@role_required(["admin", "manager"])
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
@role_required(["admin", "manager", "user"])
def tickets_list(request):

    user = request.session["user"]
    role = user["role"]
    user_id = user["id"]

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    assignee = request.GET.get("assignee", "")
    date_range = request.GET.get("date_range", "")

    query = """
        SELECT t.id,
               t.title,
               t.description,
               c.name AS category,
               tt.name AS ticket_type,
               t.ticket_type_id,
               u.username AS requester,
               a.username AS assignee,
               t.create_at,
               s.name AS status
        FROM tickets.tickets t
        LEFT JOIN tickets.users u ON u.id = t.user_id
        LEFT JOIN tickets.users a ON a.id = t.assign_id
        LEFT JOIN tickets.ticket_type tt ON tt.id = t.ticket_type_id
        LEFT JOIN tickets.category c ON c.id = tt.category
        LEFT JOIN tickets.status s ON s.id = t.status_id
        WHERE 1=1
    """

    params = []

    # 🔒 user เห็นเฉพาะของตัวเอง
    if role == "user":
        query += " AND t.user_id = %s"
        params.append(user_id)

    if search:
        query += " AND (t.id::text ILIKE %s OR t.title ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    if status:
        query += " AND s.name = %s"
        params.append(status)

    if assignee and role != "user":
        query += " AND a.username = %s"
        params.append(assignee)

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
        created_at = row[8]  # ✅ index ถูกแล้ว

        if created_at and timezone.is_naive(created_at):
            created_at = timezone.make_aware(created_at, dt_timezone.utc)
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
            "assignee": row[7] or "ยังไม่มอบหมาย",
            "created_at": created_at,
            "status": row[9],
        })

    return render(request, "tickets_list.html", {
        "tickets": tickets_data,
        "is_user": role == "user",   # ✅ ส่งให้ template
    })

@login_required_custom
@role_required(["user","admin", "manager"])
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
@role_required(["user"])
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

def tickets_detail_erp(request, ticket_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                t.id        AS ticket_id,
                t.title,
                t.description,
                t.create_at AS ticket_create_at,
                u.full_name,
                t.department,
                e.requester_names,
                e.module_name
            FROM tickets.tickets t
            JOIN tickets.users u ON u.id = t.user_id
            LEFT JOIN tickets.ticket_data_erp_app e
                ON e.ticket_id = t.id
              AND t.ticket_type_id = 12
        """, [ticket_id])

        data = dictfetchone(cursor)

    if not data:
        raise Http404("ERP Ticket not found")

    # -----------------------------
    # แยก requester_names (ขึ้นบรรทัด)
    # -----------------------------
    requester_list = []
    if data.get("requester_names"):
        requester_list = [
            r.strip()
            for r in data["requester_names"].splitlines()
            if r.strip()
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

    requester_with_department = []
    for i, name in enumerate(requester_list):
        dept = department_list[i] if i < len(department_list) else ""
        requester_with_department.append({
            "name": name,
            "department": dept
        })

    return render(request, "tickets_form/tickets_detail_erp.html", {
        "ticket": {
            "id": data["ticket_id"],
            "title": data["title"],
            "description": data["description"],
            "create_at": data["ticket_create_at"],
            "user_name": data["full_name"],
        },
        "detail": {
            "requesters": requester_with_department,
            "module_name": data["module_name"] or "-",
        }
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
            JOIN tickets.users u ON u.erp_user_id = t.user_id
            WHERE t.id = %s
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
@role_required(["user", "admin", "manager"])
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
                INSERT INTO tickets.tickets
                (
                    title,
                    description,
                    user_id,
                    status_id,
                    ticket_type_id,
                    create_at
                )
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

        messages.success(request, "ส่งคำร้อง Active Promotion เรียบร้อยแล้ว")
        return redirect("ticket_success")

    # =====================
    # LOAD PAGE
    # =====================
    return render(request, "tickets_form/active_promotion_form.html")

def setting_team(request):
    with connection.cursor() as cursor:
        # ===== Departments =====
        cursor.execute("""
            SELECT id, dept_name
            FROM tickets.department
            ORDER BY dept_name
        """)
        departments = dictfetchall(cursor)

        # ===== Active Users =====
        cursor.execute("""
            SELECT id, username, full_name
            FROM tickets.users
            WHERE is_active = true
            ORDER BY full_name
        """)
        users = dictfetchall(cursor)

        # ===== Existing Teams =====
        cursor.execute("""
            SELECT 
                t.id,
                t.name AS team_name,
                d.dept_name,
                u.full_name
            FROM tickets.team t
            JOIN tickets.users u ON u.id = t.users
            LEFT JOIN tickets.department d ON d.id = t.department_id
            ORDER BY d.dept_name, t.name
        """)
        teams = dictfetchall(cursor)

    # ===== Handle POST =====
    if request.method == "POST":
        team_name = request.POST.get("team_name")
        user_id = request.POST.get("user_id")
        department_id = request.POST.get("department_id")

        if not team_name or not user_id or not department_id:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบ")
            return redirect("setting_team")

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.team (name, users, department_id)
                VALUES (%s, %s, %s)
            """, [team_name, user_id, department_id])

        messages.success(request, "สร้างทีมอนุมัติเรียบร้อยแล้ว")
        return redirect("setting_team")

    return render(request, "setting_team.html", {
        "departments": departments,
        "users": users,
        "teams": teams
    })
    
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def team_adduser(request, team_id):

    with connection.cursor() as cursor:
        # ===== Team Info =====
        cursor.execute("""
            SELECT 
                t.id,
                t.name AS team_name,
                d.dept_name,
                u.full_name AS leader_name
            FROM tickets.team t
            JOIN tickets.users u ON u.id = t.users
            LEFT JOIN tickets.department d ON d.id = t.department_id
            WHERE t.id = %s
        """, [team_id])
        team = cursor.fetchone()

        if not team:
            messages.error(request, "ไม่พบทีม")
            return redirect("setting_team")

        team_data = {
            "id": team[0],
            "team_name": team[1],
            "dept_name": team[2],
            "leader_name": team[3],
        }

        # ===== Team Members =====
        cursor.execute("""
            SELECT u.id, u.full_name, u.username
            FROM tickets.team_members tm
            JOIN tickets.users u ON u.id = tm.user_id
            WHERE tm.team_id = %s
            ORDER BY u.full_name
        """, [team_id])
        members = dictfetchall(cursor)

        # ===== All Users =====
        cursor.execute("""
            SELECT id, full_name, username
            FROM tickets.users
            WHERE is_active = true
            ORDER BY full_name
        """)
        users = dictfetchall(cursor)

    # ===== Handle Add User =====
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
        "team": team_data,
        "members": members,
        "users": users
    })


def add_approve_line(request):
    with connection.cursor() as cursor:
        # ticket types
        cursor.execute("""
            SELECT id, name
            FROM tickets.ticket_type
            ORDER BY name
        """)
        ticket_types = dictfetchall(cursor)

        # teams
        cursor.execute("""
            SELECT t.id, t.name, d.dept_name
            FROM tickets.team t
            LEFT JOIN tickets.department d ON d.id = t.department_id
            ORDER BY d.dept_name, t.name
        """)
        teams = dictfetchall(cursor)

        # users
        cursor.execute("""
            SELECT id, full_name, username
            FROM tickets.users
            WHERE is_active = true
            ORDER BY full_name
        """)
        users = dictfetchall(cursor)

    # ===== POST =====
    if request.method == "POST":
        ticket_type_id = request.POST.get("ticket_type_id")
        team_id = request.POST.get("team_id")
        user_ids = request.POST.getlist("user_ids[]")  # หลายคน

        if not ticket_type_id or not team_id or not user_ids:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบ")
            return redirect("add_approve_line")

        with connection.cursor() as cursor:
            level = 1
            for uid in user_ids:
                cursor.execute("""
                    INSERT INTO tickets.approve_line
                    (name, team2_id, level, user_id)
                    VALUES (%s, %s, %s, %s)
                """, [
                    ticket_type_id,
                    team_id,
                    level,
                    uid
                ])
                level += 1

        messages.success(request, "ตั้งค่าสายอนุมัติเรียบร้อยแล้ว")
        return redirect("add_approve_line")

    return render(request, "add_approve_line.html", {
        "ticket_types": ticket_types,
        "teams": teams,
        "users": users
    })