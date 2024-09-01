import json
from datetime import datetime
from django.utils import timezone

import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse

from references.models import Event, EventTimes, EventTemplateServices, Service
from .models import TicketSale, TicketSalesService, TicketSalesPayments
from .forms import TicketSaleForm, TicketSalesServiceForm, TicketSalesPaymentsForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView

from .utils import update_ticket_amount, update_ticket_paid_amount


# TicketSale Views

class TicketSaleListView(ListView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_list.html'


class TicketSaleCreateView(CreateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


class TicketSaleUpdateView(UpdateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


class TicketSaleDetailView(DetailView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_detail.html'


class TicketSaleDeleteView(DeleteView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_confirm_delete.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


def ticket_sale_create_view(request):
    if request.method == 'POST':
        form = TicketSaleForm(request.POST)
        if form.is_valid():
            # Сохраняем форму
            ticket_sale = form.save()
            # Возвращаем JSON с информацией об ID для перенаправления в режим редактирования
            return JsonResponse({'redirect_url': reverse('ticket_sales:ticket-sale-update', args=[ticket_sale.id])})
    else:
        form = TicketSaleForm()

    return render(request, 'ticket_sales/ticket_sale_form.html', {'form': form})


def ticket_sale_update_view(request, pk):
    ticket_sale = get_object_or_404(TicketSale, pk=pk)

    if request.method == 'POST':
        form = TicketSaleForm(request.POST, instance=ticket_sale)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})  # Возвращаем успешный ответ
    else:
        form = TicketSaleForm(instance=ticket_sale)

    return render(request, 'ticket_sales/ticket_sale_form.html', {'form': form})


# TicketSalesService HTMX Views

def ticket_sales_service_create(request, ticket_sale_id):
    ticket_sale = get_object_or_404(TicketSale, id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.ticket_sale = ticket_sale
            service.save()
            update_ticket_amount(ticket_sale)

            return render(request, 'ticket_sales/partials/ticket_sales_service_list.html', {'ticket_sale': ticket_sale})
    else:
        form = TicketSalesServiceForm()
    return render(request, 'ticket_sales/partials/ticket_sales_service_form.html', {'form': form, 'ticket_sale': ticket_sale})


def ticket_sales_service_update(request, ticket_sale_id, pk):
    service = get_object_or_404(TicketSalesService, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            update_ticket_amount(service.ticket_sale)

            return render(request, 'ticket_sales/partials/ticket_sales_service_list.html',
                          {'ticket_sale': service.ticket_sale})
    else:
        form = TicketSalesServiceForm(instance=service)
    return render(request, 'ticket_sales/partials/ticket_sales_service_form.html',
                  {'form': form, 'ticket_sale': service.ticket_sale})


def ticket_sales_service_delete(request, ticket_sale_id, pk):
    service = get_object_or_404(TicketSalesService, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        ticket_sale = service.ticket_sale
        service.delete()
        update_ticket_amount(ticket_sale)

        return render(request, 'ticket_sales/partials/ticket_sales_service_list.html',
                      {'ticket_sale': service.ticket_sale})
    return render(request, 'ticket_sales/partials/ticket_sales_service_confirm_delete.html', {'service': service})


# TicketSalesPayments HTMX Views

def ticket_sales_payments_create(request, ticket_sale_id):
    ticket_sale = get_object_or_404(TicketSale, id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesPaymentsForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.ticket_sale = ticket_sale
            payment.save()
            update_ticket_paid_amount(ticket_sale)
            return render(request, 'ticket_sales/partials/ticket_sales_payments_list.html',
                          {'ticket_sale': ticket_sale})
    else:
        form = TicketSalesPaymentsForm()
    return render(request, 'ticket_sales/partials/ticket_sales_payments_form.html', {'form': form, 'ticket_sale': ticket_sale})


def ticket_sales_payments_update(request, ticket_sale_id, pk):
    payment = get_object_or_404(TicketSalesPayments, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesPaymentsForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            update_ticket_paid_amount(payment.ticket_sale)
            return render(request, 'ticket_sales/partials/ticket_sales_payments_list.html',
                          {'ticket_sale': payment.ticket_sale})
    else:
        form = TicketSalesPaymentsForm(instance=payment)
    return render(request, 'ticket_sales/partials/ticket_sales_payments_form.html', {'form': form})


def ticket_sales_payments_delete(request, ticket_sale_id, pk):
    payment = get_object_or_404(TicketSalesPayments, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        ticket_sale = payment.ticket_sale
        if payment.payment_method == "QR":
            ticket_sale.paid_qr -= payment.amount
            ticket_sale.save()
        elif payment.payment_method == "CD":
            ticket_sale.paid_card -= payment.amount
            ticket_sale.save()
        elif payment.payment_method == "CH":
            ticket_sale.paid_cash -= payment.amount
            ticket_sale.save()
        payment.delete()

        return render(request, 'ticket_sales/partials/ticket_sales_payments_list.html',
                      {'ticket_sale': ticket_sale})
    return render(request, 'ticket_sales/partials/ticket_sales_payments_confirm_delete.html', {'payment': payment})


def payment_detail_view(request, ticket_sale_id, pk):
    # Получаем объект оплаты по ticket_sale_id и pk
    payment = get_object_or_404(TicketSalesPayments, ticket_sale_id=ticket_sale_id, pk=pk)

    # Рендерим шаблон с передачей объекта оплаты
    return render(request, 'ticket_sales/partials/ticket_sales_payments_form.html', {'object': payment})


def payment_process(request, ticket_sale_id):
    ticket_sale = TicketSale.objects.get(id=ticket_sale_id)
    try:
        response = requests.get(f'http://localhost:8080/payment?amount={ticket_sale.amount}')
        json_data = response.json()
        if json_data:
            response_data = json_data.get('data')
            if response.status_code == 200 and response_data.get('status') == 'wait':
                process_id = response_data.get('processId')
                return JsonResponse({'status': 'wait', 'process_id': process_id})
        else:
            return JsonResponse({'status': 'fail'})
    except requests.RequestException:
        return JsonResponse({'status': 'fail'})


def check_payment_status(request, process_id, ticket_sale_id):
    try:
        response = requests.get(f'http://localhost:8080/status?processId={process_id}')
        response_data = response.json()
        if response.status_code == 200:
            response_data = response_data.get('data')
            if response_data.get('status') == 'success':
                chequeInfo = response_data.get("chequeInfo")
                ticket_sale = TicketSale.objects.get(id=int(ticket_sale_id))
                new_payment = TicketSalesPayments()
                new_payment.ticket_sale = ticket_sale
                new_payment.process_id = process_id
                new_payment.amount = chequeInfo['amount']
                if chequeInfo['date']:
                    new_payment.payment_date = datetime.strptime(chequeInfo['date'], "%d.%m.%y %H:%M:%S")
                else:
                    new_payment.payment_date = datetime.now()

                if chequeInfo['method'] == 'qr':
                    new_payment.payment_method = "QR"
                    ticket_sale.paid_qr += new_payment.amount
                elif chequeInfo['method'] == 'card':
                    new_payment.payment_method = "CD"
                    ticket_sale.paid_card += new_payment.amount
                else:
                    new_payment.payment_method = "CH"
                    ticket_sale.paid_cash += new_payment.amount

                new_payment.transaction_id = response_data['transactionId']
                new_payment.response_data = response_data
                new_payment.save()

                ticket_sale.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'wait'})
        return JsonResponse(response.json())
    except requests.RequestException:
        return JsonResponse({'status': 'fail'})
    except Exception as e:
        print(e.__str__())
        return JsonResponse({'status': 'wait', 'error': e.__str__()})


# обработка наличной оплаты
def cash_payment_process(request, ticket_sale_id):
    if request.method == 'POST':
        ticket_sale = TicketSale.objects.get(id=ticket_sale_id)
        paid_cash = int(request.POST.get('paid_cash'))

        # Обновляем значение поля paid_cash
        ticket_sale.paid_cash += paid_cash
        ticket_sale.save()

        new_payment = TicketSalesPayments()
        new_payment.ticket_sale = ticket_sale
        new_payment.amount = paid_cash
        new_payment.payment_date = datetime.now()
        new_payment.payment_method = "CH"
        new_payment.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'})


# печать заказа
def print_ticket_view(request, ticket_sale_id):
    services = TicketSalesService.objects.filter(ticket_sale_id=ticket_sale_id)
    data = {
        'services': [
            {
                'ticket_guid': str(service.ticket_guid),
                'service_name': service.service.name,
                'event_date': service.event_date.strftime('%d.%m.%Y'),
                'event_name': service.event.name,
                'tickets_count': service.tickets_count
            }
            for service in services
        ]
    }
    return JsonResponse(data)


def filtered_events(request):
    date = request.GET.get('date')
    events = []
    if date:
        selected_date_naive = datetime.strptime(date, '%Y-%m-%d')
        selected_date = timezone.make_aware(datetime.combine(selected_date_naive, datetime.min.time()))
        events = Event.objects.filter(begin_date__lte=selected_date, end_date__gte=selected_date)
    return JsonResponse({"events": [{"id": event.id, "name": event.event_template.name} for event in events]})


def filtered_event_times(request):
    event_id = request.GET.get('event')
    if event_id:
        event_times = EventTimes.objects.filter(event_id=event_id, is_active=True)
        times_data = [{'begin_date': time.begin_date.strftime('%H:%M')} for time in event_times]
        return JsonResponse({'times': times_data})
    return JsonResponse({'times': []})


def filtered_services(request):
    event_id = request.GET.get('event_id')
    if event_id:
        event = Event.objects.get(id=event_id)
        if event:
            services = EventTemplateServices.objects.filter(event_template=event.event_template)
            services_data = [{"id": service.service.id, "name": service.service.name} for service in services]
            return JsonResponse(services_data, safe=False)
    return JsonResponse([], safe=False)


def get_service_cost(request):
    service_id = request.GET.get('service_id')
    if service_id:
        try:
            service = Service.objects.get(id=service_id)
            return JsonResponse({'cost': service.cost})
        except Service.DoesNotExist:
            return JsonResponse({'cost': 0})
    return JsonResponse({'cost': 0})
