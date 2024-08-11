from django.contrib import admin

from .models import EventTemplate, Event, EventTimes, Inventory, Service


class EventTemplateAdmin(admin.ModelAdmin):
    model = EventTemplate
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)


class EventTimesInline(admin.StackedInline):
    model = EventTimes
    extra = 0


class InventoryInline(admin.StackedInline):
    model = Inventory
    extra = 0


class ServiceInline(admin.StackedInline):
    model = Service
    extra = 0


class EventAdmin(admin.ModelAdmin):
    model = Event
    list_display = ('id', 'begin_date', 'end_date')
    inlines = (EventTimesInline, InventoryInline, ServiceInline)


admin.site.register(EventTemplate, EventTemplateAdmin)
admin.site.register(Event, EventAdmin)
