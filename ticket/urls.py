from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # tickets
    path("tickets/", views.tickets_list, name="tickets"),
    path("tickets/detail/<int:ticket_id>/", views.tickets_detail, name="tickets_detail"),

    path("create/", views.tickets_create, name="create"),
    path("create/erp-perm/", views.erp_perm, name="erp_perm"),
    path("create/repairs/", views.repairs_form, name="repairs_form"),

    path("create/adjust/", views.adjust_form, name="adjust_form"),
    
    path("create/app/", views.app_form, name="app_form"),

    path("create/report/", views.report_form, name="report_form"),
    path("create/active-promotion/", views.active_promotion_form, name="active_promotion_form"),
    path("create/vpn/", views.vpn, name="vpn"),
    path("create/borrows/", views.borrows, name="borrows"),
    path("ticket-success/", views.ticket_success, name="ticket_success"),
    

]