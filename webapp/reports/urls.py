# urls.py
from django.urls import path
from .views import tickets_report, sales_report, sessions_report, sales_report_export, export_sessions_report_to_excel, \
    export_tickets_report_to_excel, ticket_print_data, ticket_print_pdf

app_name = 'reports'

urlpatterns = [
    path('sales/', sales_report, name='sales_report'),
    path('sales-export/', sales_report_export, name='sales_report_export'),
    path('sessions/', sessions_report, name='sessions_report'),
    path('sessions-export/', export_sessions_report_to_excel, name='sessions_report_export'),
    path('tickets/', tickets_report, name='tickets_report'),
    path('tickets-export/', export_tickets_report_to_excel, name='tickets_report_export'),
    path('ticket-print-data/<int:ticket_id>/', ticket_print_data, name='ticket-print-data'),
    path('ticket-print-pdf/<int:ticket_id>/', ticket_print_pdf, name='ticket-print-pdf'),
]
