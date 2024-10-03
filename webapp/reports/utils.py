from datetime import date, timedelta
from pyexpat.errors import messages

import openpyxl
from django.db.models import Count, Q, Sum, Case, When, F, Value, IntegerField, OuterRef, Subquery
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

from ticket_sales.models import TicketSalesTicket, TicketSalesPayments, TicketSalesService, TicketSale, SaleTypeEnum


def get_filtered_sales_data(request, form_data):
    # Основные фильтры
    start_date = form_data.get('start_date', date.today())
    end_date = form_data.get('end_date', date.today())

    # Дополнительные фильтры
    sale_types = request.GET.getlist('sale_types')
    events = request.GET.getlist('events')

    # Находим записи TicketSale в заданном интервале дат
    ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(status="CN")

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


def get_sessions_report_data(form):
    # Get date range from form
    start_date = form.cleaned_data.get('start_date', date.today())
    end_date = form.cleaned_data.get('end_date', date.today())

    # Retrieve tickets based on date range
    tickets = (TicketSalesTicket.objects.filter(event_date__range=(start_date, end_date))
               .exclude(ticket_sale__status='CN')
               .select_related('ticket_sale', 'event', 'payment'))

    # Filter by event templates if selected
    event_templates = form.cleaned_data.get('event_templates')
    if event_templates:
        tickets = tickets.filter(event__event_template__in=event_templates)

    # Group data for the report
    tickets_grouped = tickets.values(
        'ticket_sale',
        'event',
        'event__event_template__name',
        'payment',
        'event_date',
        'event__quantity',
        'event_time'
    ).annotate(
        total_tickets_sold=Count('id'),
        total_tickets_left=F('event__quantity') - Count('id'),
        total_card_sales_cs=Count('id', filter=Q(payment__payment_method__in=['CD', 'QR']) & Q(ticket_sale__sale_type='CS')),
        total_cash_sales_cs=Count('id', filter=Q(payment__payment_method='CH') & Q(ticket_sale__sale_type='CS')),
        total_kiosk_sales=Count('id', filter=Q(ticket_sale__sale_type='TS')),
        total_qr_sales_sm=Count('id', filter=Q(payment__payment_method='QR') & Q(ticket_sale__sale_type='SM')),
        total_card_sales_sm=Count('id', filter=Q(payment__payment_method='CD') & Q(ticket_sale__sale_type='SM')),
        total_kaspi_sales=Count('id', filter=Q(ticket_sale__sale_type='KP')),
        total_refunds=Count('id', filter=Q(is_refund=True))
    ).order_by('event_date')

    # Calculate totals
    total_summary = tickets.aggregate(
        total_quantity=Sum('event__quantity'),
        total_sold=Count('id'),
        total_left=Sum('event__quantity') - Count('id'),
        total_card_sales_cs=Count('id', filter=Q(payment__payment_method__in=['CD', 'QR']) & Q(
            ticket_sale__sale_type='CS')),
        total_cash_sales_cs=Count('id', filter=Q(payment__payment_method='CH') & Q(ticket_sale__sale_type='CS')),
        total_kiosk_sales=Count('id', filter=Q(ticket_sale__sale_type='TS')),
        total_qr_sales_sm=Count('id', filter=Q(payment__payment_method='QR') & Q(ticket_sale__sale_type='SM')),
        total_card_sales_sm=Count('id', filter=Q(payment__payment_method='CD') & Q(ticket_sale__sale_type='SM')),
        total_kaspi_sales=Count('id', filter=Q(ticket_sale__sale_type='KP')),
        total_refunds=Count('id', filter=Q(is_refund=True))
    )

    return tickets_grouped, total_summary


def get_ticket_report_data(form):
    # Get filter values from the form
    ticket_number = form.cleaned_data.get('ticket_number')
    order_number = form.cleaned_data.get('order_number')
    start_date = form.cleaned_data.get('start_date')
    end_date = form.cleaned_data.get('end_date')
    event_templates = form.cleaned_data.get('event_templates')

    # Filter TicketSales based on date range
    ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(status="CN")

    # Retrieve tickets related to ticket sales
    tickets = TicketSalesTicket.objects.filter(ticket_sale__in=ticket_sales)

    # Apply filters based on form data
    if ticket_number:
        tickets = tickets.filter(number=ticket_number)
    if order_number:
        tickets = tickets.filter(ticket_sale__id=order_number)
    if event_templates:
        tickets = tickets.filter(event__event_template__in=event_templates)

    # Annotate ticket number by concatenating sale ID and ticket number
    tickets = tickets.annotate(
        ticket_number=Concat(
            F('ticket_sale__id'), Value('-'), F('number'),
            output_field=CharField()
        )
    )

    # Calculate totals for all numeric fields
    total_summary = tickets.aggregate(
        total_amount=Sum('amount')
    )

    return tickets, total_summary
