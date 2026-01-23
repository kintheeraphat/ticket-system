from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # tickets
    path("tickets/", views.tickets_list, name="tickets_list"),
    # path("tickets/detail/", views.tickets_detail),
    path("tickets/detail/erp/<int:ticket_id>/", views.tickets_detail_erp, name="tickets_detail_erp"),
    path("tickets/detail/vpn/<int:ticket_id>/", views.tickets_detail_vpn, name="tickets_detail_vpn"),
    path("tickets/detail/repairs/<int:ticket_id>/",views.tickets_detail_repairs,name="tickets_detail_repairs"),
    path("tickets/detail/report/<int:ticket_id>/",views.tickets_detail_report,name="tickets_detail_report"),
    path("tickets/detail/app/<int:ticket_id>/",views.tickets_detail_newapp,name="tickets_detail_newapp"),
    path("tickets/detail/promotion/<int:ticket_id>/", views.active_promotion_detail, name="active_promotion_detail"),

    
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
    
    path("settingline/", views.setting_team, name="setting_team"),
    path("team/<int:team_id>/add-user/", views.team_adduser, name="team_adduser"),

    path("approval/add-line/", views.add_approve_line, name="add_approve_line"),

    path("team/<int:team_id>/add-user/", views.team_adduser, name="team_adduser"),
    path("team/<int:team_id>/remove-user/<int:member_id>/", views.team_removeuser, name="team_removeuser"),
]