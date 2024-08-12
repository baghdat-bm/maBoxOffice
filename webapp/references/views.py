from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseServerError
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from .forms import EventTemplateForm, EventForm, EventTimesForm
from .models import Event, EventTemplate, EventTimes


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
        event_time.delete()
        return render(request, 'references/partials/event_times_list.html', {'event': event_time.event})
    return render(request, 'references/partials/event_times_confirm_delete.html', {'event_time': event_time})
