from django.db import models


class EventTemplate(models.Model):
    name = models.CharField(max_length=300, verbose_name='Наименование')
    logo = models.ImageField(upload_to="logos/%Y/%m/%d", blank=True, null=True, verbose_name='Логотип')
    description = models.TextField(verbose_name="Описание", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Шаблон мероприятий'
        verbose_name_plural = 'Шаблоны мероприятии'
        ordering = ['name']


class Event(models.Model):
    event_template = models.ForeignKey(EventTemplate, on_delete=models.CASCADE, verbose_name="Шаблон мероприятий")
    begin_date = models.DateTimeField(verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    on_monday = models.BooleanField(verbose_name='Понедельник')
    on_tuesday = models.BooleanField(verbose_name='Вторник')
    on_wednesday = models.BooleanField(verbose_name='Среда')
    on_thursday = models.BooleanField(verbose_name='Четверг')
    on_friday = models.BooleanField(verbose_name='Пятница')
    on_saturday = models.BooleanField(verbose_name='Суббота')
    on_sunday = models.BooleanField(verbose_name='Воскресенье')

    def __str__(self):
        return f'{self.event_template.name} ({self.id})'

    @property
    def name(self) -> str:
        return f'{self.event_template.name} ({self.id})'

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'
        ordering = ['-begin_date']


class EventTimes(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие")
    begin_date = models.TimeField(verbose_name="Дата начала")
    end_date = models.TimeField(verbose_name="Дата окончания")
    is_active = models.BooleanField(verbose_name="Активность")

    def __str__(self):
        return f'{self.event.id}: {self.begin_date}-{self.end_date}'

    class Meta:
        verbose_name = 'Время'
        verbose_name_plural = 'Время'
        ordering = ['begin_date']


class Inventory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие")
    name = models.CharField(max_length=300, verbose_name='Наименование')
    size = models.CharField(max_length=15, verbose_name="Размер")
    quantity = models.PositiveSmallIntegerField(verbose_name="Количество")
    cost = models.IntegerField(verbose_name="Стоимость")

    def __str__(self):
        return f'{self.event.id}: {self.name}'

    class Meta:
        verbose_name = 'Инвентарь'
        verbose_name_plural = 'Инвентарь'
        ordering = ['name']


class Service(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Мероприятие")
    name = models.CharField(max_length=300, verbose_name='Наименование')
    size = models.CharField(max_length=15, verbose_name="Размер")
    quantity = models.PositiveSmallIntegerField(verbose_name="Количество")
    cost = models.IntegerField(verbose_name="Стоимость")

    def __str__(self):
        return f'{self.event.id}: {self.name}'

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['name']
