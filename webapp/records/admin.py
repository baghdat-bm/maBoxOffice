from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from djangoql.admin import DjangoQLSearchMixin
import json
from django.utils.safestring import mark_safe

from records.models import RecordChangeLog


class LoggableAdmin(DjangoQLSearchMixin, ImportExportActionModelAdmin):
    def save_model(self, request, obj, form, change):
        # Передаем пользователя при сохранении
        obj.save(user=request.user)

    def delete_model(self, request, obj):
        # Передаем пользователя при удалении
        obj.delete(user=request.user)


@admin.register(RecordChangeLog)
class RecordChangeLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'table_name', 'id')
    list_display_links = ('timestamp',)
    fields = ('record_id', 'user', 'action', 'version', 'timestamp', 'table_name', 'formatted_changes')

    def has_change_permission(self, request, obj=None):
        # Запретить изменение записи
        return False

    def has_add_permission(self, request):
        # Запретить добавление записи
        return False

    def has_delete_permission(self, request, obj=None):
        # Запретить удаление записи
        return False

    def formatted_changes(self, obj):
        if obj.changes:
            formatted_json = json.dumps(obj.changes, indent=4, ensure_ascii=False)
            return mark_safe(f'<pre>{formatted_json}</pre>')
        return "-"

    formatted_changes.short_description = "Изменённые данные"
