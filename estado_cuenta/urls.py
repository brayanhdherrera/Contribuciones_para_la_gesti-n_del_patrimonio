from django.urls import path
from . import views

app_name = 'estado_cuenta'

urlpatterns = [
    path('',                    views.EstadoCuentaListView.as_view(),       name='lista'),
    path('importar/',           views.ImportarEstadoCuentaView.as_view(),  name='importar'),
    path('<int:pk>/eliminar/',  views.EliminarMovimientoView.as_view(),    name='eliminar'),
    path('eliminar-todos/',     views.eliminar_todos_movimientos,          name='eliminar_todos'),
]
