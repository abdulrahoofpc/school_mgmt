from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('fees/', include('fees.urls')),
    path('expenses/', include('expenses.urls')),
    path('reports/', include('reports.urls')),
    # API endpoints
    path('api/accounts/', include('accounts.api_urls')),
    path('api/students/', include('students.api_urls')),
    path('api/teachers/', include('teachers.api_urls')),
    path('api/fees/', include('fees.api_urls')),
    path('api/expenses/', include('expenses.api_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
