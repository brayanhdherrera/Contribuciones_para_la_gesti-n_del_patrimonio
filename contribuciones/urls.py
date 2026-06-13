"""
URLs — app contribuciones (namespace: contribuciones)

  lista        GET  /contribuciones/
  crear        GET/POST  /contribuciones/nueva/
  detalle      GET  /contribuciones/<pk>/
  editar       GET/POST  /contribuciones/<pk>/editar/
  eliminar     GET/POST  /contribuciones/<pk>/eliminar/
  exportar     GET  /contribuciones/exportar/excel/
  importar     GET/POST  /contribuciones/importar/
"""

from django.urls import path
from . import views

app_name = 'contribuciones'

urlpatterns = [
    path('',                      views.DashboardView.as_view(),             name='dashboard'),
    path('lista/',                views.ContribucionListView.as_view(),      name='lista'),
    path('nueva/',                views.ContribucionCreateView.as_view(),    name='crear'),
    path('<int:pk>/',             views.ContribucionDetailView.as_view(),    name='detalle'),
    path('<int:pk>/editar/',      views.ContribucionUpdateView.as_view(),    name='editar'),
    path('<int:pk>/eliminar/',    views.ContribucionDeleteView.as_view(),    name='eliminar'),
    path('exportar/excel/',       views.exportar_excel,                      name='exportar_excel'),
    path('importar/',             views.ImportarContribucionView.as_view(),  name='importar'),
    path('buscar-contribuyente/', views.buscar_contribuyente,                name='buscar_contribuyente'),
]


# ── URLs Contribuyentes (namespace: contribuyentes) ────────────────────────────

urlpatterns += [
    path('contribuyentes/',                       views.ContribuyenteListView.as_view(),     name='contribuyente_lista'),
    path('contribuyentes/nuevo/',                 views.ContribuyenteCreateView.as_view(),   name='contribuyente_crear'),
    path('contribuyentes/<int:pk>/',              views.ContribuyenteDetailView.as_view(),   name='contribuyente_detalle'),
    path('contribuyentes/<int:pk>/editar/',       views.ContribuyenteUpdateView.as_view(),   name='contribuyente_editar'),
    path('contribuyentes/<int:pk>/eliminar/',     views.ContribuyenteDeleteView.as_view(),   name='contribuyente_eliminar'),
    path('contribuyentes/importar/',              views.ImportarContribuyenteView.as_view(), name='contribuyente_importar'),
]
