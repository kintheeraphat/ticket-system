from django.shortcuts import redirect, render
from django.db import connection, transaction
from django.contrib import messages
from django.utils import timezone
from ticket.decorators import login_required_custom
from ticket.templatetags.page_permission import page_permission_required
from ticket.views import dictfetchall

@login_required_custom
@page_permission_required
def stock_dashboard(request):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, spec, quantity
            FROM tickets.stock_items
            ORDER BY name
        """)
        stocks = dictfetchall(cursor)

    return render(request, "stock/stock_dashboard.html", {
        "stocks": stocks
    })


# Create your views here.
@login_required_custom
@page_permission_required
def stock_in(request):

    if request.method == "POST":

        name = request.POST.get("name")
        spec = request.POST.get("spec")
        quantity = request.POST.get("quantity")

        if not name or not quantity:
            messages.error(request, "กรอกข้อมูลไม่ครบ")
            return redirect("stock_in")

        quantity = int(quantity)


        with transaction.atomic():
            with connection.cursor() as cursor:

                cursor.execute("""
                    SELECT id FROM tickets.stock_items
                    WHERE name=%s AND spec=%s
                """, [name, spec])

                row = cursor.fetchone()

                if row:
                    stock_id = row[0]
                    cursor.execute("""
                        UPDATE tickets.stock_items
                        SET quantity = quantity + %s
                        WHERE id=%s
                    """, [quantity, stock_id])
                else:
                    cursor.execute("""
                        INSERT INTO tickets.stock_items
                        (name, spec, quantity)
                        VALUES (%s,%s,%s)
                        RETURNING id
                    """, [name, spec, quantity])
                    stock_id = cursor.fetchone()[0]

                # movement log
                cursor.execute("""
                    INSERT INTO tickets.stock_movement
                    (stock_id, movement_type, quantity)
                    VALUES (%s,'IN',%s)
                """, [stock_id, quantity])

        messages.success(request, "เพิ่มสต๊อกเรียบร้อยแล้ว")
        return redirect("stock_dashboard")

    return render(request, "stock/stock_in.html")

@login_required_custom
@page_permission_required
def stock_dispatch_list(request):

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT 
                b.id,
                t.title,
                u.full_name,
                b.borrow_date,
                b.return_date,
                t.department
            FROM tickets.borrow_requests b
            JOIN tickets.tickets t ON b.ticket_id = t.id
            JOIN tickets.users u ON b.user_id = u.id
            ORDER BY b.id DESC
        """)

        borrows = dictfetchall(cursor)

    return render(request, "stock/dispatch_list.html", {
        "borrows": borrows
    })
        
@login_required_custom
@page_permission_required
def stock_dispatch_detail(request, borrow_id):

    with connection.cursor() as cursor:

        # ================= BORROW + USER =================
        cursor.execute("""
            SELECT 
                b.id,
                b.ticket_id,
                b.request_item,
                u.full_name
            FROM tickets.borrow_requests b
            JOIN tickets.users u ON b.user_id = u.id
            WHERE b.id=%s
        """, [borrow_id])

        row = cursor.fetchone()

        if not row:
            return redirect("stock_dispatch_list")

        borrow = {
            "borrow_id": row[0],
            "ticket_id": row[1],
            "request_item": row[2],
            "full_name": row[3],
        }

        # ================= PARSE REQUEST ITEM =================
        request_items = []

        if borrow["request_item"]:
            lines = borrow["request_item"].split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # ตัดเลขลำดับหน้าออก เช่น 1. xxx
                if ". " in line:
                    line = line.split(". ", 1)[1]

                qty = 1
                label = line

                # หา pattern " x จำนวน"
                if " x " in line:
                    parts = line.rsplit(" x ", 1)
                    label = parts[0].strip()
                    try:
                        qty = int(parts[1].strip())
                    except:
                        qty = 1

                request_items.append({
                    "label": label,
                    "qty": qty
                })

        # ================= STOCK LIST =================
        cursor.execute("""
            SELECT id, name, spec, quantity
            FROM tickets.stock_items
            ORDER BY name
        """)
        stocks = dictfetchall(cursor)

    # ================= POST =================
    if request.method == "POST":

        stock_ids = request.POST.getlist("stock_id")
        quantities = request.POST.getlist("quantity")

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:

                    # ----------------------------
                    # 1️⃣ CHECK STOCK ALL FIRST
                    # ----------------------------
                    for i in range(len(stock_ids)):

                        stock_id = int(stock_ids[i])
                        qty = int(quantities[i])

                        if qty <= 0:
                            continue

                        cursor.execute("""
                            SELECT quantity
                            FROM tickets.stock_items
                            WHERE id=%s
                            FOR UPDATE
                        """, [stock_id])

                        row = cursor.fetchone()

                        if not row:
                            raise Exception("ไม่พบสินค้าในระบบ")

                        current_qty = row[0]

                        if current_qty < qty:
                            raise Exception(
                                f"สต๊อกไม่เพียงพอ (เหลือ {current_qty})"
                            )

                    # ----------------------------
                    # 2️⃣ CUT STOCK AFTER CHECK
                    # ----------------------------
                    for i in range(len(stock_ids)):

                        stock_id = int(stock_ids[i])
                        qty = int(quantities[i])

                        if qty <= 0:
                            continue

                        # ตัดสต๊อก
                        cursor.execute("""
                            UPDATE tickets.stock_items
                            SET quantity = quantity - %s
                            WHERE id=%s
                        """, [qty, stock_id])

                        # Dispatch Log (ผูก ticket_id)
                        cursor.execute("""
                            INSERT INTO tickets.stock_dispatch_log
                            (borrow_id, stock_id, quantity, dispatch_by, status)
                            VALUES (%s,%s,%s,%s,%s)
                        """, [
                            borrow["borrow_id"],
                            stock_id,
                            qty,
                            request.session["user"]["id"],
                            "borrow"
                        ])
                        # Movement Log (ผูก borrow_request)
                        cursor.execute("""
                            INSERT INTO tickets.stock_movement
                            (stock_id, movement_type, quantity, ref_borrow_id)
                            VALUES (%s,'OUT',%s,%s)
                        """, [
                            stock_id,
                            qty,
                            borrow["borrow_id"]
                        ])

            messages.success(request, "จ่ายของเรียบร้อยแล้ว")
            return redirect("stock_dispatch_list")

        except Exception as e:
            messages.error(request, str(e))
            return redirect(request.path)

    return render(request, "stock/dispatch_detail.html", {
        "borrow": borrow,
        "stocks": stocks,
        "request_items": request_items
    })



@login_required_custom
@page_permission_required
def stock_movement_list(request):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT m.id,
                   s.name,
                   s.spec,
                   m.movement_type,
                   m.quantity,
                   m.created_at
            FROM tickets.stock_movement m
            JOIN tickets.stock_items s ON m.stock_id = s.id
            ORDER BY m.created_at DESC
        """)
        movements = dictfetchall(cursor)

    return render(request, "stock/movement_list.html", {
        "movements": movements
    })
    
@login_required_custom
@page_permission_required
def stock_return_list(request):

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT 
                b.id,
                t.title,
                u.full_name
            FROM tickets.borrow_requests b
            JOIN tickets.tickets t ON b.ticket_id = t.id
            JOIN tickets.users u ON b.user_id = u.id
            ORDER BY b.id DESC
        """)

        borrows = dictfetchall(cursor)

        for b in borrows:

            # -----------------------
            # รวมจำนวนที่จ่ายออก
            # -----------------------
            cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0)
                FROM tickets.stock_dispatch_log
                WHERE borrow_id = %s
            """, [b["id"]])
            dispatched = cursor.fetchone()[0]

            # -----------------------
            # รวมจำนวนที่คืนเข้า
            # -----------------------
            cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0)
                FROM tickets.stock_movement
                WHERE ref_borrow_id = %s
                AND movement_type = 'IN'
            """, [b["id"]])
            returned = cursor.fetchone()[0]

            remaining = dispatched - returned

            # -----------------------
            # สถานะ
            # -----------------------
            if dispatched == 0:
                status = "no-dispatch"
            elif remaining <= 0:
                status = "returned"
            elif returned > 0:
                status = "partial"
            else:
                status = "borrowed"

            b["status"] = status
            b["remaining"] = remaining

        # ❗ แสดงเฉพาะที่ยังต้องคืน
        borrows = [
            b for b in borrows
            if b["status"] in ("borrowed", "partial")
        ]

    return render(request, "stock/return_list.html", {
        "borrows": borrows
    })

@login_required_custom
@page_permission_required
def stock_return_detail(request, borrow_id):

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT 
                b.id,
                u.full_name
            FROM tickets.borrow_requests b
            JOIN tickets.users u ON b.user_id = u.id
            WHERE b.id=%s
        """, [borrow_id])

        row = cursor.fetchone()

        if not row:
            messages.error(request, "ไม่พบข้อมูลคำขอ")
            return redirect("stock_return_list")

        borrow = {
            "borrow_id": row[0],
            "full_name": row[1],
        }

        # ดึงของที่เคยจ่าย
        cursor.execute("""
            SELECT 
                d.stock_id,
                s.name,
                s.spec,
                SUM(d.quantity) as dispatched_qty
            FROM tickets.stock_dispatch_log d
            JOIN tickets.stock_items s ON d.stock_id = s.id
            WHERE d.borrow_id=%s
            GROUP BY d.stock_id, s.name, s.spec
        """, [borrow_id])

        dispatch_items = dictfetchall(cursor)

    # ================= POST =================
    if request.method == "POST":

        stock_ids = request.POST.getlist("stock_id")
        quantities = request.POST.getlist("quantity")

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:

                    for i in range(len(stock_ids)):

                        stock_id = int(stock_ids[i])
                        return_qty = int(quantities[i])

                        if return_qty <= 0:
                            continue

                        # รวมที่เคยจ่าย
                        cursor.execute("""
                            SELECT COALESCE(SUM(quantity),0)
                            FROM tickets.stock_dispatch_log
                            WHERE stock_id=%s
                            AND borrow_id=%s
                        """, [stock_id, borrow_id])

                        dispatched_qty = cursor.fetchone()[0]

                        # รวมที่เคยคืน
                        cursor.execute("""
                            SELECT COALESCE(SUM(quantity),0)
                            FROM tickets.stock_movement
                            WHERE stock_id=%s
                            AND ref_borrow_id=%s
                            AND movement_type='IN'
                        """, [stock_id, borrow_id])

                        returned_qty = cursor.fetchone()[0]

                        available_to_return = dispatched_qty - returned_qty

                        if return_qty > available_to_return:
                            raise Exception(
                                f"คืนเกินจำนวนที่ยังไม่คืน (เหลือคืนได้ {available_to_return})"
                            )

                        # เพิ่ม stock กลับ
                        cursor.execute("""
                            UPDATE tickets.stock_items
                            SET quantity = quantity + %s
                            WHERE id=%s
                        """, [return_qty, stock_id])

                        # movement log
                        cursor.execute("""
                            INSERT INTO tickets.stock_movement
                            (stock_id, movement_type, quantity, ref_borrow_id)
                            VALUES (%s,'IN',%s,%s)
                        """, [
                            stock_id,
                            return_qty,
                            borrow_id
                        ])

            messages.success(request, "คืนของเรียบร้อยแล้ว")
            return redirect("stock_return_list")

        except Exception as e:
            messages.error(request, str(e))
            return redirect(request.path)

    return render(request, "stock/return_detail.html", {
        "borrow": borrow,
        "dispatch_items": dispatch_items
    })

@login_required_custom
@page_permission_required
def stock_return_now(request, borrow_id):

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:

                cursor.execute("""
                    SELECT 
                        stock_id,
                        SUM(quantity) as total_qty
                    FROM tickets.stock_dispatch_log
                    WHERE borrow_id=%s
                    GROUP BY stock_id
                """, [borrow_id])

                dispatch_items = cursor.fetchall()

                if not dispatch_items:
                    messages.error(request, "ไม่พบรายการที่ต้องคืน")
                    return redirect("stock_return_list")

                for stock_id, total_qty in dispatch_items:

                    # บวก stock กลับ
                    cursor.execute("""
                        UPDATE tickets.stock_items
                        SET quantity = quantity + %s
                        WHERE id=%s
                    """, [total_qty, stock_id])

                    # movement log
                    cursor.execute("""
                        INSERT INTO tickets.stock_movement
                        (stock_id, movement_type, quantity, ref_borrow_id)
                        VALUES (%s,'IN',%s,%s)
                    """, [
                        stock_id,
                        total_qty,
                        borrow_id
                    ])

                # ลบ dispatch log
                cursor.execute("""
                    DELETE FROM tickets.stock_dispatch_log
                    WHERE borrow_id=%s
                """, [borrow_id])

        messages.success(request, "คืนของเรียบร้อยแล้ว")
        return redirect("stock_return_list")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("stock_return_list")

@login_required_custom
@page_permission_required
def stock_return_now(request, borrow_id):

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:

                # ดึงของที่เคยจ่าย
                cursor.execute("""
                    SELECT stock_id, SUM(quantity)
                    FROM tickets.stock_dispatch_log
                    WHERE borrow_id=%s
                    GROUP BY stock_id
                """, [borrow_id])

                items = cursor.fetchall()

                if not items:
                    raise Exception("ไม่มีรายการให้คืน")

                for stock_id, total_qty in items:

                    # บวก stock กลับ
                    cursor.execute("""
                        UPDATE tickets.stock_items
                        SET quantity = quantity + %s
                        WHERE id=%s
                    """, [total_qty, stock_id])

                    # movement log
                    cursor.execute("""
                        INSERT INTO tickets.stock_movement
                        (stock_id, movement_type, quantity, ref_borrow_id)
                        VALUES (%s,'IN',%s,%s)
                    """, [
                        stock_id,
                        total_qty,
                        borrow_id
                    ])

                # ลบ dispatch log กันคืนซ้ำ
                cursor.execute("""
                    DELETE FROM tickets.stock_dispatch_log
                    WHERE borrow_id=%s
                """, [borrow_id])

        messages.success(request, "คืนของทั้งหมดเรียบร้อย")
        return redirect("stock_return_list")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("stock_return_list")
    
   