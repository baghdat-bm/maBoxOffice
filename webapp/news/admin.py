from django.contrib import admin
from django import forms
from ckeditor.widgets import CKEditorWidget

from .models import NewsCategory, News, NewsImages


class NewsAdminForm(forms.ModelForm):
    content_ru = forms.CharField(widget=CKEditorWidget(), label='Содержание (рус.)')
    content_kz = forms.CharField(widget=CKEditorWidget(), label='Содержание (каз.)')
    content_en = forms.CharField(widget=CKEditorWidget(), label='Содержание (анг.)')

    class Meta:
        model = News
        fields = "__all__"


class NewsImagesAdminInline(admin.TabularInline):
    model = NewsImages
    extra = 0


class NewsAdmin(admin.ModelAdmin):
    model = News
    prepopulated_fields = {"slug": ("title_ru",)}
    form = NewsAdminForm
    inlines = (NewsImagesAdminInline, )
    date_hierarchy = 'created_at'
    readonly_fields = ("views",)
    list_display = ("title_ru", "slug", "category",
                    "created_at", "published", "id")
    list_editable = ("published",)
    list_filter = (
        "category",
        "published",
    )
    search_fields = ("title_ru",)
    # show_facets = admin.ShowFacets.ALWAYS
    save_as = True


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name_ru",)}


admin.site.register(News, NewsAdmin)
admin.site.register(NewsCategory, CategoryAdmin)
