from django.contrib import admin

from .models import TicketSale, TicketSalesService, TicketSalesPayments


class TicketSalesServiceInline(admin.StackedInline):
    model = TicketSalesService
    extra = 0


class TicketSalesPaymentsInline(admin.StackedInline):
    model = TicketSalesPayments
    extra = 0


class TicketSaleAdmin(admin.ModelAdmin):
    model = TicketSale
    list_display = ('id', 'date', 'amount', 'status')
    list_display_links = ('id', 'date')
    inlines = (TicketSalesServiceInline, TicketSalesPaymentsInline)


admin.site.register(TicketSale, TicketSaleAdmin)
