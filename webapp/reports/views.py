from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from datetime import date, timedelta
import openpyxl
from django.db.models import Count, Q, Sum, Case, When, F, Value, IntegerField, OuterRef, Subquery
from django.contrib import messages
from django.utils.timezone import now
from openpyxl.utils import get_column_letter

from references.models import Event
from ticket_sales.models import TicketSalesTicket, TicketSalesPayments, TicketSalesService, TicketSale, SaleTypeEnum
from .forms import TicketReportForm, SalesReportForm, SessionsReportForm
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

from .utils import get_filtered_sales_data


@permission_required('reports.view_sales_report', raise_exception=True)
def sales_report(request):
    # Получаем данные из формы фильтрации
    form = SalesReportForm(request.GET or None)

    if form.is_valid():

        tickets = get_filtered_sales_data(request, form.cleaned_data)

        # Пагинация по 20 записей на страницу
        paginator = Paginator(tickets, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Итоговые суммы по текущей странице
        totals = {
            'total_amount': sum(item.amount for item in page_obj),
            'total_cashier_paid_card': sum(item.cashier_paid_card for item in page_obj),
            'total_cashier_paid_cash': sum(item.cashier_paid_cash for item in page_obj),
            'total_kiosk_paid': sum(item.kiosk_paid for item in page_obj),
            'total_muzaidyny_qr_paid': sum(item.muzaidyny_qr_paid for item in page_obj),
            'total_muzaidyny_card_paid': sum(item.muzaidyny_card_paid for item in page_obj),
            'total_kaspi_paid': sum(item.kaspi_paid for item in page_obj),
            'total_refund_amount': sum(item.refund_amount for item in page_obj),
        }

        # Получаем дополнительные данные для контекста
        sale_types = request.GET.getlist('sale_types')
        events = request.GET.getlist('events')

        # Если не выбраны sale_types или events, ставим "all" по умолчанию
        if len(sale_types) == 0:
            sale_types = ['all', ]
        if len(events) == 0:
            events = ['all', ]

    else:
        page_obj = None  # Ошибки формы
        totals = {}  # Пустые итоги
        sale_types = []
        events = []
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')

    context = {
        'form': form,
        'page_obj': page_obj,
        'totals': totals,  # Передаем итоговые суммы в контекст
        'sale_type_choices': SaleTypeEnum.choices(),
        'events_list': Event.objects.all(),
        'selected_sale_types': sale_types,  # Передаем выбранные типы продаж
        'selected_events': events,  # Передаем выбранные мероприятия
    }
    return render(request, 'reports/sales_report.html', context)


@permission_required('reports.view_sales_report', raise_exception=True)
def sales_report_export(request):
    # Получаем данные из формы фильтрации
    form = SalesReportForm(request.GET or None)

    if form.is_valid():

        tickets = get_filtered_sales_data(request, form.cleaned_data)

        # Создаем Excel-файл
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Sales Report"

        # Заголовки для столбцов
        headers = [
            "Дата", "Сумма продажи", "Касса (безнал)", "Касса (наличные)",
            "Киоск", "Muzaidyny.kz (KaspiQR)", "Muzaidyny.kz (Карта)",
            "Kaspi платежи", "Возвраты", "Мероприятие"
        ]
        sheet.append(headers)

        # Заполняем строки данными отчета
        for ticket in tickets:
            sheet.append([
                ticket.sale_date.strftime('%d.%m.%Y'),
                ticket.amount,
                ticket.cashier_paid_card,
                ticket.cashier_paid_cash,
                ticket.kiosk_paid,
                ticket.muzaidyny_qr_paid,
                ticket.muzaidyny_card_paid,
                ticket.kaspi_paid,
                ticket.refund_amount,
                ticket.event_name,
            ])

        # Настраиваем ширину колонок
        for col_num, column_title in enumerate(headers, 1):
            column_letter = get_column_letter(col_num)
            sheet.column_dimensions[column_letter].width = 15

        # Создаем HTTP-ответ с Excel-файлом
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=sales_report_{now().strftime("%Y-%m-%d")}.xlsx'
        workbook.save(response)

        return response

    else:
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')
        return redirect('reports:sales_report')


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
