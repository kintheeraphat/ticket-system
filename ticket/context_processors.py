# ticket/context_processors.py

from django.db import connection

def user_permissions(request):
    user = request.session.get("user")
    if not user:
        return {}

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.url_name
            FROM tickets.user_permissions up
            JOIN tickets.permissions p ON p.id = up.permission_id
            WHERE up.user_id = %s
              AND COALESCE(up.allow, TRUE) = TRUE
        """, [user["id"]])

        permissions = [row[0] for row in cursor.fetchall()]

    return {
        "user_permissions": permissions
    }
