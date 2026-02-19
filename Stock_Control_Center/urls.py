# ticket/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # ================= STOCK =================
    path("stock/", views.stock_dashboard, name="stock_dashboard"),
    path("stock/in/", views.stock_in, name="stock_in"),
    path("stock/movement/", views.stock_movement_list, name="stock_movement_list"),
    path("stock/dispatch-list/", views.stock_dispatch_list, name="stock_dispatch_list"),
    path("stock/dispatch/<int:borrow_id>/", views.stock_dispatch_detail, name="stock_dispatch_detail"),
    path("stock/return/", views.stock_return_list, name="stock_return_list"),
    path("stock/return/<int:borrow_id>/", views.stock_return_detail, name="stock_return_detail"),
    path("stock/return/<int:borrow_id>/now/", views.stock_return_now, name="stock_return_now"),
    path("stock/edit/<int:stock_id>/", views.stock_edit, name="stock_edit"),


]
