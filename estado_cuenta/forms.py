import json
from django import forms


class ImportarEstadoCuentaForm(forms.Form):
    archivo = forms.FileField(
        label='Seleccione el archivo',
        help_text='Formatos aceptados: XML (.xml), PDF (.pdf), TXT (.txt/.csv)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xml,.pdf,.txt,.csv',
        })
    )


class ConfirmarImportacionForm(forms.Form):
    datos = forms.CharField(widget=forms.HiddenInput)
    nombre_archivo = forms.CharField(widget=forms.HiddenInput)
    archivo_id = forms.IntegerField(widget=forms.HiddenInput)

    def clean_datos(self):
        datos = self.cleaned_data['datos']
        try:
            return json.loads(datos)
        except json.JSONDecodeError:
            raise forms.ValidationError('Error al decodificar los datos.')
