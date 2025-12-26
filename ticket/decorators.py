from django.shortcuts import redirect

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user = request.session.get("user")
            if not user:
                return redirect("login")

            if user["role"] not in allowed_roles:
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
