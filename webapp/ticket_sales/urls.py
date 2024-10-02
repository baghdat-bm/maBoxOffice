from django.urls import path
from .views import TicketSaleListView, TicketSaleUpdateView, TicketSaleDeleteView, \
    TicketSaleDetailView, payment_process_cashier, check_payment_status_cashier, payment_detail_view, \
    ticket_sale_create_view, \
    ticket_sale_update_view, cash_payment_process, print_ticket_view, filtered_events, filtered_event_times, \
    ticket_sales_service_create, ticket_sales_service_update, ticket_sales_service_delete, \
    ticket_sales_payments_create, ticket_sales_payments_update, ticket_sales_payments_delete, \
    filtered_services, get_service_cost, terminal_settings_cashier, register_terminal, refresh_terminal_token, \
    get_events_dates, get_events, TicketSaleUpdateViewTerminal, home_page_terminal, create_ticket_sale_terminal, \
    create_ticket_sale_cashier, payment_process_terminal, check_payment_status_terminal, terminal_settings_terminal, \
    get_refund_tickets, refund_tickets, kiosk_sale_tickets, ticket_sales_booking_list, ticket_sales_booking_create, \
    ticket_sales_booking_update, ticket_sales_booking_delete, tickets_purchased, delete_bookings, get_refund_payments, \
    check_payment_refund_status, bulk_delete_ticket_sales, ticket_sales_create_discount_tickets

app_name = 'ticket_sales'

urlpatterns = [
    path('list/', TicketSaleListView.as_view(), name='ticket-sale-list'),
    path('create/', create_ticket_sale_cashier, name='ticket-sale-create'),
    path('<int:pk>/update/', TicketSaleUpdateView.as_view(), name='ticket-sale-update'),
    path('<int:pk>/delete/', TicketSaleDeleteView.as_view(), name='ticket-sale-delete'),
    path('bulk-delete/', bulk_delete_ticket_sales, name='bulk-delete'),
    path('<int:pk>/', TicketSaleDetailView.as_view(), name='ticket-sale-detail'),
    path('create-x/', ticket_sale_create_view, name='ticket-sale-create-x'),
    path('<int:pk>/update-x/', ticket_sale_update_view, name='ticket-sale-update-x'),
    path('<int:pk>/update-t/', TicketSaleUpdateViewTerminal.as_view(), name='ticket-sale-update-t'),
    path('home-terminal/', home_page_terminal, name='home-terminal'),
    path('kiosk-sale-tickets/<uuid:kiosk_guid>/', kiosk_sale_tickets, name='kiosk-sale-tickets'),
    path('tickets-purchased/<int:sale_id>/', tickets_purchased, name='tickets-purchased'),
    path('create-sale-terminal/', create_ticket_sale_terminal, name='create-sale-terminal'),
    path('delete-bookings/', delete_bookings, name='delete-bookings'),

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
    path('payment-process/<int:ticket_sale_id>/', payment_process_cashier, name='payment-process'),
    path('payment-process-terminal/<int:ticket_sale_id>/', payment_process_terminal, name='payment-process-terminal'),
    path('check-payment-status/<str:process_id>/<str:ticket_sale_id>/', check_payment_status_cashier,
         name='check-payment-status'),
    path('check-payment-status-terminal/<str:process_id>/<str:ticket_sale_id>/', check_payment_status_terminal,
         name='check-payment-status-terminal'),
    path('cash-payment-process/<int:ticket_sale_id>/', cash_payment_process, name='cash-payment-process'),

    # Print ticket
    path('ticket-print-data/<int:ticket_sale_id>/', print_ticket_view, name='ticket-print-data'),

    # Filtered events, services
    path('filtered-events/', filtered_events, name='filtered-events'),
    path('filtered-event-times/', filtered_event_times, name='filtered-event-times'),
    path('filtered-services/<str:sale_type>/', filtered_services, name='filtered-services'),
    path('get-service-cost/', get_service_cost, name='get-service-cost'),
    path('get-events-dates/', get_events_dates, name='get-events-dates'),
    path('get-events/', get_events, name='get-events'),

    # Terminal settings
    path('terminal-settings-cashier/', terminal_settings_cashier, name='terminal-settings-cashier'),
    path('terminal-settings-terminal/', terminal_settings_terminal, name='terminal-settings-terminal'),
    path('register-terminal/', register_terminal, name='register-terminal'),
    path('refresh-terminal-token/', refresh_terminal_token, name='refresh-terminal-token'),

    # Возврат билетов
    path('<int:sale_id>/refund-tickets/', get_refund_tickets, name='refund_tickets_list'),
    path('<int:sale_id>/refund-tickets/confirm/', refund_tickets, name='refund_tickets'),
    path('check-refund-status/<str:process_id>/<str:ticket_sale_id>/', check_payment_refund_status,
         name='check-refund-status'),

    # Бронирование билетов
    path('bookings/<uuid:booking_guid>/', ticket_sales_booking_list, name='booking_list'),
    path('bookings/create/', ticket_sales_booking_create, name='booking_create'),
    path('bookings/<int:pk>/edit/', ticket_sales_booking_update, name='booking_update'),
    path('bookings/<int:pk>/delete/', ticket_sales_booking_delete, name='booking_delete'),
]
