from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from djangoql.admin import DjangoQLSearchMixin
from rangefilter.filters import DateRangeFilterBuilder

from .models import TicketSale, TicketSalesService, TicketSalesPayments, TerminalSettings, \
    TicketSalesTicket, TicketSalesBooking, AppSettings


class TicketSalesServiceInline(admin.StackedInline):
    model = TicketSalesService
    extra = 0
    fields = (
        'service', 'event', 'event_date', 'event_time', 'event_time_end', 'tickets_count', 'tickets_amount',
        'discount', 'total_amount', 'paid_amount')


class TicketSalesServiceAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = TicketSalesService

    def has_change_permission(self, request, obj=None):
        return False


class TicketSalesPaymentsInline(admin.StackedInline):
    model = TicketSalesPayments
    extra = 0


class TicketSalesPaymentsAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = TicketSalesPayments
    list_display = ('id', 'payment_date', 'payment_method', 'amount', 'refund_amount', 'transaction_id', 'process_id',)
    list_filter = (("ticket_sale__date", DateRangeFilterBuilder()), 'ticket_sale__sale_type', 'payment_method')
    search_fields = ('id', 'transaction_id', 'process_id', 'amount', 'payment_date')

    def has_change_permission(self, request, obj=None):
        return False


class TicketSalesTicketInline(admin.StackedInline):
    model = TicketSalesTicket
    extra = 0
    readonly_fields = ('ticket_guid', 'amount', 'is_refund')
    fields = ('service', 'payment', 'event', 'event_date', 'event_time', 'event_time_end', 'amount', 'ticket_guid',
              'last_event_code', 'process_id', 'is_refund', 'refund_amount')


class TicketSalesTicketAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = TicketSalesTicket
    list_display = ('id', 'number', 'event_date', 'event_time', 'payment_method', 'amount', 'refund_amount')
    list_filter = (("ticket_sale__date", DateRangeFilterBuilder()), 'ticket_sale__sale_type', 'event', 'service',)

    def has_change_permission(self, reqsuest, obj=None):
        return False


class TicketSaleAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = TicketSale
    list_display = ('id', 'date', 'amount', 'paid_amount', 'refund_amount', 'tickets_count', 'status', 'sale_type')
    list_display_links = ('id', 'date')
    inlines = (TicketSalesServiceInline, TicketSalesPaymentsInline, TicketSalesTicketInline)
    list_filter = (("date", DateRangeFilterBuilder()), 'status', 'sale_type')


class TerminalSettingsAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = TerminalSettings
    list_display = ('username', 'ip_address', 'port', 'refresh_token', 'expiration_date', 'app_type')
    search_fields = ('username', 'ip_address')

    # def has_add_permission(self, request):
    #     # Разрешить добавление записи, только если её еще нет
    #     return not TerminalSettings.objects.exists()

    # def has_delete_permission(self, request, obj=None):
    #     # Запретить удаление записи
    #     return False


class TicketSalesBookingAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = TicketSalesBooking
    list_display = ('id', 'service', 'event', 'event_date', 'event_time', 'tickets_count', 'total_amount',
                    'created_date')
    list_filter = ('event_date', 'created_date')
    search_fields = ('service__name', 'event__name')


class AppSettingsAdmin(admin.ModelAdmin):
    model = AppSettings

    def has_add_permission(self, request):
        # Разрешить добавление записи, только если её еще нет
        return not AppSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Запретить удаление записи
        return False


admin.site.register(TicketSale, TicketSaleAdmin)
admin.site.register(TerminalSettings, TerminalSettingsAdmin)
admin.site.register(TicketSalesBooking, TicketSalesBookingAdmin)
admin.site.register(TicketSalesService, TicketSalesServiceAdmin)
admin.site.register(TicketSalesPayments, TicketSalesPaymentsAdmin)
admin.site.register(TicketSalesTicket, TicketSalesTicketAdmin)
admin.site.register(AppSettings, AppSettingsAdmin)
