from django.urls import path
from .views import (event_template_create_view, event_template_update_view, event_template_list_view,
                    event_template_detail_view, event_template_delete_view,
                    EventCreateView, EventUpdateView, EventDeleteView, EventDetailView, event_times_create,
                    event_times_update, event_times_delete, EventListView,
                    InventoryListView, InventoryCreateView, InventoryUpdateView, InventoryDeleteView, InventoryDetailView,
                    ServiceListView, ServiceCreateView, ServiceUpdateView, ServiceDeleteView, ServiceDetailView
                    )

app_name = 'references'

urlpatterns = [
    # Event template
    path('event-templates/', event_template_list_view, name='event_template_list'),
    path('event-templates/create/', event_template_create_view, name='event_template_create'),
    path('event-templates/<int:pk>/', event_template_detail_view, name='event_template_detail'),
    path('event-templates/<int:pk>/edit/', event_template_update_view, name='event_template_update'),
    path('event-templates/<int:pk>/delete/', event_template_delete_view, name='event_template_delete'),

    # Event
    path('event/list/', EventListView.as_view(), name='event-list'),
    path('event/create/', EventCreateView.as_view(), name='event-create'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event-update'),
    path('event/<int:pk>/delete/', EventDeleteView.as_view(), name='event-delete'),
    path('event/<int:pk>/', EventDetailView.as_view(), name='event-detail'),

    # EventTimes
    path('event/<int:event_id>/times/create/', event_times_create, name='event-times-create'),
    path('event/<int:event_id>/times/<int:pk>/update/', event_times_update, name='event-times-update'),
    path('event/<int:event_id>/times/<int:pk>/delete/', event_times_delete, name='event-times-delete'),

    # Inventory URLs
    path('inventory/list/', InventoryListView.as_view(), name='inventory-list'),
    path('inventory/create/', InventoryCreateView.as_view(), name='inventory-create'),
    path('inventory/<int:pk>/update/', InventoryUpdateView.as_view(), name='inventory-update'),
    path('inventory/<int:pk>/delete/', InventoryDeleteView.as_view(), name='inventory-delete'),
    path('inventory/<int:pk>/', InventoryDetailView.as_view(), name='inventory-detail'),

    # Service URLs
    path('service/list/', ServiceListView.as_view(), name='service-list'),
    path('service/create/', ServiceCreateView.as_view(), name='service-create'),
    path('service/<int:pk>/update/', ServiceUpdateView.as_view(), name='service-update'),
    path('service/<int:pk>/delete/', ServiceDeleteView.as_view(), name='service-delete'),
    path('service/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
]
