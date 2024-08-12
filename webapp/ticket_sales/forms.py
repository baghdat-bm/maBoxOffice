from django import forms
from .models import TicketSale, TicketSalesService, TicketSalesPayments


class TicketSaleForm(forms.ModelForm):
    class Meta:
        model = TicketSale
        fields = ['date', 'amount', 'status']


class TicketSalesServiceForm(forms.ModelForm):
    class Meta:
        model = TicketSalesService
        fields = ['service', 'event', 'event_date', 'event_time', 'inventory', 'inventories_count', 'tickets_count',
                  'tickets_amount', 'discount', 'total_amount']


class TicketSalesPaymentsForm(forms.ModelForm):
    class Meta:
        model = TicketSalesPayments
        fields = ['payment_date', 'payment_method', 'accepted_from_the_buyer', 'amount_of_change',
                  'accepted_amount', 'process_id', 'last_status', 'error_text', 'transaction_id', 'response_data']
