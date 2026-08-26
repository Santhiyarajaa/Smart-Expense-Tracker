"""
URL configuration for smart_expense_tracker project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('expenses.api_urls')),
    path('', include('expenses.urls')),
]
