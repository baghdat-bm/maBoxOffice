from django.urls import path
from .views import TicketSaleListView, TicketSaleCreateView, TicketSaleUpdateView, TicketSaleDeleteView, \
    TicketSaleDetailView, payment_process, check_payment_status
from .views import ticket_sales_service_create, ticket_sales_service_update, ticket_sales_service_delete
from .views import ticket_sales_payments_create, ticket_sales_payments_update, ticket_sales_payments_delete

app_name = 'ticket_sales'

urlpatterns = [
    path('list/', TicketSaleListView.as_view(), name='ticket-sale-list'),
    path('create/', TicketSaleCreateView.as_view(), name='ticket-sale-create'),
    path('<int:pk>/update/', TicketSaleUpdateView.as_view(), name='ticket-sale-update'),
    path('<int:pk>/delete/', TicketSaleDeleteView.as_view(), name='ticket-sale-delete'),
    path('<int:pk>/', TicketSaleDetailView.as_view(), name='ticket-sale-detail'),

    # TicketSalesService URLs
    path('<int:ticket_sale_id>/services/create/', ticket_sales_service_create,
         name='ticket-sales-service-create'),
    path('<int:ticket_sale_id>/services/<int:pk>/update/', ticket_sales_service_update,
         name='ticket-sales-service-update'),
    path('<int:ticket_sale_id>/services/<int:pk>/delete/', ticket_sales_service_delete,
         name='ticket-sales-service-delete'),

    # TicketSalesPayments URLs
    path('<int:ticket_sale_id>/payments/create/', ticket_sales_payments_create,
         name='ticket-sales-payments-create'),
    path('<int:ticket_sale_id>/payments/<int:pk>/update/', ticket_sales_payments_update,
         name='ticket-sales-payments-update'),
    path('<int:ticket_sale_id>/payments/<int:pk>/delete/', ticket_sales_payments_delete,
         name='ticket-sales-payments-delete'),

    # Payment process
    path('payment-process/<int:ticket_sale_id>/', payment_process, name='payment-process'),
    path('check-payment-status/<int:process_id>/', check_payment_status, name='check-payment-status'),
]
