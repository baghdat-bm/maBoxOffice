from django import forms
from django.forms import inlineformset_factory
from crispy_forms.bootstrap import InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, ButtonHolder, Field, Div

from .models import EventTemplate, Event, EventTimes, Inventory, Service, EventTemplateServices


class EventTemplateForm(forms.ModelForm):
    class Meta:
        model = EventTemplate
        fields = ['name', 'logo', 'description']

    def __init__(self, *args, **kwargs):
        super(EventTemplateForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget.attrs.update({'style': 'height:70px;'})


class EventForm(forms.ModelForm):
    begin_date = forms.DateTimeField(
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M'],
        label='Дата начала'
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M'],
        label='Дата окончания'
    )

    class Meta:
        model = Event
        fields = ['event_template', 'begin_date', 'end_date', 'quantity', 'on_monday', 'on_tuesday', 'on_wednesday',
                  'on_thursday', 'on_friday', 'on_saturday', 'on_sunday']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'event_template',
            'begin_date',
            'end_date',
            'quantity',
            Row(
                Div(Field('on_monday'), css_class='d-none'),  # Скрываем поля в общем рендере
                Div(Field('on_tuesday'), css_class='d-none'),
                Div(Field('on_wednesday'), css_class='d-none'),
                Div(Field('on_thursday'), css_class='d-none'),
                Div(Field('on_friday'), css_class='d-none'),
                Div(Field('on_saturday'), css_class='d-none'),
                Div(Field('on_sunday'), css_class='d-none'),
            ),
        )


class EventTimesForm(forms.ModelForm):
    begin_date = forms.TimeField(
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        input_formats=['%H:%M'],
        label='Время начала'
    )
    end_date = forms.TimeField(
        widget=forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        input_formats=['%H:%M'],
        label='Время окончания'
    )

    class Meta:
        model = EventTimes
        fields = ['begin_date', 'end_date', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'size', 'quantity', 'cost']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'cost', 'inventory', 'on_calculation']


class EventTemplateServicesForm(forms.ModelForm):
    class Meta:
        model = EventTemplateServices
        fields = ['service',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].widget.attrs.update({'class': 'form-control'})
