from django.contrib import admin

from .models import TicketSale, TicketSalesService, TicketSalesPayments, TicketsSold


class TicketSalesServiceInline(admin.StackedInline):
    model = TicketSalesService
    extra = 0
    readonly_fields = ('ticket_guid',)  # Сделаем поле только для чтения
    fields = (
        'service', 'event', 'event_date', 'event_time', 'tickets_count', 'tickets_amount', 'discount', 'total_amount',
        'ticket_guid')


class TicketSalesPaymentsInline(admin.StackedInline):
    model = TicketSalesPayments
    extra = 0


class TicketsSoldInline(admin.StackedInline):
    model = TicketsSold
    extra = 0


class TicketSaleAdmin(admin.ModelAdmin):
    model = TicketSale
    list_display = ('id', 'date', 'amount', 'status')
    list_display_links = ('id', 'date')
    inlines = (TicketSalesServiceInline, TicketSalesPaymentsInline, TicketsSoldInline)


admin.site.register(TicketSale, TicketSaleAdmin)
