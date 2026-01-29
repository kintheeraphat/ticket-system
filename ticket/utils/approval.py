from django.db import connection

APPROVE_PENDING = 7   # Pending
APPROVE_WAITING = 6   # Waiting


def create_ticket_approval_by_ticket_type(
    *,
    ticket_id: int,
    ticket_type_id: int,
    requester_user_id: int,
    flow_no: int = 1
):
    """
    สร้าง approval โดย:
    - category มาจาก ticket_type
    - team มาจาก team ที่ requester อยู่ (team_members)
    - รองรับ 1 user หลาย team
    """

    with connection.cursor() as cursor:

        # ---------------------------------
        # 1) ดึง category ของ ticket_type
        # ---------------------------------
        cursor.execute("""
            SELECT category
            FROM tickets.ticket_type
            WHERE id = %s
        """, [ticket_type_id])

        row = cursor.fetchone()
        if not row:
            raise Exception("ไม่พบ ticket_type")

        category_id = row[0]

        # ---------------------------------
        # 2) หา team ที่ user อยู่ และมี approve_line
        # ---------------------------------
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
            raise Exception("ไม่พบ team ที่ user อยู่และรองรับสายอนุมัตินี้")

        team_id = team_row[0]

        # ---------------------------------
        # 3) หา level แรก
        # ---------------------------------
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

        # ---------------------------------
        # 4) กัน insert ซ้ำ
        # ---------------------------------
        cursor.execute("""
            SELECT 1
            FROM tickets.ticket_approval_status
            WHERE ticket_id = %s
            LIMIT 1
        """, [ticket_id])

        if cursor.fetchone():
            return

        # ---------------------------------
        # 5) insert ticket_approval_status
        # ---------------------------------
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
