from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Sum, Q

from references.models import Event, EventTimes, EventTemplateServices
from ticket_sales.models import TicketSalesService


def get_available_events_dates(include_tickets=False):
    events = Event.objects.all()
    available_dates = []

    # Функция для проверки, включен ли день недели для данного мероприятия
    def is_day_included(event, date):
        day_of_week = date.weekday()  # Получаем день недели (0 - понедельник, 6 - воскресенье)
        return (
                (day_of_week == 0 and event.on_monday) or
                (day_of_week == 1 and event.on_tuesday) or
                (day_of_week == 2 and event.on_wednesday) or
                (day_of_week == 3 and event.on_thursday) or
                (day_of_week == 4 and event.on_friday) or
                (day_of_week == 5 and event.on_saturday) or
                (day_of_week == 6 and event.on_sunday)
        )

    # Определяем диапазон дат: сегодня и +30 дней
    today = timezone.now().date()
    date_limit = today + timedelta(days=30)

    # Итерация по каждому мероприятию
    for event in events:
        start_date = event.begin_date
        end_date = event.end_date

        # Убедимся, что конец мероприятия не превышает наш лимит +30 дней
        if end_date > date_limit:
            end_date = date_limit

        # Проходим по всем датам от начала до конца мероприятия
        for day in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=day)

            # Проверяем, включен ли текущий день недели для данного мероприятия
            # и входит ли дата в диапазон [сегодня, сегодня + 30 дней]
            if today <= current_date <= date_limit and is_day_included(event, current_date):

                if include_tickets:
                    # Преобразование даты в строку, если это необходимо для фильтрации
                    current_date_str = current_date.isoformat()

                    # Подсчет проданных билетов для данного мероприятия на текущую дату
                    sold_tickets = TicketSalesService.objects.filter(
                        event=event,
                        event_date=current_date_str,  # Преобразование текущей даты в строку, если это необходимо
                        service__on_calculation=True
                    ).aggregate(total_sold_tickets=Sum('tickets_count'))

                    # Извлекаем сумму проданных билетов или используем 0, если билеты не продавались
                    sold_tickets_count = sold_tickets['total_sold_tickets'] or 0

                    # Вычисляем доступное количество билетов
                    available_quantity = event.quantity - sold_tickets_count

                    # Добавляем дату и количество доступных билетов в список
                    available_dates.append({
                        'date': current_date,
                        'available_tickets': available_quantity
                    })
                else:
                    available_dates.append(current_date)

    # Удаление дубликатов и сортировка по дате
    if include_tickets:
        available_dates = sorted(available_dates, key=lambda x: x['date'])
    else:
        available_dates = sorted(list(set(available_dates)))

    return available_dates


def get_events_data(date):
    date_naive = datetime.strptime(date, '%Y-%m-%d')
    selected_date = timezone.make_aware(datetime.combine(date_naive, datetime.min.time()))
    events = Event.objects.filter(begin_date__lte=selected_date, end_date__gte=selected_date)
    data = []

    for event in events:
        times = EventTimes.objects.filter(event=event)
        event_data = {
            'id': event.id,
            'name': event.name,
            # 'quantity': event.quantity,
            'times': []
        }

        for time in times:
            # Получаем записи TicketSalesService для текущего мероприятия и времени
            sold_tickets = TicketSalesService.objects.filter(
                event=event,
                event_time=time.begin_date,
                event_time_end=time.end_date,
                service__on_calculation=True
            ).aggregate(total_sold_tickets=Sum('tickets_count'))

            # Извлекаем сумму проданных билетов
            sold_tickets_count = sold_tickets['total_sold_tickets'] or 0

            # Вычисляем количество доступных билетов
            available_quantity = event.quantity - sold_tickets_count

            if available_quantity > 0:
                # Добавляем время мероприятия с количеством доступных билетов
                event_data['times'].append({
                    'begin_date': time.begin_date.strftime('%H:%M'),
                    'end_date': time.end_date.strftime('%H:%M'),
                    'quantity': available_quantity
                })

        if len(event_data['times']) > 0:
            data.append(event_data)

    return data


def get_filtered_services(event_id):
    if event_id:
        event = Event.objects.get(id=event_id)
        if event:
            services = EventTemplateServices.objects.filter(event_template=event.event_template)
            services_data = [{"id": service.service.id, "name": service.service.name} for service in services]
            return services_data
    return []


def get_available_services(event_id, date):
    if event_id and date:
        # Преобразуем дату из строки в datetime объект
        date_naive = datetime.strptime(date, '%Y-%m-%d')
        selected_date = timezone.make_aware(datetime.combine(date_naive, datetime.min.time()))

        # Получаем день недели (0 - понедельник, 6 - воскресенье)
        day_of_week = selected_date.weekday()

        # Создаем фильтр по дням недели с использованием Q-объектов
        day_filter = Q()
        if day_of_week == 0:
            day_filter &= Q(on_monday=True)
        elif day_of_week == 1:
            day_filter &= Q(on_tuesday=True)
        elif day_of_week == 2:
            day_filter &= Q(on_wednesday=True)
        elif day_of_week == 3:
            day_filter &= Q(on_thursday=True)
        elif day_of_week == 4:
            day_filter &= Q(on_friday=True)
        elif day_of_week == 5:
            day_filter &= Q(on_saturday=True)
        elif day_of_week == 6:
            day_filter &= Q(on_sunday=True)

        # Фильтруем мероприятия по дате и дню недели
        event = Event.objects.filter(
            id=event_id,
            begin_date__lte=selected_date,
            end_date__gte=selected_date
        ).filter(day_filter).first()

        if event:
            services = EventTemplateServices.objects.filter(event_template=event.event_template)
            services_data = []

            for service in services:
                service_item = service.service
                service_data = {
                    "id": service_item.id,
                    "name": service_item.name,
                    "cost": service_item.cost,
                    "times": []
                }

                # Получаем доступные EventTimes для данного мероприятия
                times = EventTimes.objects.filter(event=event, is_active=True)
                for time in times:
                    # Получаем записи TicketSalesService для текущего сервиса, мероприятия и времени
                    sold_tickets = TicketSalesService.objects.filter(
                        event=event,
                        event_time=time.begin_date,
                        event_time_end=time.end_date,
                        service=service_item,  # Фильтруем по сервису
                        service__on_calculation=True
                    ).aggregate(total_sold_tickets=Sum('tickets_count'))

                    # Извлекаем сумму проданных билетов для этого сервиса и времени
                    sold_tickets_count = sold_tickets['total_sold_tickets'] or 0

                    # Вычисляем доступное количество билетов для этого сервиса
                    available_quantity = event.quantity - sold_tickets_count

                    if available_quantity > 0:
                        # Добавляем время мероприятия с количеством доступных билетов
                        service_data['times'].append({
                            'begin_date': time.begin_date.strftime('%H:%M'),
                            'end_date': time.end_date.strftime('%H:%M'),
                            'quantity': available_quantity
                        })

                if len(service_data['times']) > 0:
                    services_data.append(service_data)

            return services_data
    return []
