from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("admin-page/", views.admin_page),
    path("manager-page/", views.manager_page),
    path("user-page/", views.user_page),
    
    path("tickets/",views.tickets_list,name="tickets"),
    path("tickets/detail/", views.tickets_detail, name="tickets_detail"),

    path("create/",views.tickets_create,name="create"),
    path("create/erp-perm/", views.erp_perm, name="erp_perm"),
    path("create/repairs/", views.repairs_form, name="repairs_form"),

    path("tickets/adjust/", views.adjust_form, name="adjust_form"),
    path("tickets/app/", views.app_form, name="app_form"),
    path("tickets/report/", views.report_form, name="report_form"),
    path("tickets/active-promotion/", views.active_promotion_form, name="active_promotion_form"),
    path("create/vpn/", views.vpn, name="vpn"),
    path("create/borrows/", views.borrows, name="borrows"),

]