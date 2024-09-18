import uuid
from datetime import timedelta
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from references.models import Event, Service
from ticket_sales.models import TicketSalesTicket, TicketSalesService, TicketSale
from .tasks import check_booking_expiration


class TicketCheckSerializer(serializers.Serializer):
    ID = serializers.UUIDField()
    event_code = serializers.CharField(max_length=1)


class EventsListSerializer(serializers.Serializer):
    date = serializers.DateField(format='%Y-%m-%d', input_formats=['%Y-%m-%d'])

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Дата не может быть в прошлом.")
        return value


class ServiceListSerializer(serializers.Serializer):
    eventID = serializers.IntegerField()
    date = serializers.DateField(format='%Y-%m-%d', input_formats=['%Y-%m-%d'])

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Дата не может быть в прошлом.")
        return value


class TicketSalesTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSalesTicket
        fields = ['ticket_guid']


class TicketSalesServiceSerializer(serializers.Serializer):
    event_date = serializers.DateField()
    event_time = serializers.TimeField()
    event_time_end = serializers.TimeField(allow_null=True)
    event_id = serializers.IntegerField()
    service_id = serializers.IntegerField()
    count = serializers.IntegerField()

    def create(self, validated_data, ticket_sale=None, event=None, service=None):
        event_date = validated_data['event_date']
        event_time = validated_data['event_time']
        event_time_end = validated_data['event_time_end']
        count = validated_data['count']

        # Создаем услугу для заказа
        service_instance = TicketSalesService.objects.create(
            ticket_sale=ticket_sale,
            service=service,
            event=event,
            event_date=event_date,
            event_time=event_time,
            event_time_end=event_time_end,
            tickets_count=count,
            tickets_amount=service.cost * count,  # Используем стоимость услуги
            total_amount=service.cost * count
        )

        ticket_guids = []
        # Создаем билеты для услуги
        for i in range(count):
            ticket = TicketSalesTicket.objects.create(
                ticket_sale=ticket_sale,
                service=service,
                amount=service.cost,
                number=i + 1,
                event=event,
                event_date=event_date,
                event_time=event_time,
                event_time_end=event_time_end,
                ticket_guid=uuid.uuid4()
            )
            ticket_guids.append(str(ticket.ticket_guid))

        return ticket_guids

    def save(self, **kwargs):
        return self.create(self.validated_data, **kwargs)


class TicketSaleSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True)
    tickets = TicketSalesServiceSerializer(many=True)

    def create(self, validated_data):
        email = validated_data.get('email')
        phone = validated_data.get('phone')
        tickets_data = validated_data.get('tickets')

        # Создаем новый заказ
        booking_begin_date = timezone.now()
        booking_end_date = booking_begin_date + timedelta(minutes=20)

        ticket_sale = TicketSale.objects.create(
            email=email,
            phone=phone,
            booking_begin_date=booking_begin_date,
            booking_end_date=booking_end_date,
            status='NP'  # Начальный статус "Не оплачен"
        )

        total_amount = 0
        ticket_guids = []

        # Создаем услуги и билеты
        for ticket_data in tickets_data:
            # Получаем объекты Event и Service с проверкой существования
            try:
                event = Event.objects.get(id=ticket_data.get('event_id'))
            except Event.DoesNotExist:
                raise ValidationError(f"Event with id {ticket_data.get('event_id')} does not exist.")

            try:
                service = Service.objects.get(id=ticket_data.get('service_id'))
            except Service.DoesNotExist:
                raise ValidationError(f"Service with id {ticket_data.get('service_id')} does not exist.")

            # Передаем ticket_sale, event и service в save() как дополнительные аргументы
            serializer = TicketSalesServiceSerializer(data=ticket_data)
            if serializer.is_valid(raise_exception=True):
                guids = serializer.save(ticket_sale=ticket_sale, event=event, service=service)
                ticket_guids.extend(guids)
                total_amount += service.cost * ticket_data['count']  # Используем поле service.cost

        # Обновляем общую сумму заказа
        ticket_sale.amount = total_amount
        ticket_sale.save()

        # Запуск фоновой задачи через 20 минут
        # check_booking_expiration.apply_async((ticket_sale.id,), countdown=1200)  # 1200 секунд = 20 минут

        return {
            'id': ticket_sale.id,
            'amount': total_amount,
            'booking_begin_date': ticket_sale.booking_begin_date,
            'booking_end_date': ticket_sale.booking_end_date,
            'ticket_guids': ticket_guids
        }


class PaymentDataSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    dateTime = serializers.DateTimeField()  # Поле автоматически преобразует строку в DateTime
    invoiceId = serializers.CharField(max_length=100)
    invoiceIdAlt = serializers.CharField(max_length=100)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    terminal = serializers.UUIDField()
    accountId = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=255)
    language = serializers.CharField(max_length=2)
    cardMask = serializers.CharField(max_length=50)
    cardType = serializers.CharField(max_length=50, required=False, allow_blank=True)
    issuer = serializers.CharField(max_length=100)
    reference = serializers.CharField(max_length=50)
    secure = serializers.CharField(max_length=10)
    tokenRecipient = serializers.CharField(max_length=100, required=False, allow_blank=True)
    code = serializers.CharField(max_length=10)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    reasonCode = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    ip = serializers.IPAddressField()
    ipCountry = serializers.CharField(max_length=100)
    ipCity = serializers.CharField(max_length=100)
    ipRegion = serializers.CharField(max_length=100, required=False, allow_blank=True)
    ipDistrict = serializers.CharField(max_length=100, required=False, allow_blank=True)
    ipLongitude = serializers.FloatField()
    ipLatitude = serializers.FloatField()
    cardId = serializers.UUIDField()
