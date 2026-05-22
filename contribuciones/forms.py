from django import forms
from django.utils import timezone
from .models import Contribucion, MESES, TIPOS_CUENTA
class ContribucionForm(forms.ModelForm):
        class Meta:
            model  = Contribucion
            fields = [
                'obligacion_pago',
                'numero_identidad',
                'numero_contribuyente_ofa',
                'codigo_zpc',
                'periodo_mes',
                'periodo_anio',
                'monto_cup',
                'tipo_cuenta',
        ]
        widgets = {
            'obligacion_pago': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Contribución mensual patrimonio',
                'autofocus': True,
            }),
            'numero_identidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '11 dígitos',
                'maxlength': 11,
                'inputmode': 'numeric',
            }),
            'numero_contribuyente_ofa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número OFA',
                'inputmode': 'numeric',
            }),
            'codigo_zpc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ZPC-001',
                'style': 'text-transform:uppercase;',
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
            'tipo_cuenta': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'obligacion_pago':           'Obligación de Pago',
            'numero_identidad':          'Número de Identidad',
            'numero_contribuyente_ofa':  'Número de Contribuyente OFA',
            'codigo_zpc':                'Código ZPC',
            'periodo_mes':               'Mes del Período',
            'periodo_anio':              'Año del Período',
            'monto_cup':                 'Monto en CUP',
            'tipo_cuenta':               'Tipo de Cuenta a Operar',
        }

    # ── Validaciones de campo ──────────────────────────────────────────────────

        def clean_numero_identidad(self):
            ci = self.cleaned_data.get('numero_identidad', '').strip()
            if not ci.isdigit():
                raise forms.ValidationError('El número de identidad solo debe contener dígitos.')
            if len(ci) != 11:
                raise forms.ValidationError('El número de identidad debe tener exactamente 11 dígitos.')
    
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

    # ── Validación cruzada ────────────────────────────────────────────────────

        def clean(self): 
            cleaned = super().clean() 
            mes = cleaned.get('periodo_mes')
            anio = cleaned.get('periodo_anio')
            if mes and anio:
                now = timezone.now()
            if anio == now.year and mes > now.month:
                self.add_error('periodo_mes', 'No se puede registrar un período futuro.')
                return cleaned


# ── Formulario de búsqueda (GET, sin CSRF) ─────────────────────────────────────

class BusquedaForm(forms.Form):
    """Búsqueda simple en el listado."""
    q            = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por identidad, OFA o ZPC…',
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
