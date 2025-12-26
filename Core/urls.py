from django.contrib import admin
from django.urls import path, include # เพิ่ม include ตรงนี้

urlpatterns = [
    path('admin/', admin.site.urls),
    # เปลี่ยนจาก ticket.site.urls เป็นการ include ไฟล์ urls จากแอป ticket
    path('', include('ticket.urls')), 
]