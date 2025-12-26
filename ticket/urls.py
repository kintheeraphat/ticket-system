from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("admin-page/", views.admin_page),
    path("manager-page/", views.manager_page),
    path("user-page/", views.user_page),
]