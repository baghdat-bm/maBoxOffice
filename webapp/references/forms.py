from django import forms
from django.forms import inlineformset_factory, CheckboxSelectMultiple
from crispy_forms.bootstrap import InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, ButtonHolder, Field, Div

from .models import EventTemplate, Event, EventTimes, Inventory, Service, EventTemplateServices, SaleType


class EventTemplateForm(forms.ModelForm):
    class Meta:
        model = EventTemplate
        fields = ['name', 'logo', 'description']

    def __init__(self, *args, **kwargs):
        super(EventTemplateForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget.attrs.update({'style': 'height:70px;'})

    def clean_name(self):
        name = self.cleaned_data['name']
        # Check for duplicate names
        if EventTemplate.objects.filter(name=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(f"Мероприятие с наименованием '{name}' уже существует.")
        return name


class EventForm(forms.ModelForm):
    begin_date = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        label='Дата начала'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        label='Дата окончания'
    )

    class Meta:
        model = Event
        fields = ['name', 'event_template', 'begin_date', 'end_date', 'quantity', 'on_monday', 'on_tuesday',
                  'on_wednesday', 'on_thursday', 'on_friday', 'on_saturday', 'on_sunday']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
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

    def clean_name(self):
        name = self.cleaned_data['name']
        # Check for duplicate names
        if Event.objects.filter(name=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(f"Сеанс мероприятия с наименованием '{name}' уже существует.")
        return name


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

    def clean_name(self):
        name = self.cleaned_data['name']
        # Check for duplicate names
        if Inventory.objects.filter(name=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(f"Инвентарь с наименованием '{name}' уже существует.")
        return name


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'cost', 'inventory', 'on_calculation', 'sale_types']
        widgets = {
            'sale_types': CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If the form is used for creating a new instance (no initial sale types)
        if not self.instance.pk:
            # Set all SaleType instances as initial value
            self.fields['sale_types'].initial = SaleType.objects.all()

    def clean_name(self):
        name = self.cleaned_data['name']
        # Check for duplicate names
        if Service.objects.filter(name=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(f"Услуга с наименованием '{name}' уже существует.")
        return name


class EventTemplateServicesForm(forms.ModelForm):
    class Meta:
        model = EventTemplateServices
        fields = ['service',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].widget.attrs.update({'class': 'form-control'})
