from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from ticket_sales.views import TicketSaleListView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),
    path("references/", include("references.urls")),
    path("ticket-sales/", include("ticket_sales.urls")),
    path('', TicketSaleListView.as_view(), name='home'),
]

# # Add this to include language prefixes
# urlpatterns += i18n_patterns(
#     path('', HomePageView.as_view(), name='home'),
#     path("news/", include("news.urls")),
# )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
