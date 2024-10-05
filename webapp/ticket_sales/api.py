from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import PermissionRequiredMixin
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_200_OK
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import timedelta

from reports.models import HasAvailableEventDatesPermission, HasTicketCheckPermission, HasEventsListPermission, \
    HasServicesListPermission, HasCreateTicketsPermission, HasPaymentInfoPermission
from .models import TicketSalesTicket, TicketSalesPayments, TicketSale
from .serializers import TicketCheckSerializer, EventsListSerializer, ServiceListSerializer, TicketSaleSerializer, \
    PaymentDataSerializer
from .ticket_sale_utils import get_available_events_dates, get_events_data, get_available_services
from .utils import create_tickets_on_new_payment


class TicketCheckView(APIView):
    permission_classes = [IsAuthenticated, HasTicketCheckPermission]

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

        # Разрешаем приход на 10 минут раньше
        early_entry_allowed = event_start - timedelta(minutes=10)
        event_end = ((timezone.make_aware(
            timezone.datetime.combine(ticket.event_date, ticket.event_time_end)))
                     + timedelta(minutes=10)) if ticket.event_time_end else None

        if not (early_entry_allowed <= current_datetime <= event_end):
            return Response({'result': False, 'error_code': '2', 'message': 'Билет не активен по времени мероприятия'},
                            status=HTTP_400_BAD_REQUEST)

        if not ticket.payment or ticket.payment.amount == 0:
            return Response({'result': False, 'error_code': '5', 'message': 'Билет не оплачен'},
                            status=HTTP_400_BAD_REQUEST)

        # 3. Проверка последнего события в зависимости от event_code
        if event_code == "1":  # Вход
            if ticket.last_event_code == "1":
                return Response({'result': False, 'error_code': '3', 'message': 'Билет уже использован для входа'},
                                status=HTTP_400_BAD_REQUEST)
            if ticket.is_refund:
                return Response({'result': False, 'error_code': '4', 'message': 'Билет возвращен'},
                                status=HTTP_400_BAD_REQUEST)
        elif event_code == "0":  # Выход
            if ticket.last_event_code == "0" or ticket.last_event_code is None:
                return Response({'result': False, 'error_code': '5', 'message': 'Билет не был использован для входа'},
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
    permission_classes = [IsAuthenticated, HasAvailableEventDatesPermission]

    def get(self, request, *args, **kwargs):
        available_dates = get_available_events_dates(True)
        return Response({"available_dates": available_dates})


class EventsListView(APIView):
    permission_classes = [IsAuthenticated, HasEventsListPermission]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Дата в формате YYYY-MM-DD",
                type=openapi.TYPE_STRING,
                required=True,
                format='date'
            )
        ],
        responses={200: 'Список сеансов', 400: 'Неверные параметры'},
    )
    def get(self, request, *args, **kwargs):
        serializer = EventsListSerializer(data=request.GET)

        if serializer.is_valid():
            date = serializer.validated_data['date'].strftime('%Y-%m-%d')
            data = get_events_data(date)
            return Response({'events': data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServicesListView(APIView):
    permission_classes = [IsAuthenticated, HasServicesListPermission]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'eventID',
                openapi.IN_QUERY,
                description="ID мероприятия",
                type=openapi.TYPE_STRING,
                required=True,
                format='number'
            ),
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="Дата в формате YYYY-MM-DD",
                type=openapi.TYPE_STRING,
                required=True,
                format='date'
            )
        ],
        responses={200: 'Список услуг', 400: 'Неверные параметры'},
    )
    def get(self, request, *args, **kwargs):
        user_of_sm = request.user.has_perm('reports.access_sm_app')
        user_kp_sm = request.user.has_perm('reports.access_kp_app')
        if user_of_sm or user_kp_sm:
            serializer = ServiceListSerializer(data=request.GET)
            if serializer.is_valid():
                event_id = serializer.validated_data['eventID']
                date = serializer.validated_data['date'].strftime('%Y-%m-%d')
                sale_types = []
                if user_of_sm:
                    sale_types.append('SM')
                if user_kp_sm:
                    sale_types.append('KP')
                data = get_available_services(event_id, date, sale_types)
                return Response({'services': data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)


class CreateTicketSaleAPIView(APIView):
    permission_classes = [IsAuthenticated, HasCreateTicketsPermission]

    @swagger_auto_schema(
        request_body=TicketSaleSerializer,
        responses={
            201: openapi.Response('Заказ успешно создан', TicketSaleSerializer),
            400: 'Неверные параметры запроса'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = TicketSaleSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentDataView(APIView):
    permission_classes = [IsAuthenticated, HasPaymentInfoPermission]

    @swagger_auto_schema(
        request_body=PaymentDataSerializer,
        responses={
            201: openapi.Response('Данные платежа приняты', PaymentDataSerializer),
            400: 'Неверные параметры запроса'
        }
    )
    def post(self, request):
        serializer = PaymentDataSerializer(data=request.data)

        if serializer.is_valid():
            try:
                ticket_sale = TicketSale.objects.filter(id=serializer.validated_data['invoiceId']).first()
            except Exception as e:
                return Response({'error': e.__str__(), 'success': False},
                                status=status.HTTP_400_BAD_REQUEST)
            if not ticket_sale:
                return Response({'error': 'No invoice found with invoiceId', 'success': False},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                new_payment = TicketSalesPayments.objects.get(transaction_id=serializer.validated_data['id'],
                                                              ticket_sale=ticket_sale)
            except TicketSalesPayments.DoesNotExist:
                new_payment = TicketSalesPayments(ticket_sale=ticket_sale,
                                                  transaction_id=serializer.validated_data['id'])
            new_payment.payment_date = serializer.validated_data['dateTime']
            new_payment.payment_method = 'CD'
            new_payment.currency = serializer.validated_data['currency']
            new_payment.description = serializer.validated_data['description']
            new_payment.card_mask = serializer.validated_data['cardMask']
            new_payment.terminal = serializer.validated_data['terminal']
            new_payment.response_data = request.data
            if serializer.validated_data['code'] == 'ok':
                new_payment.amount = serializer.validated_data['amount']
            else:
                new_payment.error_text = {"reason": serializer.validated_data['reason'],
                                          "reasonCode": serializer.validated_data['reasonCode']}
            new_payment.save()

            if new_payment.amount > 0:
                ticket_sale.paid_amount += new_payment.amount
                ticket_sale.paid_card += new_payment.amount
                ticket_sale.save()
                create_tickets_on_new_payment(ticket_sale, new_payment, new_payment.amount)

            return Response({'success': True}, status=status.HTTP_200_OK)

        return Response({'error': serializer.errors, 'success': False},
                        status=status.HTTP_400_BAD_REQUEST)
