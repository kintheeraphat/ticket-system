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
            SELECT id, name, spec, quantity, item_type
            FROM tickets.stock_items
            ORDER BY name
        """)
        stocks = dictfetchall(cursor)

    return render(request, "stock/stock_dashboard.html", {
        "stocks": stocks
    })

@login_required_custom
@page_permission_required
def stock_in(request):

    if request.method == "POST":

        name = request.POST.get("name")
        spec = request.POST.get("spec")
        quantity = request.POST.get("quantity")
        item_type = request.POST.get("item_type")  # 🔥 เพิ่มตรงนี้

        if not name or not quantity or not item_type:
            messages.error(request, "กรอกข้อมูลไม่ครบ")
            return redirect("stock_in")

        try:
            quantity = int(quantity)
        except ValueError:
            messages.error(request, "จำนวนต้องเป็นตัวเลข")
            return redirect("stock_in")

        with transaction.atomic():
            with connection.cursor() as cursor:

                # -----------------------------
                # เช็คว่ามี item นี้อยู่แล้วไหม
                # -----------------------------
                cursor.execute("""
                    SELECT id
                    FROM tickets.stock_items
                    WHERE name = %s
                    AND COALESCE(spec,'') = COALESCE(%s,'')
                """, [name, spec])

                row = cursor.fetchone()

                if row:
                    stock_id = row[0]

                    # เพิ่มจำนวนอย่างเดียว (ไม่เปลี่ยน item_type)
                    cursor.execute("""
                        UPDATE tickets.stock_items
                        SET quantity = quantity + %s
                        WHERE id = %s
                    """, [quantity, stock_id])

                else:
                    # เพิ่ม item ใหม่
                    cursor.execute("""
                        INSERT INTO tickets.stock_items
                        (name, spec, quantity, item_type)
                        VALUES (%s,%s,%s,%s)
                        RETURNING id
                    """, [name, spec, quantity, item_type])

                    stock_id = cursor.fetchone()[0]

                # -----------------------------
                # movement log (IN)
                # -----------------------------
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
def stock_edit(request, stock_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, name, spec, quantity, item_type
            FROM tickets.stock_items
            WHERE id = %s
        """, [stock_id])

        row = cursor.fetchone()

        if not row:
            messages.error(request, "ไม่พบข้อมูลสินค้า")
            return redirect("stock_dashboard")

        stock = {
            "id": row[0],
            "name": row[1],
            "spec": row[2],
            "quantity": row[3],
            "item_type": row[4],
        }

    if request.method == "POST":
        name = request.POST.get("name")
        spec = request.POST.get("spec")
        quantity = request.POST.get("quantity")
        item_type = request.POST.get("item_type")

        if not name or not quantity or not item_type:
            messages.error(request, "กรอกข้อมูลไม่ครบ")
            return redirect(request.path)

        try:
            quantity = int(quantity)
        except ValueError:
            messages.error(request, "จำนวนต้องเป็นตัวเลข")
            return redirect(request.path)

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE tickets.stock_items
                    SET name = %s,
                        spec = %s,
                        quantity = %s,
                        item_type = %s
                    WHERE id = %s
                """, [name, spec, quantity, item_type, stock_id])

        messages.success(request, "แก้ไขข้อมูลเรียบร้อยแล้ว")
        return redirect("stock_dashboard")

    return render(request, "stock/stock_edit.html", {
        "stock": stock
    })


@login_required_custom
@page_permission_required
def stock_dispatch_list(request):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                b.id,
                t.title,
                u.full_name
            FROM tickets.borrow_requests b
            JOIN tickets.tickets t ON b.ticket_id = t.id
            JOIN tickets.users u ON b.user_id = u.id
            WHERE NOT EXISTS (
                SELECT 1
                FROM tickets.stock_dispatch_log s
                WHERE s.borrow_id = b.id
                AND s.status IN ('borrow', 'return')
            )
            ORDER BY b.id DESC
        """)
        borrows = dictfetchall(cursor)

    return render(request, "stock/dispatch_list.html", {
        "borrows": borrows
    })


@login_required_custom
@page_permission_required
def stock_dispatch_detail(request, borrow_id):

    # ================= GET DATA =================
    with connection.cursor() as cursor:

        # ---------- BORROW + USER ----------
        cursor.execute("""
            SELECT 
                b.id,
                b.ticket_id,
                b.request_item,
                u.full_name
            FROM tickets.borrow_requests b
            JOIN tickets.users u ON b.user_id = u.id
            WHERE b.id = %s
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

        # ---------- CHECK ALREADY DISPATCH ----------
        cursor.execute("""
            SELECT 1
            FROM tickets.stock_dispatch_log
            WHERE borrow_id = %s
            AND status = 'borrow'
            LIMIT 1
        """, [borrow_id])

        if cursor.fetchone():
            messages.info(request, "รายการนี้จ่ายของไปแล้ว")
            return redirect("stock_dispatch_list")

        # ---------- PARSE REQUEST ITEM ----------
        request_items = []

        if borrow["request_item"]:
            lines = borrow["request_item"].split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # ตัดเลขลำดับ เช่น 1. xxx
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

        # ---------- STOCK LIST ----------
        cursor.execute("""
            SELECT id, name, spec, quantity
            FROM tickets.stock_items
            ORDER BY name
        """)
        stocks = dictfetchall(cursor)

    # ================= POST (DISPATCH) =================
    if request.method == "POST":

        stock_ids = request.POST.getlist("stock_id")
        quantities = request.POST.getlist("quantity")

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:

                    # ---------- 1️⃣ CHECK STOCK FIRST ----------
                    for i in range(len(stock_ids)):
                        stock_id = int(stock_ids[i])
                        qty = int(quantities[i])

                        if qty <= 0:
                            continue

                        cursor.execute("""
                            SELECT quantity
                            FROM tickets.stock_items
                            WHERE id = %s
                            FOR UPDATE
                        """, [stock_id])

                        row = cursor.fetchone()

                        if not row:
                            raise Exception("ไม่พบสินค้าในระบบ")

                        if row[0] < qty:
                            raise Exception(f"สต๊อกไม่พอ (เหลือ {row[0]})")

                    # ---------- 2️⃣ CUT STOCK + LOG ----------
                    for i in range(len(stock_ids)):
                        stock_id = int(stock_ids[i])
                        qty = int(quantities[i])

                        if qty <= 0:
                            continue

                        # ตัดสต๊อก
                        cursor.execute("""
                            UPDATE tickets.stock_items
                            SET quantity = quantity - %s
                            WHERE id = %s
                        """, [qty, stock_id])

                        # Dispatch Log
                        cursor.execute("""
                            INSERT INTO tickets.stock_dispatch_log
                            (borrow_id, stock_id, quantity, dispatch_by, status)
                            VALUES (%s,%s,%s,%s,'borrow')
                        """, [
                            borrow["borrow_id"],
                            stock_id,
                            qty,
                            request.session["user"]["id"]
                        ])

                        # Movement OUT
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

    # ================= RENDER =================
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
            SELECT DISTINCT
                b.id,
                t.title,
                u.full_name
            FROM tickets.stock_dispatch_log s
            JOIN tickets.borrow_requests b ON s.borrow_id = b.id
            JOIN tickets.tickets t ON b.ticket_id = t.id
            JOIN tickets.users u ON b.user_id = u.id
            WHERE s.status = 'borrow'
            ORDER BY b.id DESC
        """)

        borrows = dictfetchall(cursor)

    return render(request, "stock/return_list.html", {
        "borrows": borrows
    })
    
@login_required_custom
@page_permission_required
def stock_return_detail(request, borrow_id):

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                s.id,
                i.name,
                i.spec,
                s.quantity
            FROM tickets.stock_dispatch_log s
            JOIN tickets.stock_items i ON s.stock_id = i.id
            WHERE s.borrow_id = %s
            AND s.status = 'borrow'
        """, [borrow_id])

        items = dictfetchall(cursor)

        if not items:
            messages.info(request, "ไม่มีของที่ต้องคืน")
            return redirect("stock_return_list")

    return render(request, "stock/return_detail.html", {
        "items": items,
        "borrow_id": borrow_id,   # ต้องส่งชื่อนี้เป๊ะ ๆ
    })


@login_required_custom
@page_permission_required
def stock_return_now(request, borrow_id):

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:

                # 🔥 ดึง item_type มาด้วย
                cursor.execute("""
                    SELECT 
                        s.id,
                        s.stock_id,
                        s.quantity,
                        i.item_type
                    FROM tickets.stock_dispatch_log s
                    JOIN tickets.stock_items i ON s.stock_id = i.id
                    WHERE s.borrow_id = %s
                    AND s.status = 'borrow'
                    FOR UPDATE
                """, [borrow_id])

                rows = cursor.fetchall()

                if not rows:
                    messages.warning(request, "ไม่มีรายการที่ต้องคืน")
                    return redirect("stock_return_list")

                for log_id, stock_id, qty, item_type in rows:

                    # ✅ คืน stock เฉพาะของ borrow
                    if item_type == "borrow":
                        cursor.execute("""
                            UPDATE tickets.stock_items
                            SET quantity = quantity + %s
                            WHERE id = %s
                        """, [qty, stock_id])

                    # 📝 movement IN (เก็บประวัติทุกกรณี)
                    cursor.execute("""
                        INSERT INTO tickets.stock_movement
                        (stock_id, movement_type, quantity, ref_borrow_id)
                        VALUES (%s,'IN',%s,%s)
                    """, [stock_id, qty, borrow_id])

                    # 🔄 update status
                    cursor.execute("""
                        UPDATE tickets.stock_dispatch_log
                        SET status = 'return'
                        WHERE id = %s
                    """, [log_id])

        messages.success(request, "คืนของเรียบร้อยแล้ว")
        return redirect("stock_return_list")

    except Exception as e:
        messages.error(request, str(e))
        return redirect("stock_return_list")