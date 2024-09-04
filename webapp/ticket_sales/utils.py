from ticket_sales.models import TicketSalesService, TicketSalesPayments, TerminalSettings
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


def get_terminal_settings():
    data = cache.get("terminal_settings")
    if data is None:
        first_item = TerminalSettings.objects.first()
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
