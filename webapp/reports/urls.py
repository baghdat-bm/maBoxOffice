# urls.py
from django.urls import path
from .views import ticket_registry_report

app_name = 'reports'

urlpatterns = [
    path('tickets/', ticket_registry_report, name='tickets_report'),
]
