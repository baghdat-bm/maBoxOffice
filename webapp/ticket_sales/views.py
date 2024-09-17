import json
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
import re

import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt

from references.models import Event, EventTimes, EventTemplateServices, Service
from .models import TicketSale, TicketSalesService, TicketSalesPayments, TerminalSettings, TicketSalesTicket, \
    SaleTypeEnum
from .forms import TicketSaleForm, TicketSalesServiceForm, TicketSalesPaymentsForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView

from .ticket_sale_utils import get_available_events_dates, get_events_data, get_filtered_services
from .utils import update_ticket_amount, update_ticket_paid_amount, get_terminal_settings, update_terminal_token


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


class TicketSaleCreateView(CreateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


def create_ticket_sale_cashier(request):
    # Создаем новую запись TicketSale
    ticket_sale = TicketSale.objects.create(sale_type=SaleTypeEnum.CS.value[0])

    # Перенаправляем на страницу редактирования
    return redirect(reverse('ticket_sales:ticket-sale-update', kwargs={'pk': ticket_sale.pk}))


class TicketSaleUpdateView(UpdateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


def home_page_terminal(request):
    return render(request, 'terminal/home.html')


@csrf_exempt
def create_ticket_sale_terminal(request):
    # Создаем новую запись TicketSale
    ticket_sale = TicketSale.objects.create(sale_type=SaleTypeEnum.TS.value[0])

    # Перенаправляем на страницу редактирования
    return redirect(reverse('ticket_sales:ticket-sale-update-t', kwargs={'pk': ticket_sale.pk}))


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


def payment_process(request, ticket_sale_id):
    ticket_sale = TicketSale.objects.get(id=ticket_sale_id)
    terminal = get_terminal_settings()
    if not terminal:
        return JsonResponse({'status': 'fail', 'message': 'terminal is not set'}, status=400)
    try:
        headers = {'accesstoken': terminal['access_token']}
        response = requests.get(f'https://{terminal['ip_address']}:8080/payment?amount={ticket_sale.amount}',
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
        response = requests.get(f'https://{terminal['ip_address']}:8080/payment?amount={ticket_sale.amount}',
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


def check_payment_status(request, process_id, ticket_sale_id):
    terminal = get_terminal_settings()
    if not terminal:
        return JsonResponse({'status': 'fail', 'message': 'terminal is not set'}, status=400)
    try:
        headers = {'accesstoken': terminal['access_token']}
        response = requests.get(f'https://{terminal['ip_address']}:8080/status?processId={process_id}',
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
        response = requests.get(f'https://{terminal['ip_address']}:8080/status?processId={process_id}',
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

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'})


# печать заказа
@csrf_exempt
def print_ticket_view(request, ticket_sale_id):
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
def filtered_services(request):
    event_id = request.GET.get('event_id')
    data = get_filtered_services(event_id)
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
            return redirect('ticket_sales:terminal-settings')

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
            return redirect('ticket_sales:terminal-settings')

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

        # Парсим JSON-данные из тела запроса
        try:
            data = json.loads(request.body)
            ticket_ids = data.get('tickets', [])
            print('>>>> ticket_ids', ticket_ids, 'ticket_sale', ticket_sale)

            # Проверяем, что выбраны билеты
            if not ticket_ids:
                return JsonResponse({'success': False, 'message': 'No tickets selected'})

            # Обрабатываем возврат билетов
            tickets = TicketSalesTicket.objects.filter(id__in=ticket_ids, is_refund=False)
            refund_sum = sum(ticket.amount for ticket in tickets)
            print('>>>> refund_sum', refund_sum)

            # Обновляем билеты
            tickets.update(is_refund=True)

            # Обновляем сумму возврата в заказе
            ticket_sale.refund_amount += refund_sum
            ticket_sale.save()

            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})
