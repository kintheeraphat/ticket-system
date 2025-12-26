from django.shortcuts import render

def dashboard(req):
    return render(req, 'dashboard.html')