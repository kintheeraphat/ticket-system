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
    context = {}
    if request.method == "POST":
        # ดึงค่าจากฟอร์มมาเก็บไว้ในตัวแปร
        context['saved_names'] = request.POST.getlist('name_en[]')
        context['saved_modules'] = request.POST.getlist('erp_module[]')
        context['saved_remark'] = request.POST.get('remark')
        
        # ทำการประมวลผลอื่นๆ (เช่น ส่ง Line Notify หรือ Email) 
        # โดยไม่ต้องเซฟลง Database
        
    return render(request, "tickets_form/erp_perm.html", context)
def vpn(req):
    return render(req,'tickets_form/vpn.html')
def borrows(req):
    return render(req,'tickets_form/borrows.html')

def tickets_detail(request):
    return render(request, "tickets_form/tickets_detail.html")


def adjust_form(request):
    return render(request, "tickets_form/adjust_form.html")


def app_report_form(request):
    return render(request, "tickets_form/app_report_form.html")


def active_promotion_form(request):
    return render(request, "tickets_form/active_promotion_form.html")
