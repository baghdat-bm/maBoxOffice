from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
import json
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_naive, is_aware


class RecordChangeLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Создание'),
        ('updated', 'Изменение'),
        ('deleted', 'Удаление'),
    ]

    record_id = models.CharField(max_length=255, verbose_name="Идентификатор записи")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Тип события")
    changes = models.JSONField(null=True, blank=True, verbose_name="Измененные данные")
    version = models.PositiveIntegerField(verbose_name="Версия записи", default=1)
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Дата и время события")
    table_name = models.CharField(max_length=255, verbose_name="Название таблицы", blank=True)

    class Meta:
        verbose_name = "Лог изменений записи"
        verbose_name_plural = "Логи изменений записей"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Record {self.record_id} - {self.get_action_display()} - Version {self.version}"


class LoggableModelMixin(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        user = kwargs.pop('user', None)

        action = 'created' if is_new else 'updated'
        changes = None
        version = 1

        if not is_new:
            # Получаем изменения
            changes = self.get_changed_fields()
            if not changes:
                # Пропускаем, если нет изменений
                return

            # Получаем последнюю версию из логов
            last_log = RecordChangeLog.objects.filter(record_id=self.pk).order_by('-version').first()
            if last_log:
                version = last_log.version + 1

        super().save(*args, **kwargs)

        RecordChangeLog.objects.create(
            record_id=self.pk,
            user=user,
            action=action,
            changes=changes,
            version=version,
            table_name=self._meta.verbose_name
        )

    def delete(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        last_log = RecordChangeLog.objects.filter(record_id=self.pk).order_by('-version').first()
        version = last_log.version + 1 if last_log else 1

        RecordChangeLog.objects.create(
            record_id=self.pk,
            user=user,
            action='deleted',
            version=version,
            table_name=self._meta.verbose_name
        )
        super().delete(*args, **kwargs)

    def get_changed_fields(self):
        try:
            old_instance = self.__class__.objects.get(pk=self.pk)
        except ObjectDoesNotExist:
            return None

        changes = {}
        for field in self._meta.fields:
            field_name = field.name
            old_value = getattr(old_instance, field_name)
            new_value = getattr(self, field_name)

            # Приведение обоих значений к одинаковому типу для корректного сравнения
            if isinstance(old_value, datetime) and isinstance(new_value, str):
                new_value = parse_datetime(new_value)

            # Приведение к "наивному" времени без временной зоны для корректного сравнения
            if isinstance(old_value, datetime) and isinstance(new_value, datetime):
                if is_aware(old_value):
                    old_value = make_naive(old_value)  # Убираем информацию о временной зоне
                if is_aware(new_value):
                    new_value = make_naive(new_value)

            if old_value != new_value:
                # Форматирование изменений: старое значение >> новое значение
                changes[field_name] = f"{self.serialize_value(old_value)} => {self.serialize_value(new_value)}"

        return changes

    @staticmethod
    def serialize_value(value):
        if isinstance(value, datetime):
            return value.isoformat()  # Преобразуем datetime в строку
        if isinstance(value, models.Model):
            return str(value)  # Преобразуем внешние ключи в строку
        # Добавьте другие типы данных, если требуется
        return value
