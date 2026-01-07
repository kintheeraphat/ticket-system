from django.shortcuts import render, redirect
from .auth_users import USERS
from .decorators import role_required

@role_required(["admin"])
def admin_page(request):
    return render(request, "admin.html")

@role_required(["manager", "admin"])
def manager_page(request):
    return render(request, "manager.html")

@role_required(["user", "manager", "admin"])
def user_page(request):
    return render(request, "user.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = USERS.get(username)

        if user and user["password"] == password:
            request.session["user"] = {
                "username": username,
                "role": user["role"]
            }
            return redirect("dashboard")

        return render(request, "login.html", {"error": "Login failed"})

    return render(request, "login.html")

def logout_view(request):
    request.session.flush()
    return redirect("login")    

def dashboard(req):
    return render(req, 'dashboard.html')

def tickets_list(req):
    return render(req,'tickets_list.html')

def tickets_create(req):
    return render(req,'tickets_create.html')

def erp_perm(request):
    return render(request, "tickets_form/erp_perm.html")