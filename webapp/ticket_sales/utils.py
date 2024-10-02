import uuid

from django.db.models import Sum

from ticket_sales.helpers import get_num_val
from ticket_sales.models import TicketSalesService, TicketSalesPayments, TerminalSettings, TicketSalesTicket
from django.db import models
import requests
from django.core.cache import cache
from datetime import datetime


def update_ticket_amount(ticket_sale):
    # Получаем общие суммы для total_amount и tickets_count в одном запросе
    totals = TicketSalesService.objects.filter(
        ticket_sale=ticket_sale).aggregate(
        total_amount=models.Sum('total_amount'),
        total_tickets=models.Sum('tickets_count')
    )

    # Устанавливаем значения для ticket_sale
    ticket_sale.amount = totals['total_amount'] or 0
    ticket_sale.tickets_count = totals['total_tickets'] or 0
    ticket_sale.save()


def update_ticket_paid_amount(ticket_sale):
    total_amount = TicketSalesPayments.objects.filter(
        ticket_sale=ticket_sale).aggregate(total=models.Sum('amount'))['total'] or 0
    ticket_sale.paid_amount = total_amount
    ticket_sale.save()


def get_terminal_settings(app_type='CS'):
    data = cache.get("terminal_settings")
    if data is None:
        first_item = TerminalSettings.objects.filter(app_type=app_type).first()
        if first_item:
            data = {
                'ip_address': first_item.ip_address,
                'username': first_item.username,
                'access_token': first_item.access_token,
                'refresh_token': first_item.refresh_token,
                'expiration_date': first_item.expiration_date
            }
            cache.set("terminal_settings", data, 300)
    if not data:
        return None
    return data


def update_terminal_token(terminal_settings):
    ip_address = terminal_settings['ip_address']
    username = terminal_settings['username']
    refresh_token = terminal_settings['refresh_token']

    if not ip_address or not username:
        return {'error': 'Terminal IP address and username are not provided.', 'status': 400}

    url = f"https://{ip_address}:8080/v2/revoke?name={username}&refreshToken={refresh_token}"

    try:
        response = requests.get(url, timeout=10, verify=False)

        if response.status_code == 200:
            response_data = response.json()
            data = response_data['data']

            expiration_date = datetime.strptime(data['expirationDate'], '%b %d, %Y %H:%M:%S')

            settings = TerminalSettings.objects.first()
            if settings:
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
            return {'status': 200, 'data': data}

        elif response.status_code == 500:
            return {'error': response.json().get('message', 'Unknown error'), 'status': 500}
        else:
            return {'error': 'Unknown error occurred during registration.', 'status': response.status_code}
    except requests.exceptions.RequestException as e:
        return {'error': f'Connection error: {str(e)}', 'status': 500}


def create_tickets_on_new_payment(ticket_sale, new_payment, paid_sum):
    # Variable for ticket numbering
    curr_num = 0
    services = TicketSalesService.objects.filter(ticket_sale=ticket_sale)
    if paid_sum == 0:
        services = services.filter(total_amount=0)

    for service in services:
        # Get existing tickets related to this service
        existing_tickets = TicketSalesTicket.objects.filter(
            ticket_sale=ticket_sale,
            service=service.service,
            event=service.event,
            event_date=service.event_date,
            event_time=service.event_time
        )

        # Calculate the total existing amount and count of tickets
        total_existing_amount = existing_tickets.aggregate(amount_sum=Sum('amount'))['amount_sum'] or 0
        total_existing_count = existing_tickets.count()
        curr_num += total_existing_count
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
                service.save()

            # Create additional tickets based on the remaining tickets and amount
            for _ in range(tickets_to_create):
                curr_num += 1
                ticket_amount = remaining_amount // tickets_to_create  # Equal distribution of remaining amount
                try:
                    TicketSalesTicket.objects.create(
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
                except Exception as e:
                    print('>>>>>>> error:', e.__str__())
    return curr_num
