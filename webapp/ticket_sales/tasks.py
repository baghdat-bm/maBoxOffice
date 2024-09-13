from celery import shared_task
from django.utils import timezone
from .models import TicketSale
from datetime import timedelta


@shared_task
def check_booking_expiration(ticket_sale_id):
    try:
        ticket_sale = TicketSale.objects.get(id=ticket_sale_id)

        # Проверяем, истекло ли время бронирования и не была ли произведена оплата
        if ticket_sale.booking_end_date <= timezone.now() and ticket_sale.paid_amount == 0:
            ticket_sale.status = 'CN'  # Статус "Отменен"
            ticket_sale.save()
        else:
            print('===============================')
            print('check_booking_expiration called')
            print('ticket_sale.booking_end_date >>', ticket_sale.booking_end_date)
            print('timezone.now() >>', timezone.now())
            print('===============================')

    except TicketSale.DoesNotExist:
        pass  # Заказ не существует
