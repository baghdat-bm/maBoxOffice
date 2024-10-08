from django import forms

from .models import TicketSale, TicketSalesService, TicketSalesPayments, TicketSalesBooking


class TicketSaleForm(forms.ModelForm):
    class Meta:
        model = TicketSale
        fields = ['date', 'time', 'amount', 'tickets_count', 'status', 'paid_amount', 'refund_amount', 'paid_cash',
                  'paid_card', 'paid_qr', 'sale_type', 'email', 'phone', 'booking_begin_date', 'booking_end_date']
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }


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
        fields = ['service', 'event', 'event_date', 'event_time', 'event_time_end', 'tickets_count', 'tickets_amount',
                  'discount', 'total_amount', 'paid_amount']


class TicketSalesPaymentsForm(forms.ModelForm):
    class Meta:
        model = TicketSalesPayments
        fields = ['payment_date', 'payment_method', 'amount', 'refund_amount', 'process_id', 'last_status',
                  'error_text', 'transaction_id', 'response_data', 'currency', 'description', 'card_mask',
                  'terminal', 'refund_transaction_id']


class TicketSalesBookingForm(forms.ModelForm):
    class Meta:
        model = TicketSalesBooking
        fields = ['service', 'event', 'event_date', 'event_time', 'event_time_end', 'tickets_count', 'tickets_amount',
                  'discount', 'total_amount']
