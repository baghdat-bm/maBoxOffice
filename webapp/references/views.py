from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseServerError
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin

from .forms import EventTemplateForm, EventForm, EventTimesForm, InventoryForm, ServiceForm, EventTemplateServicesForm
from .models import Event, EventTemplate, EventTimes, Service, Inventory, EventTemplateServices


def home_page(request):
    return render(request, 'site/home.html')


@permission_required('references.add_eventtemplate', raise_exception=True)
def event_template_create_view(request):
    if request.method == 'POST':
        form = EventTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('references:event_template_list')
    else:
        form = EventTemplateForm()
    return render(request, 'references/event_template_form.html', {'form': form})


@permission_required('references.change_eventtemplate', raise_exception=True)
def event_template_update_view(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    if request.method == 'POST':
        form = EventTemplateForm(request.POST, request.FILES, instance=event_template)
        if form.is_valid():
            form.save()
            return redirect('references:event_template_list')
    else:
        form = EventTemplateForm(instance=event_template)
    return render(request, 'references/event_template_form.html', {'form': form})


@permission_required('references.view_eventtemplate', raise_exception=True)
def event_template_list_view(request):
    event_templates = EventTemplate.objects.all()
    return render(request, 'references/event_template_list.html', {'event_templates': event_templates})


@permission_required('references.view_eventtemplate', raise_exception=True)
def event_template_detail_view(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    return render(request, 'references/event_template_detail.html', {'event_template': event_template})


@permission_required('references.delete_eventtemplate', raise_exception=True)
def event_template_delete_view(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    if request.method == 'POST':
        event_template.delete()
        return redirect('references:event_template_list')
    return render(request, 'references/event_template_confirm_delete.html', {'event_template': event_template})


# Event CRUD

class EventListView(PermissionRequiredMixin, ListView):
    model = Event
    # form_class = EventForm
    template_name = 'references/event_list.html'
    permission_required = 'references.view_event'


class EventCreateView(PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'references/event_form.html'
    success_url = reverse_lazy('references:event-list')
    permission_required = 'references.add_event'


class EventUpdateView(PermissionRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'references/event_form.html'
    success_url = reverse_lazy('references:event-list')
    permission_required = 'references.change_event'


class EventDeleteView(PermissionRequiredMixin, DeleteView):
    model = Event
    template_name = 'references/event_confirm_delete.html'
    success_url = reverse_lazy('references:event-list')
    permission_required = 'references.delete_event'


class EventDetailView(PermissionRequiredMixin, DetailView):
    model = Event
    template_name = 'references/event_detail.html'
    permission_required = 'references.view_event'


# EventTimes CRUD via HTMX

def event_times_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = EventTimesForm(request.POST)
        if form.is_valid():
            event_time = form.save(commit=False)
            event_time.event = event
            event_time.save()
            # Возвращаем только список EventTimes, чтобы обновить нужный элемент
            return render(request, 'references/partials/event_times_list.html', {'event': event})
    else:
        form = EventTimesForm()
    return render(request, 'references/partials/event_times_form.html', {'form': form, 'event': event})


def event_times_update(request, event_id, pk):
    event_time = get_object_or_404(EventTimes, id=pk, event_id=event_id)
    if request.method == "POST":
        form = EventTimesForm(request.POST, instance=event_time)
        if form.is_valid():
            form.save()
            return render(request, 'references/partials/event_times_list.html', {'event': event_time.event})
    else:
        form = EventTimesForm(instance=event_time)
    return render(request, 'references/partials/event_times_form.html', {'form': form, 'event': event_time.event})


def event_times_delete(request, event_id, pk):
    event_time = get_object_or_404(EventTimes, id=pk, event_id=event_id)
    if request.method == "POST":
        event = event_time.event
        event_time.delete()
        return render(request, 'references/partials/event_times_list.html', {'event': event})
    return render(request, 'references/partials/event_times_confirm_delete.html', {'event_time': event_time})


# Inventory Views
class InventoryListView(PermissionRequiredMixin, ListView):
    model = Inventory
    template_name = 'references/inventory_list.html'
    permission_required = 'references.view_inventory'


class InventoryCreateView(PermissionRequiredMixin, CreateView):
    model = Inventory
    form_class = InventoryForm
    template_name = 'references/inventory_form.html'
    success_url = reverse_lazy('references:inventory-list')
    permission_required = 'references.add_inventory'


class InventoryUpdateView(PermissionRequiredMixin, UpdateView):
    model = Inventory
    form_class = InventoryForm
    template_name = 'references/inventory_form.html'
    success_url = reverse_lazy('references:inventory-list')
    permission_required = 'references.change_inventory'


class InventoryDeleteView(PermissionRequiredMixin, DeleteView):
    model = Inventory
    template_name = 'references/inventory_confirm_delete.html'
    success_url = reverse_lazy('references:inventory-list')
    permission_required = 'references.delete_inventory'


class InventoryDetailView(PermissionRequiredMixin, DetailView):
    model = Inventory
    template_name = 'references/inventory_detail.html'
    permission_required = 'references.view_inventory'


# Service Views
class ServiceListView(PermissionRequiredMixin, ListView):
    model = Service
    template_name = 'references/service_list.html'
    permission_required = 'references.view_service'


class ServiceCreateView(PermissionRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'references/service_form.html'
    success_url = reverse_lazy('references:service-list')
    permission_required = 'references.add_service'


class ServiceUpdateView(PermissionRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'references/service_form.html'
    success_url = reverse_lazy('references:service-list')
    permission_required = 'references.change_service'


class ServiceDeleteView(PermissionRequiredMixin, DeleteView):
    model = Service
    template_name = 'references/service_confirm_delete.html'
    success_url = reverse_lazy('references:service-list')
    permission_required = 'references.delete_service'


class ServiceDetailView(PermissionRequiredMixin, DetailView):
    model = Service
    template_name = 'references/service_detail.html'
    permission_required = 'references.view_service'


def event_template_service_create(request, event_template_id):
    event_template = get_object_or_404(EventTemplate, pk=event_template_id)

    if request.method == 'POST':
        form = EventTemplateServicesForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.event_template = event_template
            try:
                service.save()
            except Exception as e:
                messages.error(request, "Не удалось добавить услугу, возможно услуга уже добавлена")
            return render(request, 'references/partials/event_template_services_list.html',
                          {'event_template': event_template})

    form = EventTemplateServicesForm()
    return render(request, 'references/partials/event_template_service_form.html', {'form': form, 'event_template': event_template})


def event_template_service_update(request, event_template_id, pk):
    service = get_object_or_404(EventTemplateServices, id=pk, event_template_id=event_template_id)
    if request.method == 'POST':
        form = EventTemplateServicesForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return render(request, 'references/partials/event_template_services_list.html', {'event_template': service.event_template})
    else:
        form = EventTemplateServicesForm(instance=service)

    return render(request, 'references/partials/event_template_service_form.html', {'form': form, 'event_template': service.event_template})


def event_template_service_delete(request, event_template_id, pk):
    service = get_object_or_404(EventTemplateServices, id=pk, event_template_id=event_template_id)

    if request.method == 'POST':
        event_template = service.event_template
        service.delete()
        # return redirect('references:event_template_update', pk=event_template_id)
        return render(request, 'references/partials/event_template_services_list.html',
                      {'event_template': event_template})

    return render(request, 'references/partials/event_template_service_confirm_delete.html',
                  {'service': service})
