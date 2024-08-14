import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import TicketSale, TicketSalesService, TicketSalesPayments
from .forms import TicketSaleForm, TicketSalesServiceForm, TicketSalesPaymentsForm
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView, ListView


# TicketSale Views

class TicketSaleListView(ListView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_list.html'


class TicketSaleCreateView(CreateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


class TicketSaleUpdateView(UpdateView):
    model = TicketSale
    form_class = TicketSaleForm
    template_name = 'ticket_sales/ticket_sale_form.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


class TicketSaleDetailView(DetailView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_detail.html'


class TicketSaleDeleteView(DeleteView):
    model = TicketSale
    template_name = 'ticket_sales/ticket_sale_confirm_delete.html'
    success_url = reverse_lazy('ticket_sales:ticket-sale-list')


# TicketSalesService HTMX Views

def ticket_sales_service_create(request, ticket_sale_id):
    ticket_sale = get_object_or_404(TicketSale, id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.ticket_sale = ticket_sale
            service.save()
            return render(request, 'ticket_sales/partials/ticket_sales_service_list.html', {'ticket_sale': ticket_sale})
    else:
        form = TicketSalesServiceForm()
    return render(request, 'ticket_sales/partials/ticket_sales_service_form.html', {'form': form, 'ticket_sale': ticket_sale})


def ticket_sales_service_update(request, ticket_sale_id, pk):
    service = get_object_or_404(TicketSalesService, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return render(request, 'ticket_sales/partials/ticket_sales_service_list.html',
                          {'ticket_sale': service.ticket_sale})
    else:
        form = TicketSalesServiceForm(instance=service)
    return render(request, 'ticket_sales/partials/ticket_sales_service_form.html', {'form': form})


def ticket_sales_service_delete(request, ticket_sale_id, pk):
    service = get_object_or_404(TicketSalesService, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        service.delete()
        return render(request, 'ticket_sales/partials/ticket_sales_service_list.html',
                      {'ticket_sale': service.ticket_sale})
    return render(request, 'ticket_sales/partials/ticket_sales_service_confirm_delete.html', {'service': service})


# TicketSalesPayments HTMX Views

def ticket_sales_payments_create(request, ticket_sale_id):
    ticket_sale = get_object_or_404(TicketSale, id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesPaymentsForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.ticket_sale = ticket_sale
            payment.save()
            return render(request, 'ticket_sales/partials/ticket_sales_payments_list.html',
                          {'ticket_sale': ticket_sale})
    else:
        form = TicketSalesPaymentsForm()
    return render(request, 'ticket_sales/partials/ticket_sales_payments_form.html', {'form': form, 'ticket_sale': ticket_sale})


def ticket_sales_payments_update(request, ticket_sale_id, pk):
    payment = get_object_or_404(TicketSalesPayments, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        form = TicketSalesPaymentsForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return render(request, 'ticket_sales/partials/ticket_sales_payments_list.html',
                          {'ticket_sale': payment.ticket_sale})
    else:
        form = TicketSalesPaymentsForm(instance=payment)
    return render(request, 'ticket_sales/partials/ticket_sales_payments_form.html', {'form': form})


def ticket_sales_payments_delete(request, ticket_sale_id, pk):
    payment = get_object_or_404(TicketSalesPayments, id=pk, ticket_sale_id=ticket_sale_id)
    if request.method == "POST":
        payment.delete()
        return render(request, 'ticket_sales/partials/ticket_sales_payments_list.html',
                      {'ticket_sale': payment.ticket_sale})
    return render(request, 'ticket_sales/partials/ticket_sales_payments_confirm_delete.html', {'payment': payment})


def payment_process(request, ticket_sale_id, payment_id):
    payment = TicketSalesPayments.objects.get(ticket_sale_id=ticket_sale_id, id=payment_id)
    payload = {
        'amount': payment.accepted_amount,
        'method': payment.payment_method,
        # добавьте другие необходимые данные
    }

    try:
        response = requests.post('http://localhost:8080/payment', json=payload)
        response_data = response.json()
        if response.status_code == 200 and response_data.get('status') == 'success':
            payment.process_id = response_data.get('process_id')
            payment.save()
            return JsonResponse({'status': 'success', 'process_id': payment.process_id})
        else:
            return JsonResponse({'status': 'fail'})
    except requests.RequestException:
        return JsonResponse({'status': 'fail'})


def check_payment_status(request, process_id=None):
    try:
        response = requests.get(f'http://localhost:8080/status/{process_id}')
        return JsonResponse(response.json())
    except requests.RequestException:
        return JsonResponse({'status': 'fail'})
