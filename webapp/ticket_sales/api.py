from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_200_OK
from django.utils import timezone
from django.urls import path
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import TicketSalesTicket


class TicketCheckView(APIView):
    # Ограничение доступа только для аутентифицированных пользователей
    permission_classes = [IsAuthenticated]

    # Описание входных параметров для Swagger
    @swagger_auto_schema(
        operation_description="Check the ticket by its GUID and event code.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ID': openapi.Schema(type=openapi.TYPE_STRING, description='Ticket GUID (UUID format)'),
                'event_code': openapi.Schema(type=openapi.TYPE_STRING,
                                             description='Event code ("1" for entry, "0" for exit)', max_length=1),
            },
            required=['ID', 'event_code']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'result': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='The result of the check'),
                },
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'result': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='The result of the check'),
                    'error_code': openapi.Schema(type=openapi.TYPE_STRING, description='Error code'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                },
            ),
        }
    )

    def post(self, request, *args, **kwargs):
        # Получаем параметры из тела запроса
        ticket_guid = request.data.get('ID')  # ID билета
        event_code = request.data.get('event_code')  # Код события (1-вход, 0-выход)

        # Проверка наличия обязательных параметров
        if not ticket_guid or not event_code:
            return Response({'result': False, 'error_code': '1', 'message': 'Отсутствуют параметры ID или event_code'},
                            status=HTTP_400_BAD_REQUEST)

        try:
            # 1. Поиск билета по ticket_guid
            ticket = TicketSalesTicket.objects.get(ticket_guid=ticket_guid)
        except TicketSalesTicket.DoesNotExist:
            return Response({'result': False, 'error_code': '1', 'message': 'Билет не найден'},
                            status=HTTP_404_NOT_FOUND)

        # 2. Проверка даты и времени мероприятия
        current_datetime = timezone.now()
        event_start = timezone.make_aware(timezone.datetime.combine(ticket.event_date, ticket.event_time))
        event_end = timezone.make_aware(
            timezone.datetime.combine(ticket.event_date, ticket.event_time_end)) if ticket.event_time_end else None

        if not (event_start <= current_datetime <= event_end):
            return Response({'result': False, 'error_code': '2', 'message': 'Билет не активен по времени мероприятия'},
                            status=HTTP_400_BAD_REQUEST)

        # 3. Проверка последнего события в зависимости от event_code
        if event_code == "1":  # Вход
            if ticket.last_event_code == "1":
                return Response({'result': False, 'error_code': '3', 'message': 'Билет уже использован для входа'},
                                status=HTTP_400_BAD_REQUEST)
        elif event_code == "0":  # Выход
            if ticket.last_event_code == "0" or ticket.last_event_code is None:
                return Response({'result': False, 'error_code': '3', 'message': 'Билет не был использован для входа'},
                                status=HTTP_400_BAD_REQUEST)
        else:
            return Response({'result': False, 'error_code': '1', 'message': 'Некорректный код события'},
                            status=HTTP_400_BAD_REQUEST)

        # Если все проверки пройдены успешно
        # тогда обновляем статус билета
        ticket.last_event_code = event_code
        ticket.save()

        # Возвращаем успешный ответ
        return Response({'result': True}, status=HTTP_200_OK)


api_urls = [
    path('api/ticket_check/', TicketCheckView.as_view(), name='ticket_check'),
]