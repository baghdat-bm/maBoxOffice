from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import get_language
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from .models import NewsCategory, News, NewsImages
from .forms import NewsCategoryForm, NewsForm, NewsImagesForm


def get_field_for_language(instance, field_name):
    lang = get_language()
    if lang == 'ru':
        return getattr(instance, f'{field_name}_ru')
    elif lang == 'kz':
        return getattr(instance, f'{field_name}_kz')
    else:  # Default to English
        return getattr(instance, f'{field_name}_en')


class HomePageView(TemplateView):
    template_name = 'site/home.html'


# NewsCategory Views
class NewsCategoryListView(ListView):
    model = NewsCategory
    template_name = 'news/category_list.html'
    context_object_name = 'categories'


class NewsCategoryDetailView(DetailView):
    model = NewsCategory
    template_name = 'news/category_detail.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['name'] = get_field_for_language(self.object, 'name')
        return context


class NewsCategoryCreateView(CreateView):
    model = NewsCategory
    form_class = NewsCategoryForm
    template_name = 'news/category_form.html'
    success_url = reverse_lazy('news:category_list')


class NewsCategoryUpdateView(UpdateView):
    model = NewsCategory
    form_class = NewsCategoryForm
    template_name = 'news/category_form.html'
    success_url = reverse_lazy('news:category_list')


class NewsCategoryDeleteView(DeleteView):
    model = NewsCategory
    template_name = 'news/category_confirm_delete.html'
    success_url = reverse_lazy('news:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['name'] = get_field_for_language(self.object, 'name')
        return context


# News Views
class NewsListView(ListView):
    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'


class NewsDetailView(DetailView):
    model = News
    template_name = 'news/news_detail.html'
    context_object_name = 'news'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = get_field_for_language(self.object, 'title')
        context['content'] = get_field_for_language(self.object, 'content')
        return context


class NewsCreateView(CreateView):
    model = News
    form_class = NewsForm
    template_name = 'news/news_form.html'
    success_url = reverse_lazy('news:news_list')


class NewsUpdateView(UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'news/news_form.html'
    success_url = reverse_lazy('news:news_list')


class NewsDeleteView(DeleteView):
    model = News
    template_name = 'news/news_confirm_delete.html'
    success_url = reverse_lazy('news:news_list')


# NewsImages Views
class NewsImagesCreateView(CreateView):
    model = NewsImages
    form_class = NewsImagesForm
    template_name = 'news/news_images_form.html'
    success_url = reverse_lazy('news:news_list')


class NewsImagesDeleteView(DeleteView):
    model = NewsImages
    template_name = 'news/news_images_confirm_delete.html'

    def get_success_url(self):
        news_id = self.object.news.id
        return reverse_lazy('news:news_detail', kwargs={'pk': news_id})
