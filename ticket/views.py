from django.shortcuts import render, redirect
from django.db import connection
from django.utils import timezone
from django.contrib import messages
from django.utils.dateparse import parse_date


# views.py
import os

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

        # ❌ ไม่พบ user
        if not user:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            return render(request, "login.html")

        # ❌ ไม่ใช่ admin
        if user[3] != "admin":
            messages.error(request, "บัญชีนี้ไม่มีสิทธิ์เข้าใช้งานระบบ")
            return render(request, "login.html")

        # ✅ admin เท่านั้นถึงจะผ่าน
        request.session["user"] = {
            "id": user[0],
            "username": user[1],
            "full_name": user[2],
            "role": user[3],
        }

        return redirect("dashboard")

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

    with connection.cursor() as cursor:

        # =====================
        # SUMMARY CARDS
        # =====================
        cursor.execute("""
            SELECT COUNT(*) FROM tickets.tickets t
            JOIN tickets.status s ON s.id = t.status_id
            WHERE s.name = 'รอดำเนินการ'
        """)
        pending = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM tickets.tickets t
            JOIN tickets.status s ON s.id = t.status_id
            WHERE s.name = 'เสร็จสิ้นแล้ว'
        """)
        closed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tickets.tickets")
        total = cursor.fetchone()[0]

        # =====================
        # CHART : ticket_type
        # =====================
        cursor.execute("""
        SELECT 
            tt.name,
            COUNT(t.id) AS total
        FROM tickets.ticket_type tt
        LEFT JOIN tickets.tickets t 
            ON t.ticket_type_id = tt.id
        GROUP BY tt.name
        ORDER BY total DESC
    """)
        chart_rows = cursor.fetchall()

        chart_labels = [row[0] for row in chart_rows]
        chart_values = [row[1] for row in chart_rows]

        # =====================
        # TOP CATEGORY
        # =====================
        top_category_name = chart_labels[0] if chart_labels else ""
        top_category_count = chart_values[0] if chart_values else 0

    context = {
        "pending": pending,
        "closed": closed,
        "total": total,

        "chart_labels": chart_labels,
        "chart_values": chart_values,

        "top_category_name": top_category_name,
        "top_category_count": top_category_count,
    }

    return render(request, "dashboard.html", context)


def tickets_list(request):
    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    assignee = request.GET.get("assignee", "")
    date_range = request.GET.get("date_range", "")

    # Base query
    query = """
        SELECT t.id,
               t.title,
               t.description,
               tt.name AS ticket_type,
               u.username AS requester,
               a.username AS assignee,
               t.create_at,
               s.name AS status
        FROM tickets.tickets t
        LEFT JOIN tickets.users u ON u.id = t.user_id
        LEFT JOIN tickets.users a ON a.id = t.assign_id
        LEFT JOIN tickets.ticket_type tt ON tt.id = t.ticket_type_id
        LEFT JOIN tickets.status s ON s.id = t.status_id
        WHERE 1=1
    """

    params = []

    # Filter: search
    if search:
        query += " AND (t.id::text ILIKE %s OR t.title ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    # Filter: status
    if status:
        query += " AND s.name = %s"
        params.append(status)

    # Filter: assignee
    if assignee:
        query += " AND a.username = %s"
        params.append(assignee)

    # Filter: date range
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

    # Order at the very end (only once)
    query += " ORDER BY t.create_at DESC"

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        tickets = cursor.fetchall()

    tickets_list = []
    for row in tickets:
        tickets_list.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "ticket_type": row[3],
            "requester": row[4],
            "assignee": row[5] or "ยังไม่มอบหมาย",
            "created_at": row[6],
            "status": row[7]
        })

    return render(request, "tickets_list.html", {"tickets": tickets_list})


def tickets_create(req):
    return render(req,'tickets_create.html')

def erp_perm(request):
    if request.method == "POST":

        # -----------------------------
        # REQUEST TYPE
        # -----------------------------
        request_type = request.POST.get("request_type")

        if request_type == "open_user":
            title = "ขอเปิด User ใหม่"
        elif request_type == "adjust_perm":
            title = "ปรับปรุงสิทธิ์เดิม"
        else:
            title = "คำร้อง ERP"

        description = request.POST.get("remark", "")
        ticket_type_id = 1   # master ticket_type
        status_id = 1        # Waiting for Approve
        user_id = request.session["user"]["id"]
        department = request.POST.getlist("department[]")

        # -----------------------------
        # INSERT tickets.tickets
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
