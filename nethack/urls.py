from django.urls import path
from web.views import index, health, diagnostics_info

urlpatterns = [
    path('', index, name='index'),
    path('api/health/', health, name='health'),
    path('api/diagnostics-info/', diagnostics_info, name='diagnostics-info'),
]
