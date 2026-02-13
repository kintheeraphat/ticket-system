from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.db import connection


def page_permission_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user = request.session.get("user")
        if not user:
            return redirect("login")

        # 🔥 ADMIN BYPASS
        if user.get("role_id") == 1:
            return view_func(request, *args, **kwargs)

        user_id = user.get("id")
        url_name = request.resolver_match.url_name

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1
                FROM tickets.user_permissions up
                JOIN tickets.permissions p
                    ON p.id = up.permission_id
                WHERE up.user_id = %s
                  AND p.url_name = %s
                  AND COALESCE(up.allow, TRUE) = TRUE
                LIMIT 1
            """, [user_id, url_name])

            has_permission = cursor.fetchone()

        if not has_permission:
            return HttpResponseForbidden("ไม่มีสิทธิ์เข้าหน้านี้")

        return view_func(request, *args, **kwargs)

    return wrapper
