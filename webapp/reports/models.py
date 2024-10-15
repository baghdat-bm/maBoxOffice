from django.db import models
from rest_framework.permissions import BasePermission


class Reports(models.Model):
    class Meta:
        permissions = [
            # права на отчеты
            ("view_sales_report", "Может просматривать отчет по продажам"),
            ("view_events_report", "Может просматривать отчет по сеансам"),
            ("view_tickets_report", "Может просматривать отчет реестр билетов"),
            ("view_services_report", "Может просматривать отчет реестр видов услуг"),
            # права на методы API
            ("access_available_event_dates", "Доступ к методу available-event-dates"),
            ("access_events_list", "Доступ к методу events-list"),
            ("access_services_list", "Доступ к методу services-list"),
            ("access_ticket_check", "Доступ к методу ticket-check"),
            ("access_create_tickets", "Доступ к методу create-tickets"),
            ("access_payment_info", "Доступ к методу payment-info"),
            ("access_app_configs", "Доступ к методу app-configs"),
            # права на приложения
            ("access_cs_app", "Доступ к приложению Касса"),
            ("access_ts_app", "Доступ к приложению Кисок"),
            ("access_sm_app", "Доступ к приложению Сайт muzaidyny.kz"),
            ("access_kp_app", "Доступ к приложению Kaspi"),
        ]


class HasAvailableEventDatesPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('reports.access_available_event_dates')


class HasEventsListPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('reports.access_events_list')


class HasServicesListPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('reports.access_services_list')


class HasTicketCheckPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('reports.access_ticket_check')


class HasCreateTicketsPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('reports.access_create_tickets')


class HasPaymentInfoPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('reports.access_payment_info')


class HasAppConfigsPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('reports.access_app_configs')
