from datetime import timedelta
from django.utils import timezone

from references.models import Event


def get_available_events_dates():
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

            # if is_day_included(event, current_date):
            # Проверяем, включен ли текущий день недели для данного мероприятия
            # и входит ли дата в диапазон [сегодня, сегодня + 30 дней]
            if today <= current_date <= date_limit and is_day_included(event, current_date):
                available_dates.append(current_date)

    # Удаление дубликатов и сортировка дат
    available_dates = sorted(list(set(available_dates)))
    return available_dates
