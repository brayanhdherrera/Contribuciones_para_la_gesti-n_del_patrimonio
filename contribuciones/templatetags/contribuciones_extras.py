"""
Filtros de template personalizados para la app contribuciones.
Uso: {% load contribuciones_extras %}
"""

from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """Añade una clase CSS a un campo de formulario Django."""
    return field.as_widget(attrs={'class': css_class})


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Preserva los parámetros GET actuales y agrega/reemplaza los indicados.
    Útil para paginación + filtros combinados.
    Uso: {% query_transform page=2 %}
    """
    request = context['request']
    updated = request.GET.copy()
    for k, v in kwargs.items():
        updated[k] = v
    return updated.urlencode()
