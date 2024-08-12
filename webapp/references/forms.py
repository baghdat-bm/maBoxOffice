from django import forms
from django.forms import inlineformset_factory
from crispy_forms.bootstrap import InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Fieldset, ButtonHolder

from .models import EventTemplate, Event, EventTimes, Inventory, Service


class EventTemplateForm(forms.ModelForm):
    class Meta:
        model = EventTemplate
        fields = ['name', 'logo', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-0'),
                Column('logo', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description',
            Submit('submit', 'Save', css_class='btn btn-primary')
        )


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['event_template', 'begin_date', 'end_date', 'on_monday', 'on_tuesday', 'on_wednesday', 'on_thursday', 'on_friday', 'on_saturday', 'on_sunday']


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


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['event', 'name', 'size', 'quantity', 'cost']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['event', 'name', 'size', 'quantity', 'cost']
