# urls.py
from django.urls import path
from .views import tickets_report, sales_report, sessions_report

app_name = 'reports'

urlpatterns = [
    path('sales/', sales_report, name='sales_report'),
    path('sessions/', sessions_report, name='sessions_report'),
    path('tickets/', tickets_report, name='tickets_report'),
]
