from django import forms
from datetime import date

from references.models import EventTemplate


class TicketReportForm(forms.Form):
    ticket_number = forms.IntegerField(required=False, label='Номер билета')
    order_number = forms.IntegerField(required=False, label='Номер заказа')

    start_date = forms.DateField(
        required=False,
        initial=date.today().strftime('%d-%m-%Y'),  # Текущая дата по умолчанию
        widget=forms.TextInput(attrs={'class': 'form-control datepicker', 'autocomplete': 'off'}),
        label='Начало периода',
        help_text="Выберите начало периода",
        input_formats=['%d-%m-%Y'],  # Указываем формат 'dd-mm-yyyy'
    )

    end_date = forms.DateField(
        required=False,
        initial=date.today().strftime('%d-%m-%Y'),  # Текущая дата по умолчанию
        widget=forms.TextInput(attrs={'class': 'form-control datepicker', 'autocomplete': 'off'}),
        label='Конец периода',
        help_text="Выберите конец периода",
        input_formats=['%d-%m-%Y'],  # Указываем формат 'dd-mm-yyyy'
    )

    event_templates = forms.ModelMultipleChoiceField(
        queryset=EventTemplate.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Мероприятие'
    )

    def __init__(self, *args, **kwargs):
        super(TicketReportForm, self).__init__(*args, **kwargs)
        self.fields['ticket_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['order_number'].widget.attrs.update({'class': 'form-control'})
