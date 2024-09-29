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

from references.models import Event, EventTemplate
from ticket_sales.models import TicketSalesTicket, TicketSalesPayments, TicketSalesService, TicketSale, SaleTypeEnum
from .forms import TicketReportForm, SalesReportForm, SessionsReportForm
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat

from .utils import get_filtered_sales_data, get_sessions_report_data


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
    form = SessionsReportForm(request.GET or None)

    if form.is_valid():
        tickets_grouped, total_summary = get_sessions_report_data(form)

        # Paginate the results
        paginator = Paginator(tickets_grouped, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        events_list = EventTemplate.objects.all()
        selected_events = form.cleaned_data.get('event_templates', ['all'])
    else:
        page_obj = None
        total_summary = {}
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')

        events_list = EventTemplate.objects.all()
        selected_events = ['all']

    context = {
        'form': form,
        'page_obj': page_obj,
        'events_list': events_list,
        'selected_events': selected_events,
        'total_summary': total_summary,
    }

    return render(request, 'reports/sessions_report.html', context)


@permission_required('reports.view_events_report', raise_exception=True)
def export_sessions_report_to_excel(request):
    form = SessionsReportForm(request.GET or None)

    if form.is_valid():
        tickets_grouped, total_summary = get_sessions_report_data(form)

        # Create a new Excel workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Отчет по сеансам'

        # Define headers for Excel columns
        headers = [
            '№', 'Дата', 'Время сеанса', 'Кол-во всего билетов', 'Кол-во остатков билетов',
            'Кол-во проданных билетов', 'Касса (безнал)', 'Касса (наличные)', 'Киоск',
            'Muzaidyny.kz (KaspiQR)', 'Muzaidyny.kz (Карта)', 'Kaspi платежи', 'Возвраты', 'Мероприятие'
        ]

        # Write headers to Excel sheet
        for col_num, header in enumerate(headers, 1):
            ws.cell(row=1, column=col_num, value=header)

        # Write data rows
        for row_num, ticket in enumerate(tickets_grouped, start=2):
            ws.cell(row=row_num, column=1, value=row_num-1)  # №
            ws.cell(row=row_num, column=2, value=ticket['event_date'].strftime('%d.%m.%Y'))
            ws.cell(row=row_num, column=3, value=ticket['event_time'].strftime('%H:%M'))
            ws.cell(row=row_num, column=4, value=ticket['event__quantity'])
            ws.cell(row=row_num, column=5, value=ticket['total_tickets_left'])
            ws.cell(row=row_num, column=6, value=ticket['total_tickets_sold'])
            ws.cell(row=row_num, column=7, value=ticket['total_card_sales_cs'])
            ws.cell(row=row_num, column=8, value=ticket['total_cash_sales_cs'])
            ws.cell(row=row_num, column=9, value=ticket['total_kiosk_sales'])
            ws.cell(row=row_num, column=10, value=ticket['total_qr_sales_sm'])
            ws.cell(row=row_num, column=11, value=ticket['total_card_sales_sm'])
            ws.cell(row=row_num, column=12, value=ticket['total_kaspi_sales'])
            ws.cell(row=row_num, column=13, value=ticket['total_refunds'])
            ws.cell(row=row_num, column=14, value=ticket['event__event_template__name'])

        # Adjust column widths
        for col_num in range(1, len(headers) + 1):
            column_letter = get_column_letter(col_num)
            ws.column_dimensions[column_letter].width = 20

        # Create a response for the Excel file
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="sessions_report.xlsx"'
        wb.save(response)

        return response
    else:
        messages.error(request, 'Пожалуйста исправьте ошибки в фильтрах')
        return redirect('reports:sessions_report')


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
