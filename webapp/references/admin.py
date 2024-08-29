from django.contrib import admin

from .models import EventTemplate, Event, EventTimes, Inventory, Service, EventTemplateServices


class EventTemplateServicesInline(admin.StackedInline):
    model = EventTemplateServices
    extra = 0


class EventTemplateAdmin(admin.ModelAdmin):
    model = EventTemplate
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    inlines = (EventTemplateServicesInline,)


class EventTimesInline(admin.StackedInline):
    model = EventTimes
    extra = 0


class EventAdmin(admin.ModelAdmin):
    model = Event
    list_display = ('id', 'begin_date', 'end_date', 'quantity')
    list_display_links = ('id', 'begin_date', 'end_date')
    inlines = (EventTimesInline,)


admin.site.register(EventTemplate, EventTemplateAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Inventory)
admin.site.register(Service)
