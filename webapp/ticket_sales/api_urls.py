from django.urls import path

from ticket_sales.api import TicketCheckView, AvailableDatesView

app_name = 'ticket_sales_api'

urlpatterns = [
    path('ticket-check/', TicketCheckView.as_view(), name='ticket-check'),
    path('available-dates/', AvailableDatesView.as_view(), name='available-dates'),
]
