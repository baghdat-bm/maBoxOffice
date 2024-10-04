from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseServerError
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from .forms import EventTemplateForm, EventForm, EventTimesForm, InventoryForm, ServiceForm, EventTemplateServicesForm
from .models import Event, EventTemplate, EventTimes, Service, Inventory, EventTemplateServices


def home_page(request):
    return render(request, 'site/home.html')


def event_template_create_view(request):
    if request.method == 'POST':
        form = EventTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('references:event_template_list')
    else:
        form = EventTemplateForm()
    return render(request, 'references/event_template_form.html', {'form': form})


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


def event_template_list_view(request):
    event_templates = EventTemplate.objects.all()
    return render(request, 'references/event_template_list.html', {'event_templates': event_templates})


def event_template_detail_view(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    return render(request, 'references/event_template_detail.html', {'event_template': event_template})


def event_template_delete_view(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    if request.method == 'POST':
        event_template.delete()
        return redirect('references:event_template_list')
    return render(request, 'references/event_template_confirm_delete.html', {'event_template': event_template})


# Event CRUD

class EventListView(ListView):
    model = Event
    # form_class = EventForm
    template_name = 'references/event_list.html'


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'references/event_form.html'
    success_url = reverse_lazy('references:event-list')


class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'references/event_form.html'
    success_url = reverse_lazy('references:event-list')


class EventDeleteView(DeleteView):
    model = Event
    template_name = 'references/event_confirm_delete.html'
    success_url = reverse_lazy('references:event-list')


class EventDetailView(DetailView):
    model = Event
    template_name = 'references/event_detail.html'


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
class InventoryListView(ListView):
    model = Inventory
    template_name = 'references/inventory_list.html'


class InventoryCreateView(CreateView):
    model = Inventory
    form_class = InventoryForm
    template_name = 'references/inventory_form.html'
    success_url = reverse_lazy('references:inventory-list')


class InventoryUpdateView(UpdateView):
    model = Inventory
    form_class = InventoryForm
    template_name = 'references/inventory_form.html'
    success_url = reverse_lazy('references:inventory-list')


class InventoryDeleteView(DeleteView):
    model = Inventory
    template_name = 'references/inventory_confirm_delete.html'
    success_url = reverse_lazy('references:inventory-list')


class InventoryDetailView(DetailView):
    model = Inventory
    template_name = 'references/inventory_detail.html'


# Service Views
class ServiceListView(ListView):
    model = Service
    template_name = 'references/service_list.html'


class ServiceCreateView(CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'references/service_form.html'
    success_url = reverse_lazy('references:service-list')


class ServiceUpdateView(UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'references/service_form.html'
    success_url = reverse_lazy('references:service-list')


class ServiceDeleteView(DeleteView):
    model = Service
    template_name = 'references/service_confirm_delete.html'
    success_url = reverse_lazy('references:service-list')


class ServiceDetailView(DetailView):
    model = Service
    template_name = 'references/service_detail.html'


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
