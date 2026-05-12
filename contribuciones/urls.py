"""
URLs — app contribuciones (namespace: contribuciones)

  lista      GET  /contribuciones/
  crear      GET/POST  /contribuciones/nueva/
  detalle    GET  /contribuciones/<pk>/
  editar     GET/POST  /contribuciones/<pk>/editar/
  eliminar   GET/POST  /contribuciones/<pk>/eliminar/
  exportar   GET  /contribuciones/exportar/csv/
"""

from django.urls import path
from . import views

app_name = 'contribuciones'

urlpatterns = [
    path('',                      views.ContribucionListView.as_view(),   name='lista'),
    path('nueva/',                views.ContribucionCreateView.as_view(), name='crear'),
    path('<int:pk>/',             views.ContribucionDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/',      views.ContribucionUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/',    views.ContribucionDeleteView.as_view(), name='eliminar'),
    path('exportar/csv/',         views.exportar_csv,                     name='exportar_csv'),
]
