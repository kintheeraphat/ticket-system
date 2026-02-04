from django.db import connection
from django.utils import timezone

# -----------------------
# CONSTANT
# -----------------------
APPROVE_PENDING = 7    # รออนุมัติ
APPROVE_WAITING = 6    # รอ level ถัดไป
DOC_IN_PROGRESS = 4
DOC_COMPLETED = 5


# =====================================================
# CREATE APPROVAL STATUS ตอนสร้าง ticket
# =====================================================
def create_ticket_approval_by_ticket_type(
    *,
    ticket_id: int,
    ticket_type_id: int,
    requester_user_id: int,
    flow_no: int = 1   # ← คงไว้ แต่ "ไม่ใช้"
):
    """
    - category มาจาก ticket_type
    - team มาจาก team_members ของ requester
    - ❗ ใช้ approve_line ทุก flow ใน category + team
    """

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

        # 2) หา team ที่ requester อยู่ และมี approve_line
        cursor.execute("""
            SELECT DISTINCT tm.team_id
            FROM tickets.team_members tm
            JOIN tickets.approve_line al
              ON al.team_id = tm.team_id
             AND al.category_id = %s
            WHERE tm.user_id = %s
            ORDER BY tm.team_id
            LIMIT 1
        """, [category_id, requester_user_id])

        team_row = cursor.fetchone()
        if not team_row:
            raise Exception("ไม่พบ team ที่รองรับสายอนุมัติ")

        team_id = team_row[0]

        # 3) หา level แรก (ไม่สน flow)
        cursor.execute("""
            SELECT MIN(level)
            FROM tickets.approve_line
            WHERE category_id = %s
              AND team_id = %s
        """, [category_id, team_id])

        first_level = cursor.fetchone()[0]
        if first_level is None:
            raise Exception("ไม่พบ approve_line")

        # 4) กัน insert ซ้ำ
        cursor.execute("""
            SELECT 1
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
            LIMIT 1
        """, [ticket_id])

        if cursor.fetchone():
            return

        # 5) insert approval status (ทุก flow)
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
                    WHEN al.level = %s THEN %s
                    ELSE %s
                END
            FROM tickets.approve_line al
            WHERE al.category_id = %s
              AND al.team_id = %s
            ORDER BY al.level
        """, [
            ticket_id,
            first_level,
            APPROVE_PENDING,
            APPROVE_WAITING,
            category_id,
            team_id
        ])
# =====================================================
# LOAD APPROVE LINE (ทุก flow)
# =====================================================
def get_approve_line_dict_all_flows(category_id, team_id):
    """
    {
        level: {user_id, user_id, ...}
    }
    """

    approve_flow = {}

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT level, user_id
            FROM tickets.approve_line
            WHERE category_id = %s
              AND team_id = %s
            ORDER BY level
        """, [category_id, team_id])

        for level, user_id in cursor.fetchall():
            approve_flow.setdefault(level, set()).add(user_id)

    return approve_flow


# =====================================================
# APPROVE TICKET
# =====================================================
def approve_ticket_flow(*, ticket_id, approver_user_id, is_admin=False, remark=None):
    """
    - admin: ปิดทุก level ทันที
    - user: ใครก็ได้ใน level เดียวกันกดได้
    """

    with connection.cursor() as cursor:

        # ---------------------------------
        # 1) หา category + team ของ ticket
        # ---------------------------------
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
        if not row:
            raise Exception("ไม่พบ category / team")

        category_id, team_id = row

        # ---------------------------------
        # ADMIN override
        # ---------------------------------
        if is_admin:
            cursor.execute("""
                UPDATE tickets.ticket_approval_status
                SET status_id = %s,
                    action_time = %s,
                    remark = %s
                WHERE ticket_id = %s
                  AND status_id = %s
            """, [
                APPROVE_WAITING,
                timezone.now(),
                remark,
                ticket_id,
                APPROVE_PENDING
            ])

            cursor.execute("""
                UPDATE tickets.tickets
                SET status_id = %s
                WHERE id = %s
            """, [DOC_COMPLETED, ticket_id])

            return {"result": "ADMIN_COMPLETED"}

        # ---------------------------------
        # 2) หา level ปัจจุบัน
        # ---------------------------------
        cursor.execute("""
            SELECT level
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
              AND status_id = %s
            ORDER BY level
            LIMIT 1
        """, [ticket_id, APPROVE_PENDING])

        row = cursor.fetchone()
        if not row:
            raise Exception("ไม่มี level ที่รอ approve")

        current_level = row[0]

        # ---------------------------------
        # 3) โหลด approve flow (ทุก flow)
        # ---------------------------------
        flow = get_approve_line_dict_all_flows(category_id, team_id)
        current_level_users = flow.get(current_level)

        if not current_level_users:
            raise Exception("ไม่พบผู้อนุมัติใน level นี้")

        if approver_user_id not in current_level_users:
            raise Exception("คุณไม่อยู่ใน level นี้")

        # ---------------------------------
        # 4) ปิดทั้ง level ปัจจุบัน
        # ---------------------------------
        cursor.execute("""
            UPDATE tickets.ticket_approval_status
            SET status_id = %s,
                action_time = %s,
                remark = %s
            WHERE ticket_id = %s
              AND level = %s
        """, [
            APPROVE_WAITING,
            timezone.now(),
            remark,
            ticket_id,
            current_level
        ])

        # ---------------------------------
        # 5) เปิด level ถัดไป
        # ---------------------------------
        next_level = current_level + 1

        if next_level in flow:
            cursor.execute("""
                UPDATE tickets.ticket_approval_status
                SET status_id = %s
                WHERE ticket_id = %s
                  AND level = %s
            """, [APPROVE_PENDING, ticket_id, next_level])

            cursor.execute("""
                UPDATE tickets.tickets
                SET status_id = %s
                WHERE id = %s
            """, [DOC_IN_PROGRESS, ticket_id])

            return {"result": "NEXT_LEVEL", "level": next_level}

        # ---------------------------------
        # 6) จบ flow
        # ---------------------------------
        cursor.execute("""
            UPDATE tickets.tickets
            SET status_id = %s
            WHERE id = %s
        """, [DOC_COMPLETED, ticket_id])

        return {"result": "COMPLETED"}