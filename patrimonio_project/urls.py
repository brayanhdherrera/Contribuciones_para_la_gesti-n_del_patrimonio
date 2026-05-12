"""
URLs raíz del proyecto.
  /admin/       → Panel de administración Django
  /accounts/    → Auth nativa: login, logout, password_change, password_reset
  /contribuciones/ → App principal
  /             → Redirige a /contribuciones/
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

# Personalización del Admin
admin.site.site_header = "Administración — Contribuciones al Patrimonio"
admin.site.site_title  = "Patrimonio Admin"
admin.site.index_title = "Panel de Control"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('contribuciones/', include('contribuciones.urls')),
    path('', RedirectView.as_view(url='/contribuciones/', permanent=False)),
]
