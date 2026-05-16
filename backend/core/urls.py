from django.contrib import admin
from django.urls import path, include

# Applies the custom admin dashboard (monkey-patches admin.site.index).
from core import admin_dashboard  # noqa: F401

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/',     include('api.urls')),
]
