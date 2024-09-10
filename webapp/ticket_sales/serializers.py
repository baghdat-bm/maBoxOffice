from django.utils import timezone

from rest_framework import serializers


class TicketCheckSerializer(serializers.Serializer):
    ID = serializers.UUIDField()
    event_code = serializers.CharField(max_length=1)


class EventsListSerializer(serializers.Serializer):
    date = serializers.DateField(format='%Y-%m-%d', input_formats=['%Y-%m-%d'])

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Дата не может быть в прошлом.")
        return value
