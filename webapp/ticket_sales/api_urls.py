from django.urls import path

from ticket_sales.api import TicketCheckView, AvailableDatesView, EventsListView, ServicesListView,  \
    CreateTicketSaleAPIView

app_name = 'ticket_sales_api'

urlpatterns = [
    path('available-event-dates/', AvailableDatesView.as_view(), name='available-event-dates'),
    path('events-list/', EventsListView.as_view(), name='events-list'),
    path('services-list/', ServicesListView.as_view(), name='services-list'),
    path('ticket-check/', TicketCheckView.as_view(), name='ticket-check'),
    path('create-tickets/', CreateTicketSaleAPIView.as_view(), name='create-tickets'),
]
