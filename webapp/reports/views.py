from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from datetime import date, timedelta
from django.db import models
from django.db.models import Count, Q, Sum, Case, When, F, Value, IntegerField, OuterRef, Subquery
from django.contrib import messages

from references.models import Event
from ticket_sales.models import TicketSalesTicket, TicketSalesPayments, TicketSalesService, TicketSale, SaleTypeEnum
from .forms import TicketReportForm, SalesReportForm, SessionsReportForm
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat


@permission_required('reports.view_sales_report', raise_exception=True)
def sales_report(request):
    # Получаем данные из формы фильтрации
    form = SalesReportForm(request.GET or None)

    if form.is_valid():
        # Основные фильтры
        start_date = form.cleaned_data.get('start_date', date.today())
        end_date = form.cleaned_data.get('end_date', date.today())

        # Дополнительные фильтры
        sale_types = request.GET.getlist('sale_types')
        events = request.GET.getlist('events')

        # Находим записи TicketSale в заданном интервале дат
        ticket_sales = TicketSale.objects.filter(date__range=(start_date, end_date))

        # Проверяем наличие "Все" в фильтре sale_types
        if 'all' not in sale_types:
            ticket_sales = ticket_sales.filter(sale_type__in=sale_types)

        # Фильтруем записи TicketSalesTicket по найденным TicketSale
        tickets = TicketSalesTicket.objects.filter(ticket_sale__in=ticket_sales)

        # Проверяем наличие "Все" в фильтре events
        if 'all' not in events:
            tickets = tickets.filter(event__id__in=events)

        # Агрегируем платежи на основе типа оплаты и берем минимум от суммы билета и платежа
        tickets = tickets.annotate(
            sale_date=F('ticket_sale__date'),
            sale_type=F('ticket_sale__sale_type'),
            event_name=F('event__name'),

            # Минимальная сумма между платежом и суммой билета
            min_payment_amount=Case(
                When(payment__amount__lte=F('amount'), then=F('payment__amount')),
                default=F('amount'),
                output_field=IntegerField()
            ),

            # Агрегация для paid_card
            paid_card=Sum(
                Case(
                    When(payment__payment_method='CD', then=F('min_payment_amount')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),

            # Агрегация для paid_qr
            paid_qr=Sum(
                Case(
                    When(payment__payment_method='QR', then=F('min_payment_amount')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),

            # Агрегация для paid_cash
            paid_cash=Sum(
                Case(
                    When(payment__payment_method='CH', then=F('min_payment_amount')),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ),

            # Агрегация для refund_amount
            refund_amount=Sum(
                Case(
                    When(payment__refund_amount__lte=F('amount'), then=F('payment__refund_amount')),
                    default=F('amount'),
                    output_field=IntegerField()
                )
            ),
        ).order_by('sale_date', 'ticket_sale__id', 'id')

        # Пагинация по 10 записей на страницу
        paginator = Paginator(tickets, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Если не выбраны sale_types или events, ставим "all" по умолчанию
        if len(sale_types) == 0:
            sale_types = ['all', ]
        if len(events) == 0:
            events = ['all', ]

    else:
        page_obj = None  # Ошибки формы
        sale_types = []
        events = []
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')

    context = {
        'form': form,
        'page_obj': page_obj,
        'sale_type_choices': SaleTypeEnum.choices(),
        'events_list': Event.objects.all(),
        'selected_sale_types': sale_types,  # Передаем выбранные типы продаж
        'selected_events': events,  # Передаем выбранные мероприятия
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
