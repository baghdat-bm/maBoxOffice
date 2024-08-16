from django import forms
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, ButtonHolder, Field, Div
from crispy_forms.helper import FormHelper

from .models import TicketSale, TicketSalesService, TicketSalesPayments


class TicketSaleForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        label='Дата'
    )

    class Meta:
        model = TicketSale
        fields = ['date', 'amount', 'status', 'paid_amount', 'refund_amount']


class TicketSalesServiceForm(forms.ModelForm):
    event_date = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        label='Дата мероприятия'
    )
    event_time = forms.TimeField(
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        input_formats=['%H:%M'],
        label='Время мероприятия'
    )

    class Meta:
        model = TicketSalesService
        fields = ['service', 'event', 'event_date', 'event_time', 'inventory', 'inventories_count', 'tickets_count',
                  'tickets_amount', 'discount', 'total_amount']


class TicketSalesPaymentsForm(forms.ModelForm):
    class Meta:
        model = TicketSalesPayments
        fields = ['payment_date', 'payment_method', 'amount', 'process_id', 'last_status', 'error_text',
                  'transaction_id', 'response_data']
