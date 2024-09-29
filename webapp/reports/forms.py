from django import forms
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from references.models import EventTemplate, Event
from ticket_sales.models import SaleTypeEnum


class SalesReportForm(forms.Form):
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

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Проверяем, что обе даты указаны
        if start_date and end_date:
            # Проверяем, что интервал не превышает 30 дней
            if end_date - start_date > timedelta(days=30):
                raise ValidationError("Интервал дат не может превышать 30 дней.")

        return cleaned_data


class SessionsReportForm(forms.Form):
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
        widget=forms.CheckboxSelectMultiple,  # Use checkboxes instead of a select box
        required=False,
        label='Мероприятие'
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Проверяем, что обе даты указаны
        if start_date and end_date:
            # Проверяем, что интервал не превышает 30 дней
            if end_date - start_date > timedelta(days=30):
                raise ValidationError("Интервал дат не может превышать 30 дней.")

        return cleaned_data


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
        widget=forms.CheckboxSelectMultiple,  # Use checkboxes instead of a select box
        required=False,
        label='Мероприятие'
    )

    def __init__(self, *args, **kwargs):
        super(TicketReportForm, self).__init__(*args, **kwargs)
        self.fields['ticket_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['order_number'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Проверяем, что обе даты указаны
        if start_date and end_date:
            # Проверяем, что интервал не превышает 30 дней
            if end_date - start_date > timedelta(days=30):
                raise ValidationError("Интервал дат не может превышать 30 дней.")

        return cleaned_data
