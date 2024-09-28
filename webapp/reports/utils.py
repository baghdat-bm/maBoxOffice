from datetime import date, timedelta
import openpyxl
from django.db.models import Count, Q, Sum, Case, When, F, Value, IntegerField, OuterRef, Subquery
from django.db.models import F, Value, CharField

from ticket_sales.models import TicketSalesTicket, TicketSalesPayments, TicketSalesService, TicketSale, SaleTypeEnum


def get_filtered_sales_data(request, form_data):
    # Основные фильтры
    start_date = form_data.get('start_date', date.today())
    end_date = form_data.get('end_date', date.today())

    # Дополнительные фильтры
    sale_types = request.GET.getlist('sale_types')
    events = request.GET.getlist('events')

    # Находим записи TicketSale в заданном интервале дат
    ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date))

    if 'all' not in sale_types:
        ticket_sales = ticket_sales.filter(sale_type__in=sale_types)

    # Фильтруем записи TicketSalesTicket по найденным TicketSale
    tickets = TicketSalesTicket.objects.filter(ticket_sale__in=ticket_sales)

    if 'all' not in events:
        tickets = tickets.filter(event__id__in=events)

    # Агрегируем платежи на основе типа оплаты и добавляем обработанные поля
    tickets = tickets.annotate(
        sale_date=F('ticket_sale__date'),
        sale_type=F('ticket_sale__sale_type'),
        event_name=F('event__name'),

        min_payment_amount=Case(
            When(payment__amount__lte=F('amount'), then=F('payment__amount')),
            default=F('amount'),
            output_field=IntegerField()
        ),

        cashier_paid_card=Sum(
            Case(
                When(payment__payment_method='CD', sale_type='CS', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),

        cashier_paid_cash=Sum(
            Case(
                When(payment__payment_method='CH', sale_type='CS', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),

        kiosk_paid=Sum(
            Case(
                When(sale_type='TS', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),

        muzaidyny_qr_paid=Sum(
            Case(
                When(payment__payment_method='QR', sale_type='SM', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),

        muzaidyny_card_paid=Sum(
            Case(
                When(payment__payment_method='CD', sale_type='SM', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),

        kaspi_paid=Sum(
            Case(
                When(sale_type='KP', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),

        refund_amount=Sum(
            Case(
                When(payment__refund_amount__lte=F('amount'), then=F('payment__refund_amount')),
                default=F('amount'),
                output_field=IntegerField()
            )
        ),
    ).order_by('sale_date', 'ticket_sale__id', 'id')

    return tickets
