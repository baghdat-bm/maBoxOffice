from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from djangoql.admin import DjangoQLSearchMixin

from .models import EventTemplate, Event, EventTimes, Inventory, Service, EventTemplateServices, SaleType


class EventTemplateServicesAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = EventTemplate

    def has_change_permission(self, request, obj=None):
        return False


class EventTemplateServicesInline(admin.StackedInline):
    model = EventTemplateServices
    extra = 0


class EventTemplateAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = EventTemplate
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    inlines = (EventTemplateServicesInline,)


class EventTimesAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = EventTimes

    def has_change_permission(self, request, obj=None):
        return False


class EventTimesInline(admin.TabularInline):
    model = EventTimes
    extra = 0


class EventAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = Event
    list_display = ('id', 'begin_date', 'end_date', 'quantity')
    list_display_links = ('id', 'begin_date', 'end_date')
    inlines = (EventTimesInline,)


class ServiceAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = Service
    list_display = ('id', 'name', 'on_calculation', 'cost')
    list_display_links = ('id', 'name')
    search_fields = ('name',)


class InventoryAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    model = Inventory
    list_display = ('id', 'name', 'size', 'quantity')
    list_display_links = ('id', 'name')
    search_fields = ('name',)


admin.site.register(EventTemplate, EventTemplateAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(EventTemplateServices, EventTemplateServicesAdmin)
admin.site.register(EventTimes, EventTimesAdmin)
admin.site.register(SaleType)
