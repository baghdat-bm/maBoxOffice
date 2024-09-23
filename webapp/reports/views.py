from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator

from ticket_sales.models import TicketSalesTicket, TicketSalesPayments
from .forms import TicketReportForm
from django.db.models import F, Value, CharField
from django.db.models.functions import Concat


@permission_required('reports.view_tickets_report', raise_exception=True)
def ticket_registry_report(request):
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

    else:
        print('>>>>>>> form.errors', form.errors)

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

    context = {
        'form': form,
        'page_obj': page_obj
    }
    return render(request, 'reports/tickets_report.html', context)
