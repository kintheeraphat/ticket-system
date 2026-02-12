from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.db import connection


def page_permission_required(view_func):
    def wrapper(request, *args, **kwargs):

        user = request.session.get("user")
        if not user:
            return redirect("login")

        role_id = user.get("role_id")
        url_name = request.resolver_match.url_name

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1
                FROM tickets.page_permission
                WHERE role_id = %s
                  AND url_name = %s
                  AND can_access = TRUE
            """, [role_id, url_name])

            if not cursor.fetchone():
                return HttpResponseForbidden("ไม่มีสิทธิ์เข้าหน้านี้")

        return view_func(request, *args, **kwargs)

    return wrapper
