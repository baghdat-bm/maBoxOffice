from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import NewsCategory, News, NewsImages


class NewsCategoryForm(forms.ModelForm):
    class Meta:
        model = NewsCategory
        fields = ['name_ru', 'name_kz', 'name_en', 'slug']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = [
            'title_ru', 'title_kz', 'title_en', 'category', 'content_ru', 'content_kz', 'content_en',
            'source', 'created_at', 'photo', 'slug', 'views', 'published'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))


class NewsImagesForm(forms.ModelForm):
    class Meta:
        model = NewsImages
        fields = ['news', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
