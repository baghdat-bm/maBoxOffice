from rest_framework import serializers


class TicketCheckSerializer(serializers.Serializer):
    ID = serializers.UUIDField()
    event_code = serializers.CharField(max_length=1)
