from django.shortcuts import render, redirect
from django.db import connection
from django.utils import timezone
from django.contrib import messages
from django.utils.dateparse import parse_date
from datetime import datetime
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
        # COUNT BY STATUS
        # =====================
        cursor.execute("""
            SELECT s.name, COUNT(t.id)
            FROM tickets.status s
            LEFT JOIN tickets.tickets t
                ON t.status_id = s.id
            GROUP BY s.name
        """)
        rows = cursor.fetchall()

        status_counts = {name: count for name, count in rows}

        waiting = status_counts.get("รอดำเนินการ", 0)
        waiting_approve = status_counts.get("รออนุมัติ", 0)
        in_progress = status_counts.get("กำลังดำเนินการ", 0)
        completed = status_counts.get("เสร็จสิ้นแล้ว", 0)
        cancelled = status_counts.get("ยกเลิก", 0)

        total = sum(status_counts.values())

        # =====================
        # TOP CATEGORY (ticket_type)
        # =====================
        cursor.execute("""
            SELECT tt.name, COUNT(t.id) AS total
            FROM tickets.ticket_type tt
            LEFT JOIN tickets.tickets t
                ON t.ticket_type_id = tt.id
            GROUP BY tt.name
            ORDER BY total DESC
        """)
        category_rows = cursor.fetchall()

        chart_labels = [row[0] for row in category_rows]
        chart_values = [row[1] for row in category_rows]

        top_category_name = chart_labels[0] if chart_labels else "-"
        top_category_count = chart_values[0] if chart_values else 0

    context = {
        # STATUS
        "waiting": waiting,
        "waiting_approve": waiting_approve,
        "in_progress": in_progress,
        "completed": completed,
        "cancelled": cancelled,
        "total": total,

        # CATEGORY
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

def tickets_detail(request):
    return render(request, "tickets_form/tickets_detail.html")


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

    # -----------------------------
    # CHECK LOGIN (แบบเดียวกับ erp_perm)
    # -----------------------------
    user = request.session.get("user")
    if not user:
        return redirect("login")

    if request.method == "POST":

        # -----------------------------
        # BASIC TICKET INFO
        # -----------------------------
        title = "ปรับยอดสะสม"
        description = request.POST.get("remark", "")
        user_id = user["id"]
        status_id = 1  # Waiting

        # -----------------------------
        # TICKET TYPE FROM DROPDOWN (INT)
        # -----------------------------
        ticket_type_id = request.POST.get("ticket_type_id")

        if not ticket_type_id:
            return render(request, "tickets_form/adjust_form.html", {
                "error": "กรุณาเลือกประเภทการปรับยอด"
            })

        ticket_type_id = int(ticket_type_id)

        # -----------------------------
        # MAP TICKET TYPE → CATEGORY
        # -----------------------------
        CATEGORY_MAP = {
            5: "ยอดยกจากเดิม",
            6: "แก้ไขยอด",
            7: "โอนระหว่างร้าน",
            8: "โอนระหว่างโปรโมชั่น",
        }

        adj_category = CATEGORY_MAP.get(ticket_type_id, "ไม่ระบุ")

        # -----------------------------
        # SOURCE (ต้นทาง)
        # -----------------------------
        source_cust = request.POST.get("source_cust")
        promo_info = request.POST.get("promo_info")
        earn_master = request.POST.get("earn_master")
        amount = request.POST.get("amount")

        # -----------------------------
        # TARGET (ปลายทาง)
        # -----------------------------
        target_cust = request.POST.get("target_cust")
        target_customer_name = request.POST.get("target_customer_name")
        target_promo_code = request.POST.get("target_promo_code")
        target_promo_name = request.POST.get("target_promo_name")
        target_earn_master = request.POST.get("target_earn_master")
        target_amount = request.POST.get("target_amount")

        # -----------------------------
        # VALIDATION
        # -----------------------------
        if not amount and not target_amount:
            return render(request, "tickets_form/adjust_form.html", {
                "error": "กรุณากรอกจำนวนอย่างน้อย 1 ฝั่ง"
            })

        # -----------------------------
        # INSERT tickets.tickets
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.tickets
                (
                    title,
                    description,
                    user_id,
                    status_id,
                    ticket_type_id
                )
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
        # INSERT ticket_data_adjust
        # -----------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_adjust
                (
                    ticket_id,
                    adj_category,

                    source_cust,
                    promo_info,
                    earn_master,
                    amount,

                    target_cust,
                    target_customer_name,
                    target_promo_code,
                    target_promo_name,
                    target_earn_master,
                    target_amount
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                ticket_id,
                adj_category,

                source_cust,
                promo_info,
                earn_master,
                amount,

                target_cust,
                target_customer_name,
                target_promo_code,
                target_promo_name,
                target_earn_master,
                target_amount
            ])

        # -----------------------------
        # UPLOAD FILES (เหมือน erp_perm)
        # -----------------------------
        files = request.FILES.getlist("attachments[]")
        upload_dir = f"media/uploads/adjust/{ticket_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for f in files:
            file_path = f"{upload_dir}/{f.name}"

            with open(file_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

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
                    "ADJUST",
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

    # =========================
    # GET USER_PERMISSION ID
    # =========================
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id
            FROM tickets.user_permission
            WHERE erp_user_id = %s
              AND active = true
        """, [request.session["user"]["id"]])
        row = cursor.fetchone()

    if not row:
        messages.error(request, "ไม่พบสิทธิ์ผู้ใช้งาน")
        return redirect("login")

    user_permission_id = row[0]

    # =========================
    # POST = SAVE DATA
    # =========================
    if request.method == "POST":

        # -------------------------
        # FORM DATA
        # -------------------------
        app_type = request.POST.get("app_type")  # new / update
        deadline_raw = request.POST.get("deadline")
        app_detail = request.POST.get("app_detail", "")
        objective = request.POST.get("objective", "")

        # -------------------------
        # DATE (d/m/Y → date)
        # -------------------------
        due_date = None
        if deadline_raw:
            try:
                deadline_raw = request.POST.get("deadline")
                due_date = deadline_raw if deadline_raw else None

            except ValueError:
                messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง (วัน/เดือน/ปี)")
                return redirect("app_form")

        # -------------------------
        # TITLE + FLAG
        # -------------------------
        app_new = False
        app_edit = False

        if app_type == "new":
            title = "Request Application (New)"
            app_new = True
        else:
            title = "Request Application (Update)"
            app_edit = True

        description = f"{app_detail}\n\nวัตถุประสงค์:\n{objective}"

        status_id = 1        # รอดำเนินการ
        ticket_type_id = 2   # ⚠️ ต้องเป็น ID ที่มีจริงใน ticket_type (Application)

        # =========================
        # INSERT tickets
        # =========================
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.tickets
                (title, description, user_id, status_id, ticket_type_id, create_at, due_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                title,
                description,
                user_permission_id,
                status_id,
                ticket_type_id,
                timezone.now(),
                due_date
            ])

            ticket_id = cursor.fetchone()[0]   # ✅ ใช้ได้


        # =========================
        # INSERT ticket_data_erp_app
        # =========================
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets.ticket_data_erp_app
                (
                    ticket_id,
                    app_new,
                    app_edit,
                    old_value,
                    new_value
                )
                VALUES (%s, %s, %s, %s, %s)
            """, [
                ticket_id,
                app_new,
                app_edit,
                objective if app_edit else None,
                app_detail
            ])

        messages.success(request, "ส่งคำร้อง Request Application เรียบร้อยแล้ว")
        return redirect("ticket_success")

    # =========================
    # GET = SHOW FORM
    # =========================
    return render(request, "tickets_form/app_form.html")

def report_form(request):
    return render(request, "tickets_form/report_form.html")

def active_promotion_form(request):
    return render(request, "tickets_form/active_promotion_form.html")
