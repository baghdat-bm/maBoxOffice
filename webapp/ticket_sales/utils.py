from ticket_sales.models import TicketSalesService
from django.db import models


def update_ticket_sale_total(ticket_sale):
    total_amount = TicketSalesService.objects.filter(ticket_sale=ticket_sale).aggregate(total=models.Sum('total_amount'))['total'] or 0
    ticket_sale.amount = total_amount
    ticket_sale.save()
