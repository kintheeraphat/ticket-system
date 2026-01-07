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
    path("create/",views.tickets_create,name="create"),
    path("create/erp-perm/", views.erp_perm, name="erp_perm"),

    path("tickets/adjust/", views.adjust_form, name="adjust_form"),
    path("tickets/app-report/", views.app_report_form, name="app_report_form"),
    path("tickets/active-promotion/", views.active_promotion_form, name="active_promotion_form"),
]