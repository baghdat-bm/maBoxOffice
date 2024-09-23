from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from datetime import date, timedelta
from django.db import models
from django.db.models import Count, F, Q, Sum
from django.contrib import messages

from ticket_sales.models import TicketSalesTicket, TicketSalesPayments, TicketSalesService
from .forms import TicketReportForm, SalesReportForm, SessionsReportForm
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat


@permission_required('reports.view_tickets_report', raise_exception=True)
def tickets_report(request):
    form = TicketReportForm(request.GET or None)
    tickets = TicketSalesTicket.objects.all()

    # Фильтруем по номеру билета
    if form.is_valid():
        ticket_number = form.cleaned_data.get('ticket_number')
        order_number = form.cleaned_data.get('order_number')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        event_templates = form.cleaned_data.get('event_templates')

        if ticket_number:
            tickets = tickets.filter(number=ticket_number)
        if order_number:
            tickets = tickets.filter(ticket_sale__id=order_number)
        if start_date and end_date:
            tickets = tickets.filter(event_date__range=(start_date, end_date))
        if event_templates:
            tickets = tickets.filter(event__event_template__in=event_templates)

        # Аннотируем поле для объединения ticket_sale.id и номера билета
        tickets = tickets.annotate(
            ticket_number=Concat(
                F('ticket_sale__id'), Value('-'), F('number'),
                output_field=CharField()
            )
        )

        # Добавляем пагинацию
        paginator = Paginator(tickets, 10)  # 10 билетов на страницу
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    else:
        page_obj = None  # Ошибки формы
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')

    context = {
        'form': form,
        'page_obj': page_obj
    }
    return render(request, 'reports/tickets_report.html', context)


@permission_required('reports.view_sales_report', raise_exception=True)
def sales_report(request):
    # Получаем данные из формы фильтрации
    form = SalesReportForm(request.GET or None)
    sales = TicketSalesService.objects.all().select_related('ticket_sale', 'event', 'service')

    # Обязательный фильтр по дате
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date', date.today())
        end_date = form.cleaned_data.get('end_date', date.today())
        sales = sales.filter(event_date__range=(start_date, end_date))

        # Дополнительные фильтры
        sale_types = form.cleaned_data.get('sale_types')
        if sale_types:
            sales = sales.filter(ticket_sale__sale_type__in=sale_types)

        events = form.cleaned_data.get('events')
        if events:
            sales = sales.filter(event__in=events)

        # Группируем данные по полям sale_type, event, event_date
        sales = sales.order_by('event_date').values(
            'ticket_sale__sale_type',
            'event__name',
            'event_date'
        ).annotate(
            total_amount=models.Sum('tickets_amount'),
            paid_card=models.Sum('ticket_sale__paid_card'),
            paid_qr=models.Sum('ticket_sale__paid_qr'),
            paid_cash=models.Sum('ticket_sale__paid_cash'),
            refund_amount=models.Sum('ticket_sale__refund_amount'),
            paid_amount=models.Sum('paid_amount')
        )

        # Пагинация по 10 записей на страницу
        paginator = Paginator(sales, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None  # Ошибки формы
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')

    context = {
        'form': form,
        'page_obj': page_obj,
    }
    return render(request, 'reports/sales_report.html', context)


@permission_required('reports.view_events_report', raise_exception=True)
def sessions_report(request):
    # Получаем данные из формы фильтрации
    form = SessionsReportForm(request.GET or None)

    tickets = TicketSalesTicket.objects.all().select_related('ticket_sale', 'event', 'payment')

    # Фильтрация по дате
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date', date.today())
        end_date = form.cleaned_data.get('end_date', date.today())
        tickets = tickets.filter(event_date__range=(start_date, end_date))

        # Фильтр по мероприятиям
        event_templates = form.cleaned_data.get('event_templates')
        if event_templates:
            tickets = tickets.filter(event__event_template__in=event_templates)

        # Группировка данных по ticket_sale, event, payment, event_date
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

        # Пагинация по 10 записей на страницу
        paginator = Paginator(tickets_grouped, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

    else:
        page_obj = None  # Ошибки формы
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')

    context = {
        'form': form,
        'page_obj': page_obj,
    }

    return render(request, 'reports/sessions_report.html', context)
