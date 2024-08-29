from datetime import datetime

from django.db import models
from django.utils import timezone
import uuid

from references.models import Service, Event, Inventory


class TicketSale(models.Model):
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    amount = models.IntegerField(verbose_name="Сумма итого", blank=True, default=0)
    paid_amount = models.IntegerField(verbose_name="Сумма оплаты", blank=True, default=0)
    refund_amount = models.IntegerField(verbose_name="Сумма возврата", blank=True, default=0)
    paid_cash = models.IntegerField(verbose_name="Оплачено наличкой", blank=True, default=0)
    paid_card = models.IntegerField(verbose_name="Оплачено картой", blank=True, default=0)
    paid_qr = models.IntegerField(verbose_name="Оплачено QR", blank=True, default=0)
    status = models.CharField(max_length=25, verbose_name='Статус', null=True, blank=True, default='Новый заказ')

    def __str__(self):
        return f'№{self.pk} от {self.date}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-date']

    def save(self, *args, **kwargs):

        self.paid_amount = self.paid_cash + self.paid_card + self.paid_qr

        if self.paid_amount == 0:
            self.status = 'Не оплачен'
        elif self.paid_amount >= self.amount:
            if self.refund_amount > 0:
                if self.paid_amount > self.refund_amount:
                    self.status = 'Частичный возврат'
                else:
                    self.status = 'Оплата возвращена'
            else:
                self.status = 'Оплачен'
        elif self.paid_amount < self.amount:
            self.status = 'Частично оплачен'

        super(TicketSale, self).save(*args, **kwargs)


def default_datetime():
    return datetime.now().date()


class TicketSalesService(models.Model):
    ticket_sale = models.ForeignKey(TicketSale, on_delete=models.CASCADE, verbose_name="Заказ")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга")
    event = models.ForeignKey(Event, on_delete=models.PROTECT, verbose_name="Мероприятие")
    event_date = models.DateField(verbose_name="Дата мероприятия", default=default_datetime)
    event_time = models.TimeField(verbose_name="Время мероприятия")
    tickets_count = models.PositiveSmallIntegerField(verbose_name="Количество билетов")
    tickets_amount = models.IntegerField(verbose_name="Сумма билетов")
    discount = models.IntegerField(verbose_name="Скидка", blank=True, default=0)
    total_amount = models.IntegerField(verbose_name="Сумма итого")
    ticket_guid = models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="Идентификатор билета")

    def __str__(self):
        return f'{self.ticket_sale.pk}-{self.pk}'

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['-id']


class TicketSalesPayments(models.Model):
    PaymentMethods = (
        ("QR", "Оплата по QR"),
        ("CD", "Оплата картой"),
        ("CH", "Наличка"),
    )

    ticket_sale = models.ForeignKey(TicketSale, on_delete=models.CASCADE, verbose_name="Заказ")
    payment_date = models.DateTimeField(verbose_name="Дата оплаты")
    payment_method = models.CharField(
        max_length=2,
        choices=PaymentMethods,
        default="QR",
    )
    amount = models.IntegerField(verbose_name="Сумма оплаты", blank=True, default=0)
    process_id = models.CharField(max_length=20, verbose_name='Идентификатор процесса', unique=True)
    last_status = models.CharField(max_length=15, verbose_name='Последний статус', null=True, blank=True)
    error_text = models.CharField(max_length=450, verbose_name='Текст ошибки', null=True, blank=True)
    transaction_id = models.CharField(max_length=20, verbose_name='Идентификатор успешной транзакции', null=True,
                                      blank=True)
    response_data = models.TextField(max_length=600, verbose_name='Полученные данные', null=True,
                                     blank=True)

    def __str__(self):
        return f'{self.ticket_sale.pk}-{self.pk}'

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-id']


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
