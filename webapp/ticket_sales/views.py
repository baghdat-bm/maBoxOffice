import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Sum, Q, F
from django.utils import timezone
import re

import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt

from references.models import Event, EventTimes, EventTemplateServices, Service
from .models import TicketSale, TicketSalesService, TicketSalesPayments, TerminalSettings, TicketSalesTicket, \
    SaleTypeEnum, TicketSalesBooking
from .forms import TicketSaleForm, TicketSalesServiceForm, TicketSalesPaymentsForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView

from .ticket_sale_utils import get_available_events_dates, get_events_data, get_filtered_services
from .utils import update_ticket_amount, update_ticket_paid_amount, get_terminal_settings, update_terminal_token, \
    create_tickets_on_new_payment


# TicketSale Views

class TicketSaleListView(ListView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_list.html'
    context_object_name = 'object_list'
    paginate_by = 20  # Пагинация по 20 записей

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(id__icontains=query))
        return queryset


def create_ticket_sale_cashier(request):
    # Создаем новую запись TicketSale
    ticket_sale = TicketSale.objects.create(sale_type='CS', booking_guid=uuid.uuid4())

    # Перенаправляем на страницу редактирования
    return redirect(reverse('ticket_sales:ticket-sale-update', kwargs={'pk': ticket_sale.pk}))


class TicketSaleUpdateView(UpdateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


def home_page_terminal(request):
    new_guid = uuid.uuid4()
    return render(request, 'terminal/kiosk_home.html', {'new_guid': new_guid})


def kiosk_sale_tickets(request, kiosk_guid):
    ticket_sale = TicketSale.objects.filter(booking_guid=kiosk_guid).first()
    paid_amount = 0
    if ticket_sale:
        paid_amount = ticket_sale.paid_amount
    return render(request, 'terminal/muzaidyny_kiosk.html',
                  {'kiosk_guid': kiosk_guid, 'paid_amount': paid_amount})


def tickets_purchased(request, sale_id):
    return render(request, 'terminal/tickets_purchased.html', {'sale_id': sale_id})


@csrf_exempt
def delete_bookings(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        booking_guid = data.get('booking_guid')

        if booking_guid:
            # Удаляем брони с указанным booking_guid
            deleted_count, _ = TicketSalesBooking.objects.filter(booking_guid=booking_guid).delete()
            return JsonResponse({'status': 'deleted', 'deleted_count': deleted_count}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def create_ticket_sale_terminal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            tickets = data.get('tickets', [])
            total_amount = data.get('totalAmount', 0)
            booking_guid = data.get('booking_guid')
            if len(tickets) == 0:
                return JsonResponse({'error': 'No tickets data'}, status=400)

            # Шаг 2: Создаем заказ
            booking_begin_date = timezone.now()
            booking_end_date = booking_begin_date + timedelta(minutes=20)
            sale_type = data.get('sale_type', 'TS')

            ticket_sale = TicketSale.objects.filter(booking_guid=booking_guid).first()
            if ticket_sale is None:
                ticket_sale = TicketSale.objects.create(
                    booking_begin_date=booking_begin_date,
                    booking_end_date=booking_end_date,
                    sale_type=sale_type,
                    amount=total_amount,
                    booking_guid=booking_guid
                )

            tickets_count = 0
            # Шаг 3: Создаем записи TicketSalesService для каждой брони
            for ticket in tickets:
                booking = TicketSalesBooking.objects.get(id=ticket['id'])
                TicketSalesService.objects.create(
                    ticket_sale=ticket_sale,
                    service_id=booking.service_id,
                    event_id=booking.event_id,
                    event_date=booking.event_date,
                    event_time=booking.event_time,
                    event_time_end=booking.event_time_end,
                    tickets_count=booking.tickets_count,
                    tickets_amount=booking.tickets_amount,
                    total_amount=booking.total_amount
                )
                tickets_count += booking.tickets_count

            ticket_sale.amount = total_amount
            ticket_sale.tickets_count = tickets_count
            ticket_sale.save()

            return JsonResponse({'status': 'created', 'ticket_sale_id': ticket_sale.id}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


class TicketSaleUpdateViewTerminal(UpdateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form_terminal.html'
    success_url = reverse_lazy('ticket_sales:home-terminal')


class TicketSaleDetailView(DetailView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_detail.html'


class TicketSaleDeleteView(DeleteView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_confirm_delete.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')

    def post(self, request, *args, **kwargs):
        # Получаем объект заказа, который пытаемся удалить
        self.object = self.get_object()

        # Проверяем, оплачено ли поле paid_amount
        if self.object.paid_amount > 0:
            # Сообщение об ошибке для пользователя
            messages.error(request, 'Невозможно удалить оплаченный заказ.')

            # Перенаправляем пользователя обратно на список заказов
            return redirect('ticket_sales:ticket-sale-list')

        # Если заказ не оплачен, выполняем стандартное удаление
        return super().post(request, *args, **kwargs)


def bulk_delete_ticket_sales(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ids = data.get('ids', [])
        ids_count = len(ids)
        if ids_count > 0:
            # Ensure only unpaid orders are deleted
            TicketSale.objects.filter(id__in=ids, paid_amount=0).delete()
            messages.success(request, f'Удалено {ids_count} заказ(ов)')
        else:
            messages.warning(request, 'Не выбрано ни одного заказа')
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


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
@csrf_exempt
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
    return render(request, 'ticket_sales/partials/ticket_sales_service_form.html',
                  {'form': form, 'ticket_sale': ticket_sale})


@csrf_exempt
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

@csrf_exempt
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
    return render(request, 'ticket_sales/partials/ticket_sales_payments_form.html',
                  {'form': form, 'ticket_sale': ticket_sale})


@csrf_exempt
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


def payment_process_cashier(request, ticket_sale_id):
    ticket_sale = TicketSale.objects.get(id=ticket_sale_id)
    terminal = get_terminal_settings()
    if not terminal:
        return JsonResponse({'status': 'fail', 'message': 'terminal is not set'}, status=400)
    try:
        headers = {'accesstoken': terminal['access_token']}
        protocol = 'http' if terminal['ip_address'] == '127.0.0.1' else 'https'
        response = requests.get(f'{protocol}://{terminal['ip_address']}:8080/payment?amount={ticket_sale.amount}',
                                headers=headers, verify=False, timeout=100)
        response_data = response.json()
        if response_data:
            if response.status_code == 200 and response_data['status'] == 'wait':
                process_id = response_data['processId']
                return JsonResponse({'status': 'wait', 'process_id': process_id})
        else:
            return JsonResponse({'status': 'fail'}, status=400)
    except Exception as e:
        error = e.__str__()
        print('error >> ', error)
        return JsonResponse({'status': 'fail', 'error': error}, status=500)


@csrf_exempt
def payment_process_terminal(request, ticket_sale_id):
    ticket_sale = TicketSale.objects.get(id=ticket_sale_id)
    terminal = get_terminal_settings(app_type='TS')
    if not terminal:
        return JsonResponse({'status': 'fail', 'message': 'terminal is not set'}, status=400)
    try:
        headers = {'accesstoken': terminal['access_token']}
        protocol = 'http' if terminal['ip_address'] == '127.0.0.1' else 'https'
        response = requests.get(f'{protocol}://{terminal['ip_address']}:8080/payment?amount={ticket_sale.amount}',
                                headers=headers, verify=False, timeout=100)
        response_data = response.json()
        if response_data:
            if response.status_code == 200 and response_data['status'] == 'wait':
                process_id = response_data['processId']
                return JsonResponse({'status': 'wait', 'process_id': process_id})
        else:
            return JsonResponse({'status': 'fail'}, status=400)
    except Exception as e:
        error = e.__str__()
        print('error >> ', error)
        return JsonResponse({'status': 'fail', 'error': error}, status=500)


def check_payment_status_cashier(request, process_id, ticket_sale_id):
    terminal = get_terminal_settings()
    if not terminal:
        return JsonResponse({'status': 'fail', 'message': 'terminal is not set'}, status=400)
    try:
        headers = {'accesstoken': terminal['access_token']}
        protocol = 'http' if terminal['ip_address'] == '127.0.0.1' else 'https'
        response = requests.get(f'{protocol}://{terminal['ip_address']}:8080/status?processId={process_id}',
                                headers=headers, verify=False, timeout=100)
        response_data = response.json()
        if response.status_code == 200:
            if response_data['status'] == 'success':
                chequeInfo = response_data["chequeInfo"]
                ticket_sale = TicketSale.objects.get(id=int(ticket_sale_id))
                new_payment = TicketSalesPayments()
                new_payment.ticket_sale = ticket_sale
                new_payment.process_id = process_id
                if chequeInfo['date']:
                    new_payment.payment_date = datetime.strptime(chequeInfo['date'], "%d.%m.%y %H:%M:%S")
                else:
                    new_payment.payment_date = datetime.now()

                new_payment.amount = int(re.sub(r'\D', '', chequeInfo['amount']))

                if chequeInfo['method'] == 'qr':
                    new_payment.payment_method = "QR"
                    ticket_sale.paid_qr += new_payment.amount
                elif chequeInfo['method'] == 'card':
                    new_payment.payment_method = "CD"
                    new_payment.card_mask = chequeInfo['cardMask']
                    new_payment.terminal = chequeInfo['terminalId']
                    ticket_sale.paid_card += new_payment.amount
                else:
                    new_payment.payment_method = "CH"
                    ticket_sale.paid_cash += new_payment.amount

                new_payment.transaction_id = response_data['transactionId']
                new_payment.response_data = response_data
                new_payment.save()

                ticket_sale.save()

                create_tickets_on_new_payment(ticket_sale, new_payment, new_payment.amount)

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'wait'})
        return JsonResponse(response.json())
    # except requests.RequestException:
    #     return JsonResponse({'status': 'fail'})
    except Exception as e:
        print(e.__str__())
        return JsonResponse({'status': 'wait', 'error': e.__str__()})


@csrf_exempt
def check_payment_status_terminal(request, process_id, ticket_sale_id):
    terminal = get_terminal_settings(app_type='TS')
    if not terminal:
        return JsonResponse({'status': 'fail', 'message': 'terminal is not set'}, status=400)
    try:
        headers = {'accesstoken': terminal['access_token']}
        protocol = 'http' if terminal['ip_address'] == '127.0.0.1' else 'https'
        response = requests.get(f'{protocol}://{terminal['ip_address']}:8080/status?processId={process_id}',
                                headers=headers, verify=False, timeout=100)
        response_data = response.json()
        if response.status_code == 200:
            if response_data['status'] == 'success':
                chequeInfo = response_data["chequeInfo"]
                ticket_sale = TicketSale.objects.get(id=int(ticket_sale_id))
                new_payment = TicketSalesPayments()
                new_payment.ticket_sale = ticket_sale
                new_payment.process_id = process_id
                if chequeInfo['date']:
                    new_payment.payment_date = datetime.strptime(chequeInfo['date'], "%d.%m.%y %H:%M:%S")
                else:
                    new_payment.payment_date = datetime.now()

                new_payment.amount = int(re.sub(r'\D', '', chequeInfo['amount']))

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

                create_tickets_on_new_payment(ticket_sale, new_payment, new_payment.amount)
                bookings = TicketSalesBooking.objects.filter(booking_guid=ticket_sale.booking_guid)
                bookings.delete()

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'wait'})
        return JsonResponse(response.json())
    # except requests.RequestException:
    #     return JsonResponse({'status': 'fail'})
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

        create_tickets_on_new_payment(ticket_sale, new_payment, paid_cash)

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'})


# печать заказа
@csrf_exempt
def print_ticket_view(request, ticket_sale_id):
    tickets = TicketSalesTicket.objects.filter(ticket_sale_id=ticket_sale_id)
    create_tickets = False
    if not tickets.exists():
        create_tickets = True
    else:
        services = TicketSalesService.objects.filter(ticket_sale_id=ticket_sale_id)
        tickets_count = tickets.count()
        tickets_count_by_services = services.aggregate(Sum("tickets_count", default=0))
        if tickets_count != tickets_count_by_services:
            create_tickets = True

    if create_tickets:
        ticket_sale = TicketSale.objects.filter(id=ticket_sale_id).first()
        create_tickets_on_new_payment(ticket_sale, None, 0)
        tickets = TicketSalesTicket.objects.filter(ticket_sale_id=ticket_sale_id)

    data = {
        'services': [
            {
                'ticket_guid': str(ticket.ticket_guid),
                'number': ticket.number,
                'service_name': ticket.service.name,
                'event_date': ticket.event_date.strftime('%d.%m.%Y'),
                'event_time': f'{ticket.event_time.strftime('%H:%M')} - {ticket.event_time_end.strftime('%H:%M')}',
                'event_name': ticket.event.name,
                'amount': ticket.amount,
                'tickets_count': 1,
                'sale_id': ticket_sale_id
            }
            for ticket in tickets
        ]
    }
    return JsonResponse(data)


@csrf_exempt
def filtered_events(request):
    date = request.GET.get('date')
    events = []
    if date:
        selected_date_naive = datetime.strptime(date, '%Y-%m-%d')
        selected_date = timezone.make_aware(datetime.combine(selected_date_naive, datetime.min.time()))
        events = Event.objects.filter(begin_date__lte=selected_date, end_date__gte=selected_date)
    return JsonResponse({"events": [{"id": event.id, "name": event.name} for event in events]})


@csrf_exempt
def filtered_event_times(request):
    event_id = request.GET.get('event')
    if event_id:
        event_times = EventTimes.objects.filter(event_id=event_id, is_active=True)
        times_data = [{'begin_date': time.begin_date.strftime('%H:%M')} for time in event_times]
        return JsonResponse({'times': times_data})
    return JsonResponse({'times': []})


@csrf_exempt
def get_events(request):
    date = request.GET.get('date')
    data = get_events_data(date)
    return JsonResponse({'events': data})


@csrf_exempt
def filtered_services(request, sale_type):
    event_id = request.GET.get('event_id')
    data = get_filtered_services(event_id, sale_type)
    return JsonResponse(data, safe=False)


@csrf_exempt
def get_service_cost(request):
    service_id = request.GET.get('service_id')
    if service_id:
        try:
            service = Service.objects.get(id=service_id)
            return JsonResponse({'cost': service.cost})
        except Service.DoesNotExist:
            return JsonResponse({'cost': 0})
    return JsonResponse({'cost': 0})


def terminal_settings_cashier(request):
    settings = TerminalSettings.objects.filter(app_type='CS').first()

    if request.method == 'POST':
        ip_address = request.POST.get('ip_address')
        username = request.POST.get('username')
        access_token = request.POST.get('access_token')
        refresh_token = request.POST.get('refresh_token')
        expiration_date = request.POST.get('expiration_date')

        if not ip_address or not username:
            messages.error(request, "Необходимо заполнить поля IP Address и Username.")
            return redirect('ticket_sales:terminal-settings-cashier')

        if settings is None:
            settings = TerminalSettings(
                ip_address=ip_address,
                username=username,
                access_token=access_token,
                refresh_token=refresh_token,
                expiration_date=expiration_date,
                app_type='CS'
            )
        else:
            settings.ip_address = ip_address
            settings.username = username
            settings.access_token = access_token
            settings.refresh_token = refresh_token
            settings.expiration_date = expiration_date

        settings.save()
        messages.success(request, "Настройки сохранены.")

        return redirect('ticket_sales:terminal-settings-cashier')

    context = {
        'settings': settings,
    }
    return render(request, 'ticket_sales/terminal_settings-cashier.html', context)


def terminal_settings_terminal(request):
    settings = TerminalSettings.objects.filter(app_type='TS').first()

    if request.method == 'POST':
        ip_address = request.POST.get('ip_address')
        username = request.POST.get('username')
        access_token = request.POST.get('access_token')
        refresh_token = request.POST.get('refresh_token')
        expiration_date = request.POST.get('expiration_date')

        if not ip_address or not username:
            messages.error(request, "Необходимо заполнить поля IP Address и Username.")
            return redirect('ticket_sales:terminal-settings-terminal')

        if settings is None:
            settings = TerminalSettings(
                ip_address=ip_address,
                username=username,
                access_token=access_token,
                refresh_token=refresh_token,
                expiration_date=expiration_date,
                app_type='TS'
            )
        else:
            settings.ip_address = ip_address
            settings.username = username
            settings.access_token = access_token
            settings.refresh_token = refresh_token
            settings.expiration_date = expiration_date

        settings.save()
        messages.success(request, "Настройки сохранены.")

        return redirect('ticket_sales:terminal-settings-terminal')

    context = {
        'settings': settings,
    }
    return render(request, 'ticket_sales/terminal_settings-terminal.html', context)


def register_terminal(request):
    ip_address = request.GET.get('ip_address')
    username = request.GET.get('username')

    if not ip_address or not username:
        message = 'Необходимо заполнить поля IP Address и Username'
        messages.error(request, message)
        return JsonResponse({'error': message}, status=400)

    url = f"https://{ip_address}:8080/register?name={username}"

    try:
        response = requests.get(url, timeout=10, verify=False)

        if response.status_code == 200:
            data = response.json()
            expiration_date = make_aware(parse_datetime(data['expirationDate']))
            settings = TerminalSettings.objects.first()
            if settings:
                settings.ip_address = ip_address
                settings.username = username
                settings.access_token = data['accessToken']
                settings.refresh_token = data['refreshToken']
                settings.expiration_date = expiration_date
            else:
                settings = TerminalSettings(
                    ip_address=ip_address,
                    username=username,
                    access_token=data['accessToken'],
                    refresh_token=data['refreshToken'],
                    expiration_date=expiration_date,
                )
            settings.save()
            messages.success(request, "Регистрация прошла успешно.")
            return JsonResponse({'status': 'success'})
        elif response.status_code == 500:
            return JsonResponse({'error': response.json().get('message', 'Unknown error')}, status=500)
        else:
            return JsonResponse({'error': 'Unknown error occurred during registration.'}, status=response.status_code)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Connection error: {str(e)}'}, status=500)


def refresh_terminal_token(request):
    ip_address = request.GET.get('ip_address')
    username = request.GET.get('username')
    refresh_token = request.GET.get('refresh_token')

    terminal_settings = get_terminal_settings()
    if not terminal_settings:
        terminal_settings = TerminalSettings(
            ip_address=ip_address,
            username=username,
            access_token='',
            refresh_token=refresh_token
        )

    result = update_terminal_token(terminal_settings)
    if result['status'] == 200:
        messages.success(request, "Токен успешно обновлен.")
        return JsonResponse({'status': 'success'})
    else:
        messages.error(request, result['error'])
        return JsonResponse({'status': 'fail', 'error': result['error']}, status=400)


@csrf_exempt
def get_events_dates(request):
    available_dates = get_available_events_dates()
    return JsonResponse({"available_dates": available_dates})


def get_refund_tickets(request, sale_id):
    ticket_sale = get_object_or_404(TicketSale, pk=sale_id)
    tickets = TicketSalesTicket.objects.filter(ticket_sale=ticket_sale, is_refund=False).filter(
        Q(last_event_code="") | Q(last_event_code=None)
    )

    refund_text = ''
    if ticket_sale.paid_cash > 0:
        refund_text = 'Итого к возврату наличными'
    elif ticket_sale.paid_card > 0:
        refund_text = 'Итого к возврату банковской картой'
    elif ticket_sale.paid_qr > 0:
        refund_text = 'Итого к возврату по QR коду'
    context = {'tickets': tickets, 'sale_id': sale_id, 'refund_text': refund_text}
    return render(request, 'ticket_sales/partials/refund_ticket_list.html', context=context)


def refund_tickets(request, sale_id):
    if request.method == "POST":
        # Получаем заказ
        ticket_sale = get_object_or_404(TicketSale, pk=sale_id)
        terminal = get_terminal_settings(ticket_sale.sale_type)
        if not terminal:
            return JsonResponse({'success': False, 'message': 'Не заданы настройки для терминала оплаты'},
                                status=400)

        # Парсим JSON-данные из тела запроса
        try:
            data = json.loads(request.body)
            ticket_ids = data.get('tickets', [])
            print('>>>> ticket_ids', ticket_ids, 'ticket_sale', ticket_sale)

            # Проверяем, что выбраны билеты
            if not ticket_ids:
                return JsonResponse({'success': False, 'message': 'Не выбраны билеты к возврату'}, status=400)

            # Получаем список билетов к возврату
            tickets = TicketSalesTicket.objects.filter(id__in=ticket_ids, is_refund=False)

            # Определяем оплаты к возврату
            payment_refund_map = defaultdict(lambda: {'amount': 0, 'tickets': []})
            for ticket in tickets:
                payment = ticket.payment
                payment_refund_map[payment]['amount'] += ticket.amount
                payment_refund_map[payment]['tickets'].append(ticket)

            process_ids = []
            ticket_ids = []
            errors = []
            # Обрабатываем платежи к возврату
            for payment, data in payment_refund_map.items():
                if payment.payment_method == 'QR' or payment.payment_method == 'CD':
                    try:
                        headers = {'accesstoken': terminal['access_token']}
                        protocol = 'http' if terminal['ip_address'] == '127.0.0.1' else 'https'
                        method = "card" if payment.payment_method == 'CD' else "qr"
                        url = f'{protocol}://{terminal['ip_address']}:8080/v2/refund?method={method}'
                        url += f'"&amount={data['amount']}&transactionId={payment.transaction_id}'
                        response = requests.get(url, headers=headers, verify=False, timeout=100)
                        response_data = response.json()
                        if response_data:
                            if response.status_code == 200 and response_data['status'] == 'wait':
                                payment.process_id = response_data['processId']
                                payment.save()
                                process_ids.append(payment.process_id)
                                for ticket in data['tickets']:
                                    ticket.process_id = response_data['processId']
                                    ticket.save()
                            else:
                                errors.append(response_data['errorText'])
                        else:
                            errors.append(response_data['errorText'])
                            return JsonResponse({'success': False, 'message': response_data['errorText']}, status=400)
                    except Exception as e:
                        error = e.__str__()
                        print('error >> ', error)
                        return JsonResponse({'success': False, 'message': e.__str__()}, status=500)
                else:  # Возврат наличной оплаты
                    payment.refund_amount += data['amount']
                    payment.save()
                    # Помечаем возвратные билеты
                    for ticket in data['tickets']:
                        ticket.is_refund = True
                        ticket.save()
                        ticket_ids.append(ticket.id)
                    # Обновляем сумму возврата в заказе
                    ticket_sale.refund_amount += data['amount']

            ticket_sale.save()

            if len(errors) > 0:
                message = 'Произошла ошибка при выполнении возврата...'
                status = 400
                success = False
            elif len(process_ids) == 0:
                message = 'Возврат успешно обработан'
                status = 200
                success = True
            else:
                message = 'Возврат обрабатывается...'
                status = 202
                success = False
            return JsonResponse({'success': success, 'message': message, 'process_ids': process_ids,
                                 'ticket_ids': ticket_ids, 'errors': errors}, status=status)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Не корректные данные'}, status=400)

    return JsonResponse({'success': False, 'message': 'Не корректный http метод'}, status=400)


def check_payment_refund_status(request, process_id, ticket_sale_id):
    terminal = get_terminal_settings()
    if not terminal:
        return JsonResponse({'status': 'fail', 'message': 'terminal is not set'}, status=400)
    try:
        headers = {'accesstoken': terminal['access_token']}
        protocol = 'http' if terminal['ip_address'] == '127.0.0.1' else 'https'
        response = requests.get(f'{protocol}://{terminal['ip_address']}:8080/status?processId={process_id}',
                                headers=headers, verify=False, timeout=100)
        response_data = response.json()
        if response.status_code == 200:
            if response_data['status'] == 'success':
                chequeInfo = response_data["chequeInfo"]
                ticket_sale = TicketSale.objects.get(id=int(ticket_sale_id))
                new_payment = TicketSalesPayments()
                new_payment.ticket_sale = ticket_sale
                new_payment.process_id = process_id
                if chequeInfo['date']:
                    new_payment.payment_date = datetime.strptime(chequeInfo['date'], "%d.%m.%y %H:%M:%S")
                else:
                    new_payment.payment_date = datetime.now()

                new_payment.amount = int(re.sub(r'\D', '', chequeInfo['amount']))

                if chequeInfo['method'] == 'qr':
                    new_payment.payment_method = "QR"
                    ticket_sale.paid_qr += new_payment.amount
                elif chequeInfo['method'] == 'card':
                    new_payment.payment_method = "CD"
                    new_payment.card_mask = chequeInfo['cardMask']
                    new_payment.terminal = chequeInfo['terminalId']
                    ticket_sale.paid_card += new_payment.amount
                else:
                    new_payment.payment_method = "CH"
                    ticket_sale.paid_cash += new_payment.amount

                new_payment.transaction_id = response_data['transactionId']
                new_payment.response_data = response_data
                new_payment.save()

                ticket_sale.save()

                create_tickets_on_new_payment(ticket_sale, new_payment, new_payment.amount)

                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'wait'})
        return JsonResponse(response.json())
    # except requests.RequestException:
    #     return JsonResponse({'status': 'fail'})
    except Exception as e:
        print(e.__str__())
        return JsonResponse({'status': 'wait', 'error': e.__str__()})


def get_refund_payments(request, sale_id):
    ticket_sale = get_object_or_404(TicketSale, pk=sale_id)

    # Get only necessary fields and calculate remaining refund amount
    payments = (
        TicketSalesPayments.objects
        .filter(ticket_sale=ticket_sale, amount__gt=F('refund_amount'))
        .annotate(remaining_amount=F('amount') - F('refund_amount'))
        .values('id', 'amount', 'payment_date', 'remaining_amount')
    )

    refund_text = ''
    if ticket_sale.paid_cash > 0:
        refund_text = 'Итого к возврату наличными'
    elif ticket_sale.paid_card > 0:
        refund_text = 'Итого к возврату банковской картой'
    elif ticket_sale.paid_qr > 0:
        refund_text = 'Итого к возврату по QR коду'

    context = {'payments': payments, 'sale_id': sale_id, 'refund_text': refund_text}
    return render(request, 'ticket_sales/partials/refund_payment_list.html', context=context)


def refund_payments(request, sale_id):
    if request.method == "POST":
        # Получаем заказ
        ticket_sale = get_object_or_404(TicketSale, pk=sale_id)

        # Парсим JSON-данные из тела запроса
        try:
            data = json.loads(request.body)
            payment_ids = data.get('payments', [])
            print('>>>> payment_ids', payment_ids, 'ticket_sale', ticket_sale)

            # Проверяем, что выбраны оплаты
            if not payment_ids:
                return JsonResponse({'success': False, 'message': 'No payments selected'})

            # Обрабатываем возврат оплат
            payments = TicketSalesPayments.objects.filter(id__in=payment_ids)
            refund_sum = 0
            for payment in payments:
                refund_sum += payment.amount - payment.refund_amount
                payment.refund_amount = payment.amount
                payment.save()

            # Обновляем сумму возврата в заказе
            ticket_sale.refund_amount += refund_sum
            ticket_sale.save()

            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


### БРОНИРОВАНИЕ БИЛЕТОВ

# Create
@csrf_exempt
def ticket_sales_booking_create(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            booking = TicketSalesBooking.objects.create(
                service_id=data['service_id'],
                event_id=data['event_id'],
                event_date=data['event_date'],
                event_time=data['event_time'],
                event_time_end=data.get('event_time_end'),
                tickets_count=data['tickets_count'],
                tickets_amount=data['tickets_amount'],
                discount=data.get('discount', 0),
                total_amount=data['total_amount'],
                booking_guid=data.get('booking_guid', '')
            )
            return JsonResponse({'id': booking.id, 'status': 'created'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=405)  # Method Not Allowed


# Read (list)
def ticket_sales_booking_list(request, booking_guid):
    bookings = TicketSalesBooking.objects.filter(booking_guid=booking_guid).annotate(
        service_name=F('service__name')  # Добавляем название услуги
    ).values(
        'id', 'service_id', 'service_name', 'event_id', 'event_date', 'event_time', 'event_time_end', 'tickets_count',
        'tickets_amount', 'discount', 'total_amount'
    )
    return JsonResponse(list(bookings), safe=False)


# Update
@csrf_exempt
def ticket_sales_booking_update(request, pk):
    booking = get_object_or_404(TicketSalesBooking, pk=pk)
    if request.method == 'PUT':
        data = json.loads(request.body)
        try:
            booking.service_id = data['service_id']
            booking.event_id = data['event_id']
            booking.event_date = data['event_date']
            booking.event_time = data['event_time']
            booking.event_time_end = data.get('event_time_end')
            booking.tickets_count = data['tickets_count']
            booking.tickets_amount = data['tickets_amount']
            booking.discount = data.get('discount', 0)
            booking.total_amount = data['total_amount']
            booking.save()
            return JsonResponse({'id': booking.id, 'status': 'updated'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=405)  # Method Not Allowed


# Delete
@csrf_exempt
def ticket_sales_booking_delete(request, pk):
    booking = get_object_or_404(TicketSalesBooking, pk=pk)
    if request.method == 'DELETE':
        booking.delete()
        return JsonResponse({'status': 'deleted'}, status=200)
    return HttpResponse(status=405)  # Method Not Allowed


# Билеты льготных услуг
@csrf_exempt
def ticket_sales_create_discount_tickets(request, ticket_sale):
    if request.method == 'POST':
        try:
            tickets_count = create_tickets_on_new_payment(ticket_sale, None, 0)
            return JsonResponse({'tickets_count': tickets_count, 'status': 'Ok'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return HttpResponse(status=405)  # Method Not Allowed
