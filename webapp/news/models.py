from django.db import models
from django.urls import reverse


class NewsCategory(models.Model):
    name_ru = models.CharField(max_length=200, verbose_name="Наименование (рус.)")
    name_kz = models.CharField(max_length=200, verbose_name="Наименование (каз.)")
    name_en = models.CharField(max_length=200, verbose_name="Наименование (анг.)")
    slug = models.SlugField(max_length=200, verbose_name="Url", unique=True)

    def __str__(self):
        return self.name_ru

    class Meta:
        ordering = ["name_ru"]
        verbose_name = "Категория новости"
        verbose_name_plural = "Категории новостей"


class News(models.Model):
    title_ru = models.CharField(max_length=255, verbose_name="Заголовок (рус.)")
    title_kz = models.CharField(max_length=255, verbose_name="Заголовок (каз.)")
    title_en = models.CharField(max_length=255, verbose_name="Заголовок (анг.)")
    category = models.ForeignKey(
        NewsCategory,
        on_delete=models.PROTECT,
        verbose_name="Категория",
        related_name="news",
    )
    content_ru = models.TextField(verbose_name="Содержание (рус.)", blank=True)
    content_kz = models.TextField(verbose_name="Содержание (каз.)", blank=True)
    content_en = models.TextField(verbose_name="Содержание (анг.)", blank=True)
    source = models.CharField(max_length=200, verbose_name="Источник", blank=True)
    created_at = models.DateField(verbose_name="Дата создания")
    photo = models.ImageField(
        upload_to="photos/%Y/%m/%d", blank=True, verbose_name="Картинка анонса"
    )
    slug = models.SlugField(max_length=255, verbose_name="Url", unique=True)
    views = models.IntegerField(default=0, verbose_name="Кол-во просмотров")
    published = models.BooleanField(
        default=False, blank=True, verbose_name="Опубликован"
    )

    def __str__(self):
        return self.title_ru

    def get_absolute_url(self):
        return reverse(
            'news:news_detail',
            args=[self.slug]
        )

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['slug', '-created_at']),
        ]


class NewsImages(models.Model):
    news = models.ForeignKey(News, on_delete=models.CASCADE, verbose_name="Новость")
    image = models.ImageField(
        upload_to="news_image/%Y/%m/%d", blank=True, verbose_name="Картинка"
    )

    class Meta:
        verbose_name = "Картинку для этой новости"
        verbose_name_plural = "Картинки для этой новости"
