from django.urls import path
from .views import TicketSaleListView, TicketSaleCreateView, TicketSaleUpdateView, TicketSaleDeleteView, \
    TicketSaleDetailView, payment_process, check_payment_status, payment_detail_view, ticket_sale_create_view, \
    ticket_sale_update_view, cash_payment_process, print_ticket_view, filtered_events, filtered_event_times, \
    ticket_sales_service_create, ticket_sales_service_update, ticket_sales_service_delete, \
    ticket_sales_payments_create, ticket_sales_payments_update, ticket_sales_payments_delete

app_name = 'ticket_sales'

urlpatterns = [
    path('list/', TicketSaleListView.as_view(), name='ticket-sale-list'),
    path('create/', TicketSaleCreateView.as_view(), name='ticket-sale-create'),
    path('<int:pk>/update/', TicketSaleUpdateView.as_view(), name='ticket-sale-update'),
    path('<int:pk>/delete/', TicketSaleDeleteView.as_view(), name='ticket-sale-delete'),
    path('<int:pk>/', TicketSaleDetailView.as_view(), name='ticket-sale-detail'),
    path('create-x/', ticket_sale_create_view, name='ticket-sale-create-x'),
    path('<int:pk>/update-x/', ticket_sale_update_view, name='ticket-sale-update-x'),

    # TicketSalesService URLs
    path('<int:ticket_sale_id>/services/create/', ticket_sales_service_create,
         name='ticket-sales-service-create'),
    path('<int:ticket_sale_id>/services/<int:pk>/update/', ticket_sales_service_update,
         name='ticket-sales-service-update'),
    path('<int:ticket_sale_id>/services/<int:pk>/delete/', ticket_sales_service_delete,
         name='service-delete'),

    # TicketSalesPayments URLs
    path('<int:ticket_sale_id>/payments/<int:pk>/detail', payment_detail_view, name='payment-detail'),
    path('<int:ticket_sale_id>/payments/create/', ticket_sales_payments_create, name='payment-create'),
    path('<int:ticket_sale_id>/payments/<int:pk>/update/', ticket_sales_payments_update,
         name='payment-update'),
    path('<int:ticket_sale_id>/payments/<int:pk>/delete/', ticket_sales_payments_delete,
         name='payment-delete'),

    # Payment process
    path('payment-process/<int:ticket_sale_id>/', payment_process, name='payment-process'),
    path('check-payment-status/<str:process_id>/<str:ticket_sale_id>/', check_payment_status,
         name='check-payment-status'),
    path('cash-payment-process/<int:ticket_sale_id>/', cash_payment_process, name='cash-payment-process'),

    # Print ticket
    path('ticket-print-data/<int:ticket_sale_id>/', print_ticket_view, name='ticket-print-data'),

    # Filtered events
    path('filtered-events/', filtered_events, name='filtered-events'),
    path('filtered-event-times/', filtered_event_times, name='filtered-event-times'),
]
