from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from rest_framework.authtoken import views

from references.views import home_page
from .drf_yasg_schema import schema_view

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),
    path("references/", include("references.urls")),
    path("ticket-sales/", include("ticket_sales.urls")),

    path('api-token-auth/', views.obtain_auth_token),
    path("api/", include("ticket_sales.api_urls")),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('', home_page, name='home'),
]

# # Add this to include language prefixes
# urlpatterns += i18n_patterns(
#     path('', HomePageView.as_view(), name='home'),
#     path("news/", include("news.urls")),
# )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
