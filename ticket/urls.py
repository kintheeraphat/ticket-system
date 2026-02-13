from django.urls import path
from . import views

urlpatterns = [

    # ===== CORE =====
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ===== TICKETS =====
    path("tickets/", views.tickets_list, name="tickets_list"),

    path("tickets/detail/erp/<int:ticket_id>/", views.tickets_detail_erp, name="tickets_detail_erp"),
    path("tickets/detail/vpn/<int:ticket_id>/", views.tickets_detail_vpn, name="tickets_detail_vpn"),
    path("tickets/detail/repairs/<int:ticket_id>/", views.tickets_detail_repairs, name="tickets_detail_repairs"),
    path("tickets/detail/report/<int:ticket_id>/", views.tickets_detail_report, name="tickets_detail_report"),
    path("tickets/detail/app/<int:ticket_id>/", views.tickets_detail_newapp, name="tickets_detail_newapp"),
    path("tickets/detail/promotion/<int:ticket_id>/", views.active_promotion_detail, name="active_promotion_detail"),

    # ===== CREATE =====
    path("create/", views.tickets_create, name="create"),
    path("create/erp-perm/", views.erp_perm, name="erp_perm"),
    path("create/repairs_it/", views.repairs_it_form, name="repairs_it_form"),
    path("create/repairs/", views.repairs_form, name="repairs_form"),
    path("create/adjust/", views.adjust_form, name="adjust_form"),
    path("create/app/", views.app_form, name="app_form"),
    path("create/report/", views.report_form, name="report_form"),
    path("create/active-promotion/", views.active_promotion_form, name="active_promotion_form"),
    path("create/vpn/", views.vpn, name="vpn"),
    path("create/borrows/", views.borrows, name="borrows"),
    path("ticket-success/", views.ticket_success, name="ticket_success"),

    # ===== TEAM =====
    path("settingline/", views.setting_team, name="setting_team"),
    path("team/<int:team_id>/add-user/", views.team_adduser, name="team_adduser"),
    path("team/<int:team_id>/remove-user/<int:member_id>/", views.team_removeuser, name="team_removeuser"),

    # ===== APPROVAL =====
    path("approval/add-line/", views.add_approve_line, name="add_approve_line"),
    path("approval/flow/<int:category_id>/<int:team_id>/",views.approval_flow_detail,name="approval_flow_detail",),

    # ===== ADMIN ACTIONS =====
    path("tickets/delete/<int:ticket_id>/", views.delete_ticket, name="delete_ticket"),
    path("tickets/approve/<int:ticket_id>/", views.approve_ticket, name="approve_ticket"),
    path("tickets/admin-complete/<int:ticket_id>/", views.admin_complete_ticket, name="admin_complete_ticket"),
    path("tickets/admin-accept/<int:ticket_id>/", views.admin_accept_work, name="admin_accept_work"),
    path("tickets/accepting-work/", views.tickets_accepting_work, name="tickets_accepting_work"),

    # ===== USER MANAGEMENT =====
    path("manage/users/", views.manage_user, name="manage_user"),
    
    # =====API LOGIN TO STOCKET_IT=====
    path("api/admin-users/", views.api_admin_users, name="api_admin_users"),
    path("report-dashboard/", views.report_dashboard, name="report_dashboard"),
    path("report-detail/<int:ticket_id>/", views.report_detail, name="report_detail"),
    path("report-export/", views.report_export_excel, name="report_export_excel"),
    path("report/<int:ticket_id>/", views.report_detail, name="report_detail"),

]
