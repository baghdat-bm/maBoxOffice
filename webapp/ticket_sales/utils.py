import uuid
from django.utils import timezone
from django.db.models import Sum
from django.db import models
import requests
from django.core.cache import cache
from datetime import datetime

from ticket_sales.helpers import get_num_val
from ticket_sales.models import TicketSalesService, TicketSalesPayments, TerminalSettings, TicketSalesTicket, TicketSale


def update_ticket_amount(request, ticket_sale):
    # Получаем общие суммы для total_amount и tickets_count в одном запросе
    totals = TicketSalesService.objects.filter(
        ticket_sale=ticket_sale).aggregate(
        total_amount=models.Sum('total_amount'),
        total_tickets=models.Sum('tickets_count')
    )

    # Устанавливаем значения для ticket_sale
    ticket_sale.amount = totals['total_amount'] or 0
    ticket_sale.tickets_count = totals['total_tickets'] or 0
    ticket_sale.save(update_date=True, user=request.user)


def update_ticket_paid_amount(request, ticket_sale):
    total_amount = TicketSalesPayments.objects.filter(
        ticket_sale=ticket_sale).aggregate(total=models.Sum('amount'))['total'] or 0
    ticket_sale.paid_amount = total_amount
    ticket_sale.save(user=request.user)


def get_terminal_settings(request, app_type='CS'):
    data = cache.get(f"terminal_settings_{app_type}")
    if data is None:
        first_item = TerminalSettings.objects.filter(app_type=app_type).first()
        if first_item:
            data = {
                'ip_address': first_item.ip_address,
                'port': first_item.port,
                'use_https': first_item.use_https,
                'username': first_item.username,
                'access_token': first_item.access_token,
                'refresh_token': first_item.refresh_token,
                'expiration_date': first_item.expiration_date
            }
            cache.set(f"terminal_settings_{app_type}", data, 300)

    # Проверяем, если настройки были найдены и не истек ли токен
    if data and data['expiration_date']:
        expiration_date = data['expiration_date']
        if expiration_date <= timezone.now():
            # Получаем объект настроек терминала для обновления токена
            first_item = TerminalSettings.objects.filter(app_type=app_type).first()
            if first_item:
                data = {
                    'ip_address': first_item.ip_address,
                    'port': first_item.port,
                    'use_https': first_item.use_https,
                    'username': first_item.username,
                    'access_token': first_item.access_token,
                    'refresh_token': first_item.refresh_token,
                    'expiration_date': first_item.expiration_date,
                    'app_type': app_type
                }
                update_terminal_token(request, data)

    if not data:
        return None
    return data


def update_terminal_token(request, terminal_settings):
    ip_address = terminal_settings['ip_address']
    port = terminal_settings['port']
    use_https = terminal_settings['use_https']
    username = terminal_settings['username']
    refresh_token = terminal_settings['refresh_token']
    app_type = terminal_settings['app_type']

    if not ip_address or not username:
        return {'error': 'Terminal IP address or Username are not provided.', 'status': 400}

    if not port or not refresh_token:
        return {'error': 'Port or refresh token are not provided.', 'status': 400}

    protocol = 'https' if use_https else 'http'
    url = f"{protocol}://{ip_address}:{port}/v2/revoke?name={username}&refreshToken={refresh_token}"

    print('refreshToken url>>>>>')
    print(url)
    try:
        response = requests.get(url, timeout=40, verify=False)

        if response.status_code == 200:
            response_data = response.json()
            data = response_data['data']

            # expiration_date = datetime.strptime(data['expirationDate'], '%b %d, %Y %H:%M:%S')
            expiration_date = datetime.strptime(data['expirationDate'], '%Y-%m-%d %H:%M:%S')
            settings = TerminalSettings.objects.filter(app_type=app_type).first()
            if settings:
                settings.access_token = data['accessToken']
                settings.refresh_token = data['refreshToken']
                settings.expiration_date = expiration_date
                settings.ip_address = ip_address
                settings.port = port
                settings.use_https = use_https
            else:
                settings = TerminalSettings(
                    app_type=app_type,
                    ip_address=ip_address,
                    port=port,
                    use_https=use_https,
                    username=username,
                    access_token=data['accessToken'],
                    refresh_token=data['refreshToken'],
                    expiration_date=expiration_date,
                )
            settings.save(user=request.user)
            terminal_settings['access_token'] = data['accessToken']
            terminal_settings['refresh_token'] = data['refreshToken']
            terminal_settings['expiration_date'] = expiration_date
            return {'status': 200, 'data': data}

        elif response.status_code == 500:
            return {'error': response.json().get('message', 'Unknown error'), 'status': 500}
        else:
            return {'error': 'Unknown error occurred during registration.', 'status': response.status_code}
    except requests.exceptions.RequestException as e:
        return {'error': f'Connection error: {str(e)}', 'status': 500}


def create_tickets_on_new_payment(request, ticket_sale, new_payment, paid_sum):
    # Variable for ticket numbering
    curr_num = TicketSalesTicket.objects.filter(ticket_sale=ticket_sale).count()
    services = TicketSalesService.objects.filter(ticket_sale=ticket_sale)
    if paid_sum == 0:
        services = services.filter(total_amount=0)

    created_tickets = []
    for service in services:
        # Получаем список id созданных билетов
        created_ticket_ids = [ticket.id for ticket in created_tickets]

        # Get existing tickets related to this service
        existing_tickets = TicketSalesTicket.objects.filter(
            ticket_sale=ticket_sale,
            service=service.service,
            event=service.event,
            event_date=service.event_date,
            event_time=service.event_time
        ).exclude(id__in=created_ticket_ids)

        # Calculate the total existing amount and count of tickets
        total_existing_amount = existing_tickets.aggregate(amount_sum=Sum('amount'))['amount_sum'] or 0
        total_existing_count = existing_tickets.count()

        # Check if tickets need to be created
        if total_existing_amount < service.tickets_amount or total_existing_count < service.tickets_count:
            # Calculate how many more tickets need to be created
            tickets_to_create = service.tickets_count - total_existing_count
            remaining_amount = service.tickets_amount - total_existing_amount

            # Update the paid amount for the service
            payment_amount = get_num_val(service.paid_amount)
            payment_sum = service.total_amount - payment_amount
            paid_amount = payment_amount + min(paid_sum, payment_sum)
            if service.paid_amount != paid_amount:
                service.paid_amount = paid_amount
                service.save(user=request.user)

            # Create additional tickets based on the remaining tickets and amount
            for _ in range(tickets_to_create):
                curr_num += 1
                ticket_amount = remaining_amount // tickets_to_create  # Equal distribution of remaining amount
                try:
                    new_ticket = TicketSalesTicket(
                        ticket_sale=ticket_sale,
                        service=service.service,
                        event=service.event,
                        event_date=service.event_date,
                        event_time=service.event_time,
                        event_time_end=service.event_time_end,
                        amount=ticket_amount,
                        ticket_guid=uuid.uuid4(),  # Generate a new unique GUID
                        number=curr_num,
                        payment=new_payment
                    )
                    new_ticket.save(user=request.user)
                    created_tickets.append(new_ticket)
                except Exception as e:
                    print('>>>>>>> error:', e.__str__())

    if len(services) > 0:
        ticket_sale.tickets_count = curr_num
        if paid_sum == 0 and ticket_sale.paid_amount == 0:
            ticket_sale.status = 'IS'
            ticket_sale.save(update_status=False, user=request.user)
        else:
            ticket_sale.save(user=request.user)

    return curr_num


def refund_tickets_on_refund(request, ticket_sale, refund_payment, refund_amount):
    tickets = TicketSalesTicket.objects.filter(ticket_sale=ticket_sale, payment=refund_payment)
    tickets_count = 0
    refund_amount_remain = refund_amount
    ticket_ids = []
    for ticket in tickets:
        ticket_refund_amount = min(ticket.amount - ticket.refund_amount, refund_amount)
        ticket.refund_amount += ticket_refund_amount
        ticket.is_refund = True
        ticket.save(user=request.user)
        ticket_ids.append(ticket.id)
        refund_amount_remain -= ticket_refund_amount
        tickets_count += 1
        if ticket_refund_amount == 0:
            break

    ticket_sale.refund_amount += refund_amount - refund_amount_remain
    ticket_sale.save(update_date=False, user=request.user)

    return ticket_ids
