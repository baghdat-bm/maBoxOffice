from datetime import date, timedelta

from django.db.models import Count, Q, Sum, Case, When, F, Value, IntegerField, OuterRef, Subquery
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat, Coalesce
from collections import defaultdict, OrderedDict

from ticket_sales.models import TicketSalesTicket, TicketSale, TicketSalesService


def get_filtered_sales_data(request, form_data):
    # Основные фильтры
    start_date = form_data.get('start_date', date.today())
    end_date = form_data.get('end_date', date.today())

    # Дополнительные фильтры
    sale_types = request.GET.getlist('sale_types')
    events = request.GET.getlist('events')

    # Находим записи TicketSale в заданном интервале дат
    # ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(status="CN")
    ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(
        Q(status="CN") | Q(status="NP"))

    if sale_types and 'all' not in sale_types:
        ticket_sales = ticket_sales.filter(sale_type__in=sale_types)

    # Фильтруем записи TicketSalesTicket по найденным TicketSale
    tickets = TicketSalesTicket.objects.filter(ticket_sale__in=ticket_sales)

    if events and 'all' not in events:
        tickets = tickets.filter(event__in=events)

    # Агрегируем платежи на основе типа оплаты и добавляем обработанные поля
    tickets = tickets.annotate(
        sale_date=F('ticket_sale__date'),
        event_name=F('event__name'),
        min_payment_amount=Case(
            When(payment__amount__lte=F('amount'), then=F('payment__amount')),
            default=F('amount'),
            output_field=IntegerField()
        ),
    ).values('sale_date', 'event_name').annotate(
        # Summing all required columns
        total_amount=Sum('amount'),
        cashier_paid_card=Sum(
            Case(
                When(Q(payment__payment_method='CD') | Q(payment__payment_method='QR'), ticket_sale__sale_type='CS',
                     then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),
        cashier_paid_cash=Sum(
            Case(
                When(payment__payment_method='CH', ticket_sale__sale_type='CS', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),
        kiosk_paid=Sum(
            Case(
                When(ticket_sale__sale_type='TS', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),
        muzaidyny_qr_paid=Sum(
            Case(
                When(payment__payment_method='QR', ticket_sale__sale_type='SM', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),
        muzaidyny_card_paid=Sum(
            Case(
                When(payment__payment_method='CD', ticket_sale__sale_type='SM', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),
        kaspi_paid=Sum(
            Case(
                When(ticket_sale__sale_type='KP', then=F('min_payment_amount')),
                default=Value(0),
                output_field=IntegerField()
            )
        ),
        refund_amount=Sum('refund_amount'),
    ).order_by('-sale_date', 'event_name')

    return tickets


def get_sessions_report_data(form):
    # Get date range from form
    start_date = form.cleaned_data.get('start_date', date.today())
    end_date = form.cleaned_data.get('end_date', date.today())

    # Находим записи TicketSale в заданном интервале дат
    # ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(status="CN")
    ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(
        Q(status="CN") | Q(status="NP"))

    # Retrieve tickets based on date range
    tickets = (TicketSalesTicket.objects.filter(ticket_sale__in=ticket_sales)
               .select_related('ticket_sale', 'event', 'payment'))

    # Filter by event templates if selected
    event_templates = form.cleaned_data.get('event_templates')
    if event_templates:
        tickets = tickets.filter(event__event_template__in=event_templates)

    # Short annotations for sale type and payment method
    tickets = tickets.annotate(
        sale_type=F('ticket_sale__sale_type'),
        sale_date=F('ticket_sale__date'),
        payment_method=F('payment__payment_method'),
        event_name=F('event__name'),
    )

    final_aggregation = tickets.values(
        'event',
        'sale_date',
        'event_time',
        'event_name'
    ).annotate(
        event_quantity=F('event__quantity'),
        total_tickets_sold=Count('id'),
        total_card_sales_cs=Count('id', filter=Q(payment_method__in=['CD', 'QR']) & Q(sale_type='CS')),
        total_cash_sales_cs=Count('id', filter=Q(payment_method='CH') & Q(sale_type='CS')),
        total_kiosk_sales=Count('id', filter=Q(sale_type='TS')),
        total_qr_sales_sm=Count('id', filter=Q(payment_method='QR') & Q(sale_type='SM')),
        total_card_sales_sm=Count('id', filter=Q(payment_method='CD') & Q(sale_type='SM')),
        total_kaspi_sales=Count('id', filter=Q(sale_type='KP')),
        total_refunds=Count('id', filter=Q(is_refund=True))
    ).order_by('-sale_date', '-event_time')

    # Calculate total_tickets_left separately
    for ticket in final_aggregation:
        ticket['total_tickets_left'] = ticket['event_quantity'] - ticket['total_tickets_sold']

    return final_aggregation


def get_ticket_report_data(form):
    # Get filter values from the form
    ticket_number = form.cleaned_data.get('ticket_number')
    order_number = form.cleaned_data.get('order_number')
    start_date = form.cleaned_data.get('start_date')
    end_date = form.cleaned_data.get('end_date')
    event_templates = form.cleaned_data.get('event_templates')

    # Filter TicketSales based on date range
    # ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(status="CN")
    ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(
        Q(status="CN") | Q(status="NP"))

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
    ).order_by('-ticket_sale__id', '-ticket_number', '-event_date', '-event_time')

    return tickets


def get_services_report_data(form):
    # Filter dates
    start_date = form.cleaned_data.get('start_date')
    end_date = form.cleaned_data.get('end_date')

    # Filter ticket sales
    # ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(status="CN")
    ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date)).exclude(
        Q(status="CN") | Q(status="NP"))

    # Filter TicketSalesService based on ticket_sales
    services_data = TicketSalesService.objects.filter(ticket_sale__in=ticket_sales)

    # Filter by selected services
    selected_services = form.cleaned_data.get('services')
    if selected_services:
        services_data = services_data.filter(service__in=selected_services)

    # Group by service and date, aggregate tickets_amount and tickets_count
    grouped_data = services_data.values(
        'service__id',
        'service__name',
        'ticket_sale__date'
    ).annotate(
        total_amount=Sum('tickets_amount'),
        total_count=Sum('tickets_count')
    ).order_by('ticket_sale__date')

    # Prepare the report data
    report_data = defaultdict(lambda: defaultdict(lambda: {'amount': 0, 'count': 0}))
    total_by_service = defaultdict(lambda: {'total_amount': 0, 'total_count': 0})

    dates = sorted({entry['ticket_sale__date'] for entry in grouped_data})
    services = {entry['service__id']: entry['service__name'] for entry in grouped_data}

    for entry in grouped_data:
        service_id = entry['service__id']
        date = entry['ticket_sale__date']
        amount = entry['total_amount']
        count = entry['total_count']

        report_data[service_id][date] = {
            'amount': amount,
            'count': count
        }

        # Считаем итоги по всем датам для каждой услуги
        total_by_service[service_id]['total_amount'] += amount
        total_by_service[service_id]['total_count'] += count

    return report_data, services, dates, total_by_service
