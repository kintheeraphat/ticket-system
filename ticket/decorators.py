from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from functools import wraps

def login_required_custom(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if "user" not in request.session:
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return _wrapped


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.session.get("user")
            if not user:
                return redirect("login")

            if user.get("role_id") not in allowed_roles:
                return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าใช้งานหน้านี้")

            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.session.get("user")
        if not user or user.get("role_id") != 1:
            return HttpResponseForbidden("Admin only")
        return view_func(request, *args, **kwargs)
    return _wrapped
