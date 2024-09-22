from datetime import datetime

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import enum

from references.models import Service, Event, Inventory
from ticket_sales.helpers import get_num_val


def default_datetime():
    return datetime.now().date()


class SaleTypeEnum(enum.Enum):
    CS = "CS", "Касса"
    TS = "TS", "Киоск"
    SM = "SM", "Сайт muzaidyny.kz"
    KP = "KP", "Kaspi платежи"

    @classmethod
    def choices(cls):
        return [(key.value[0], key.value[1]) for key in cls]


class SaleStatusEnum(enum.Enum):
    NP = "NP", "Не оплачен"
    PD = "PD", "Оплачен"
    PP = "PP", "Частично оплачен"
    RT = "RT", "Возврат"
    PT = "PT", "Частичный возврат"
    CN = "CN", "Отменен"

    @classmethod
    def choices(cls):
        return [(key.value[0], key.value[1]) for key in cls]


class PaymentMethods(enum.Enum):
    QR = "QR", "Оплата по QR"
    CD = "CD", "Оплата картой"
    CH = "CH", "Наличка"

    @classmethod
    def choices(cls):
        return [(key.value[0], key.value[1]) for key in cls]


class TicketSale(models.Model):
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    amount = models.IntegerField(verbose_name="Сумма итого", blank=True, default=0)
    paid_amount = models.IntegerField(verbose_name="Сумма оплаты", blank=True, default=0)
    refund_amount = models.IntegerField(verbose_name="Сумма возврата", blank=True, default=0)
    paid_cash = models.IntegerField(verbose_name="Оплачено наличкой", blank=True, default=0)
    paid_card = models.IntegerField(verbose_name="Оплачено картой", blank=True, default=0)
    paid_qr = models.IntegerField(verbose_name="Оплачено QR", blank=True, default=0)
    status = models.CharField(max_length=2, verbose_name='Статус',
                              choices=SaleStatusEnum.choices(),
                              null=True,
                              blank=True,
                              default=SaleStatusEnum.NP.value[0])
    tickets_count = models.PositiveSmallIntegerField(verbose_name="Всего билетов", blank=True, default=0)
    tickets_made = models.BooleanField(verbose_name="Билеты сформированы", blank=True, default=False)
    sale_type = models.CharField(max_length=2,
                                 verbose_name="Тип продажи",
                                 choices=SaleTypeEnum.choices(),
                                 default='CS',
                                 blank=True)
    email = models.CharField(max_length=50, verbose_name='Email', null=True, blank=True)
    phone = models.CharField(max_length=50, verbose_name='Телефон', null=True, blank=True)
    booking_begin_date = models.DateTimeField(verbose_name="Дата время бронирования", null=True, blank=True)
    booking_end_date = models.DateTimeField(verbose_name="Дата время окончания бронирования", null=True, blank=True)

    def __str__(self):
        return f'№{self.pk} от {self.date}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-id']

    def save(self, *args, **kwargs):
        # Рассчитываем сумму оплаты
        self.paid_amount = get_num_val(self.paid_cash) + get_num_val(self.paid_card) + get_num_val(self.paid_qr)

        # Обновляем статус заказа в зависимости от суммы оплаты и возврата
        if self.status != 'CN':  # если заказ не отменен
            if self.paid_amount == 0:
                self.status = SaleStatusEnum.NP.value[0]
            elif self.paid_amount >= self.amount:
                if self.refund_amount > 0:
                    if self.paid_amount > self.refund_amount:
                        self.status = SaleStatusEnum.PT.value[0]
                    else:
                        self.status = SaleStatusEnum.RT.value[0]
                else:
                    self.status = SaleStatusEnum.PD.value[0]
            elif self.paid_amount < self.amount:
                self.status = SaleStatusEnum.PP.value[0]

        super(TicketSale, self).save(*args, **kwargs)


class TicketSalesService(models.Model):
    ticket_sale = models.ForeignKey(TicketSale, on_delete=models.CASCADE, verbose_name="Заказ")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга")
    event = models.ForeignKey(Event, on_delete=models.PROTECT, verbose_name="Мероприятие")
    event_date = models.DateField(verbose_name="Дата мероприятия", default=default_datetime)
    event_time = models.TimeField(verbose_name="Время начала мероприятия")
    event_time_end = models.TimeField(verbose_name="Время окончания мероприятия", blank=True, null=True)
    tickets_count = models.PositiveSmallIntegerField(verbose_name="Количество билетов")
    tickets_amount = models.IntegerField(verbose_name="Сумма билетов")
    discount = models.IntegerField(verbose_name="Скидка", blank=True, default=0)
    total_amount = models.IntegerField(verbose_name="Сумма итого")
    paid_amount = models.IntegerField(verbose_name="Сумма оплачено", blank=True, default=0)

    def __str__(self):
        return f'{self.ticket_sale.pk}-{self.pk}'

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['-id']


class TicketSalesPayments(models.Model):
    ticket_sale = models.ForeignKey(TicketSale, on_delete=models.CASCADE, verbose_name="Заказ")
    payment_date = models.DateTimeField(verbose_name="Дата оплаты")
    payment_method = models.CharField(
        max_length=2,
        choices=PaymentMethods.choices(),
        default="QR",
    )
    amount = models.IntegerField(verbose_name="Сумма оплаты", blank=True, default=0)
    refund_amount = models.IntegerField(verbose_name="Сумма возврата", blank=True, default=0)
    process_id = models.CharField(max_length=20, verbose_name='Идентификатор процесса', null=True, blank=True)
    last_status = models.CharField(max_length=15, verbose_name='Последний статус', null=True, blank=True)
    error_text = models.CharField(max_length=450, verbose_name='Текст ошибки', null=True, blank=True)
    transaction_id = models.CharField(max_length=50, verbose_name='Идентификатор успешной транзакции', null=True,
                                      blank=True)
    currency = models.CharField(max_length=3, verbose_name='Валюта', null=True, blank=True)
    description = models.CharField(max_length=250, verbose_name='Описание', null=True, blank=True)
    card_mask = models.CharField(max_length=25, verbose_name='Маска карты', null=True, blank=True)
    terminal = models.CharField(max_length=45, verbose_name='ID терминала', null=True, blank=True)
    response_data = models.TextField(max_length=1000, verbose_name='Полученные данные', null=True,
                                     blank=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f'{self.pk}-{self.ticket_sale.pk}'

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-id']


class TicketSalesTicket(models.Model):
    ticket_sale = models.ForeignKey(TicketSale, on_delete=models.CASCADE, verbose_name="Заказ")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга")
    payment = models.ForeignKey(TicketSalesPayments, on_delete=models.PROTECT, verbose_name="Платеж", blank=True, null=True)
    amount = models.IntegerField(verbose_name="Сумма билета")
    number = models.PositiveSmallIntegerField(verbose_name="Номер билета")
    ticket_guid = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="Идентификатор билета")
    event = models.ForeignKey(Event, on_delete=models.PROTECT, verbose_name="Мероприятие")
    event_date = models.DateField(verbose_name="Дата мероприятия", default=default_datetime)
    event_time = models.TimeField(verbose_name="Время начала мероприятия")
    event_time_end = models.TimeField(verbose_name="Время окончания мероприятия", blank=True, null=True)
    last_event_code = models.CharField(max_length=1, verbose_name="Код последнего события", blank=True, null=True,
                                       default='')
    is_refund = models.BooleanField(verbose_name='Возвратный', default=False)

    def __str__(self):
        return f'{self.number}'

    class Meta:
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'
        ordering = ['number']


class TicketsSold(models.Model):
    ticket_sale = models.ForeignKey(TicketSale, on_delete=models.CASCADE, verbose_name="Заказ")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга")
    event = models.ForeignKey(Event, on_delete=models.PROTECT, verbose_name="Мероприятие")
    event_date = models.DateField(verbose_name="Дата мероприятия")
    event_time = models.TimeField(verbose_name="Время мероприятия")
    tickets_count = models.PositiveSmallIntegerField(verbose_name="Количество билетов")

    def __str__(self):
        return f'{self.ticket_sale.pk}-{self.pk}'

    class Meta:
        verbose_name = 'Проданный билет'
        verbose_name_plural = 'Проданные билеты'
        ordering = ['-id']


class TerminalSettings(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    username = models.CharField(max_length=150, verbose_name="Username")
    access_token = models.TextField(verbose_name="Access Token")
    refresh_token = models.TextField(verbose_name="Refresh Token")
    expiration_date = models.DateTimeField(verbose_name="Expiration date", blank=True, null=True)
    app_type = models.CharField(max_length=2,
                                verbose_name="Тип приложения",
                                choices=SaleTypeEnum.choices(),
                                default=SaleTypeEnum.CS.value[0],
                                blank=True,
                                null=True,
                                unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    @staticmethod
    def get_app_type_display_choices():
        # Возвращаем только "Касса" и "Киоск"
        limited_choices = [choice for choice in SaleTypeEnum.choices() if choice[0] in ["CS", "TS"]]
        return limited_choices

    class Meta:
        verbose_name = 'Настройки терминала'
        verbose_name_plural = 'Настройки терминала'

    # def clean(self):
    #     if TerminalSettings.objects.exists() and not self.pk:
    #         raise ValidationError("Можно создать только одну запись TerminalSettings.")
    #
    # def save(self, *args, **kwargs):
    #     self.clean()
    #     super(TerminalSettings, self).save(*args, **kwargs)

    def __str__(self):
        return f"Terminal settings for {self.username} to {self.ip_address} for {self.get_app_type_display()}"
