from django import forms
from django.utils import timezone
from .models import Contribucion, Contribuyente, Organismo, MESES, TIPO_CUENTA


class ContribucionForm(forms.ModelForm):
    class Meta:
        model  = Contribucion
        fields = [
            'nombre',
            'obligacion_pago',
            'numero_identidad',
            'numero_afiliado',
            'codigo_zpc',
            'organismo',
            'direccion',
            'nombre_establecimiento',
            'periodo_mes',
            'periodo_anio',
            'monto_cup',
            'tipo_cuenta',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo de la persona o entidad',
                'maxlength': 255,
            }),
            'obligacion_pago': forms.Select(attrs={
                'class': 'form-control',
                'autofocus': True,
            }),
            'numero_identidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '11 dígitos',
                'maxlength': 11,
                'inputmode': 'numeric',
            }),
            'numero_afiliado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'N° Afiliado',
                'inputmode': 'numeric',
            }),
            'codigo_zpc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ZPC-001',
                'style': 'text-transform:uppercase;',
            }),
            'organismo': forms.Select(attrs={
                'class': 'form-control',
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Calle y entrecalles',
                'maxlength': 255,
            }),
            'nombre_establecimiento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del establecimiento',
                'maxlength': 255,
            }),
            'periodo_mes':  forms.Select(attrs={'class': 'form-control'}),
            'periodo_anio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2024',
                'min': 2000,
                'max': timezone.now().year,
            }),
            'monto_cup': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'inputmode': 'decimal',
            }),
            'tipo_cuenta': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleNombreLabelContribucion(this)',
            }),
        }
        labels = {
            'nombre':                   'Nombre del Contribuyente',
            'obligacion_pago':          'Obligación de Pago',
            'numero_identidad':         'Número de Identidad',
            'numero_afiliado':          'Número de Afiliado',
            'codigo_zpc':               'Código ZPC',
            'organismo':                'Organismo',
            'direccion':                'Dirección',
            'nombre_establecimiento':   'Nombre del Establecimiento',
            'periodo_mes':              'Mes del Período',
            'periodo_anio':             'Año del Período',
            'monto_cup':                'Monto en CUP',
            'tipo_cuenta':              'Tipo de Cuenta a Operar',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.tipo_cuenta == 'fiscal':
            self.fields['nombre'].label = 'Nombre de la Entidad'
        self.fields['organismo'].queryset = Organismo.objects.all()
        self.fields['organismo'].empty_label = 'Seleccione un organismo'

    def clean_numero_identidad(self):
        ci = self.cleaned_data.get('numero_identidad', '').strip()
        if not ci.isdigit():
            raise forms.ValidationError('El número de identidad solo debe contener dígitos.')
        if len(ci) != 11:
            raise forms.ValidationError('El número de identidad debe tener exactamente 11 dígitos.')
        return ci

    def clean_codigo_zpc(self):
        return self.cleaned_data.get('codigo_zpc', '').strip().upper()

    def clean_periodo_anio(self):
        anio = self.cleaned_data.get('periodo_anio')
        if anio is None:
            raise forms.ValidationError('El año del período es obligatorio.')
        anio_actual = timezone.now().year
        if anio < 2000:
            raise forms.ValidationError('El año no puede ser anterior al 2000.')
        if anio > anio_actual:
            raise forms.ValidationError(
                f'El año no puede ser mayor al año actual ({anio_actual}).'
            )
        return anio

    def clean_monto_cup(self):
        monto = self.cleaned_data.get('monto_cup')
        if monto is not None and monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero.')
        return monto

    def clean(self):
        cleaned = super().clean()
        mes = cleaned.get('periodo_mes')
        anio = cleaned.get('periodo_anio')
        if mes and anio:
            now = timezone.now()
            if anio == now.year and mes > now.month:
                self.add_error('periodo_mes', 'No se puede registrar un período futuro.')
        return cleaned


class BusquedaForm(forms.Form):
    q            = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, identidad, afiliado o ZPC…',
        })
    )
    tipo_cuenta  = forms.ChoiceField(
        required=False,
        label='Tipo de cuenta',
        choices=[('', 'Todos los tipos')] + list(
            Contribucion._meta.get_field('tipo_cuenta').choices
        ),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    anio         = forms.IntegerField(
        required=False,
        label='Año',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Año',
            'min': 2000,
        })
    )


class ContribuyenteForm(forms.ModelForm):
    class Meta:
        model  = Contribuyente
        fields = [
            'nombre',
            'carnet_identidad',
            'numero_contribuyente',
            'codigo_zpc',
            'tipo_cuenta',
            'organismo',
            'direccion',
            'nombre_establecimiento',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo de la persona o entidad',
                'maxlength': 255,
            }),
            'carnet_identidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '11 dígitos',
                'maxlength': 11,
                'inputmode': 'numeric',
            }),
            'numero_contribuyente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de contribuyente',
                'inputmode': 'numeric',
            }),
            'codigo_zpc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ZPC-001',
                'style': 'text-transform:uppercase;',
            }),
            'tipo_cuenta': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleNombreLabel(this)',
            }),
            'organismo': forms.Select(attrs={
                'class': 'form-control',
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Calle y entrecalles',
                'maxlength': 255,
            }),
            'nombre_establecimiento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del establecimiento',
                'maxlength': 255,
            }),
        }
        labels = {
            'nombre':                   'Nombre del Contribuyente',
            'carnet_identidad':         'Carnet de Identidad',
            'numero_contribuyente':     'Número de Contribuyente',
            'codigo_zpc':               'Código ZPC',
            'tipo_cuenta':              'Tipo de Cuenta',
            'organismo':                'Organismo',
            'direccion':                'Dirección',
            'nombre_establecimiento':   'Nombre del Establecimiento',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.tipo_cuenta == 'fiscal':
            self.fields['nombre'].label = 'Nombre de la Entidad'
        self.fields['organismo'].queryset = Organismo.objects.all()
        self.fields['organismo'].empty_label = 'Seleccione un organismo'

    def clean_carnet_identidad(self):
        ci = self.cleaned_data.get('carnet_identidad', '').strip()
        if not ci.isdigit():
            raise forms.ValidationError('El carnet de identidad solo debe contener dígitos.')
        if len(ci) != 11:
            raise forms.ValidationError('El carnet de identidad debe tener exactamente 11 dígitos.')
        return ci

    def clean_codigo_zpc(self):
        return self.cleaned_data.get('codigo_zpc', '').strip().upper()

    def clean_numero_contribuyente(self):
        num = self.cleaned_data.get('numero_contribuyente', '').strip()
        if not num.isdigit():
            raise forms.ValidationError('El número de contribuyente solo debe contener dígitos.')
        return num
