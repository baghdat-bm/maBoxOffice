from django.urls import path
from .views import (
    NewsCategoryListView, NewsCategoryDetailView, NewsCategoryCreateView,
    NewsCategoryUpdateView, NewsCategoryDeleteView, NewsListView,
    NewsDetailView, NewsCreateView, NewsUpdateView, NewsDeleteView,
    NewsImagesCreateView, NewsImagesDeleteView
)

app_name = 'news'

urlpatterns = [
    # Category URLs
    path('categories/list/', NewsCategoryListView.as_view(), name='category_list'),
    path('categories/create/', NewsCategoryCreateView.as_view(), name='category_create'),
    path('categories/update/<slug:slug>/', NewsCategoryUpdateView.as_view(), name='category_update'),
    path('categories/delete/<slug:slug>/', NewsCategoryDeleteView.as_view(), name='category_delete'),
    path('categories/detail/<slug:slug>/', NewsCategoryDetailView.as_view(), name='category_detail'),

    # News URLs
    path('list/', NewsListView.as_view(), name='news_list'),
    path('create/', NewsCreateView.as_view(), name='news_create'),
    path('detail/<slug:slug>/', NewsDetailView.as_view(), name='news_detail'),
    path('update/<slug:slug>/', NewsUpdateView.as_view(), name='news_update'),
    path('delete/<slug:slug>/', NewsDeleteView.as_view(), name='news_delete'),

    # NewsImages URLs
    path('images/add/<slug:news_slug>/', NewsImagesCreateView.as_view(), name='news_images_create'),
    path('images/delete/<int:pk>/', NewsImagesDeleteView.as_view(), name='news_images_delete'),
]
