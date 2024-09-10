from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_200_OK
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import TicketSalesTicket
from .serializers import TicketCheckSerializer
from .ticket_sale_utils import get_available_events_dates


class TicketCheckView(APIView):
    # Ограничение доступа только для аутентифицированных пользователей
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=TicketCheckSerializer,  # Здесь мы указываем, что тело запроса должно соответствовать сериализатору
        responses={200: 'Успешная проверка билета', 400: 'Неверные данные'},  # Пример ответов
    )
    def post(self, request, *args, **kwargs):
        serializer = TicketCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'result': False, 'error_code': '1', 'message': 'Неверные данные'},
                            status=HTTP_400_BAD_REQUEST)

        ticket_guid = serializer.validated_data['ID']
        event_code = serializer.validated_data['event_code']

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


class AvailableDatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        available_dates = get_available_events_dates()
        return Response({"available_dates": available_dates})
