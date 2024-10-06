from celery import shared_task
from django.utils import timezone
from .models import TicketSale, TicketSalesBooking
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


@shared_task
def cancel_expired_tickets():
    # Получаем все заказы, у которых истекло время бронирования и не было оплаты
    expired_sales = TicketSale.objects.filter(booking_end_date__lte=timezone.now(), paid_amount=0, status='NP')

    # Обновляем статус для этих заказов
    for ticket_sale in expired_sales:
        ticket_sale.status = 'CN'  # Статус "Отменен"
        ticket_sale.save()

    return f"Отменено {expired_sales.count()} заказов"


@shared_task
def delete_expired_ticket_bookings():
    expired_date = timezone.now() - timedelta(minutes=60)
    # Получаем все брони, у которых истекло время бронирования
    expired_bookings = TicketSalesBooking.objects.filter(created_date__lte=expired_date)

    count = 0
    for booking in expired_bookings:
        booking.delete()
        count += 1

    return f"Удалено {count} броней"
