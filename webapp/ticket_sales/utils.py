from ticket_sales.models import TicketSalesService, TicketSalesPayments
from django.db import models


def update_ticket_amount(ticket_sale):
    total_amount = TicketSalesService.objects.filter(ticket_sale=ticket_sale).aggregate(total=models.Sum('total_amount'))['total'] or 0
    ticket_sale.amount = total_amount
    ticket_sale.save()


def update_ticket_paid_amount(ticket_sale):
    total_amount = TicketSalesPayments.objects.filter(ticket_sale=ticket_sale).aggregate(total=models.Sum('amount'))['total'] or 0
    ticket_sale.paid_amount = total_amount
    ticket_sale.save()
