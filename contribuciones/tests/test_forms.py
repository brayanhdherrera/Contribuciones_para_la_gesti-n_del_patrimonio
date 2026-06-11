from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..forms import ContribucionForm, ContribuyenteForm, BusquedaForm

User = get_user_model()


class ContribucionFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'obligacion_pago': 'contribucion',
            'numero_identidad': '90123456789',
            'numero_afiliado': '1234567',
            'codigo_zpc': 'ZPC-001',
            'periodo_mes': 3,
            'periodo_anio': 2024,
            'monto_cup': 1500.00,
            'tipo_cuenta': 'natural',
        }

    def test_form_valido(self):
        form = ContribucionForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_obligacion_pago_es_select(self):
        form = ContribucionForm()
        widget = form.fields['obligacion_pago'].widget
        self.assertEqual(widget.__class__.__name__, 'Select')

    def test_obligacion_pago_choices_disponibles(self):
        form = ContribucionForm()
        choices = dict(form.fields['obligacion_pago'].choices)
        self.assertIn('contribucion', choices)
        self.assertIn('donacion', choices)

    def test_obligacion_pago_con_donacion(self):
        data = self.valid_data.copy()
        data['obligacion_pago'] = 'donacion'
        form = ContribucionForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['obligacion_pago'], 'donacion')

    def test_obligacion_pago_invalido(self):
        data = self.valid_data.copy()
        data['obligacion_pago'] = 'opcion_invalida'
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('obligacion_pago', form.errors)

    def test_numero_identidad_requerido(self):
        data = self.valid_data.copy()
        data['numero_identidad'] = ''
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('numero_identidad', form.errors)

    def test_numero_identidad_exactamente_11(self):
        data = self.valid_data.copy()
        data['numero_identidad'] = '1234567890'
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())

    def test_numero_identidad_solo_digitos(self):
        data = self.valid_data.copy()
        data['numero_identidad'] = '1234567890a'
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())

    def test_codigo_zpc_se_convierte_a_mayusculas(self):
        data = self.valid_data.copy()
        data['codigo_zpc'] = 'zpc-001'
        form = ContribucionForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['codigo_zpc'], 'ZPC-001')

    def test_periodo_anio_menor_a_2000(self):
        data = self.valid_data.copy()
        data['periodo_anio'] = 1999
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('periodo_anio', form.errors)

    def test_periodo_anio_futuro(self):
        data = self.valid_data.copy()
        data['periodo_anio'] = timezone.now().year + 1
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('periodo_anio', form.errors)

    def test_periodo_mes_futuro(self):
        now = timezone.now()
        if now.month == 12:
            self.skipTest('No se puede probar mes futuro en diciembre')
        data = self.valid_data.copy()
        data['periodo_mes'] = now.month + 1
        data['periodo_anio'] = now.year
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('periodo_mes', form.errors)

    def test_monto_cero_invalido(self):
        data = self.valid_data.copy()
        data['monto_cup'] = 0
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('monto_cup', form.errors)

    def test_monto_negativo_invalido(self):
        data = self.valid_data.copy()
        data['monto_cup'] = -100
        form = ContribucionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('monto_cup', form.errors)

    def test_campos_requeridos(self):
        form = ContribucionForm(data={})
        self.assertFalse(form.is_valid())
        required_fields = [
            'obligacion_pago', 'numero_identidad', 'numero_afiliado',
            'codigo_zpc', 'periodo_mes', 'periodo_anio', 'monto_cup', 'tipo_cuenta',
        ]
        for field in required_fields:
            self.assertIn(field, form.errors)


class ContribuyenteFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'carnet_identidad': '90123456789',
            'numero_contribuyente': '1234567',
            'codigo_zpc': 'ZPC-001',
            'tipo_cuenta': 'natural',
        }

    def test_form_valido(self):
        form = ContribuyenteForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_carnet_identidad_exactamente_11(self):
        data = self.valid_data.copy()
        data['carnet_identidad'] = '1234567890'
        form = ContribuyenteForm(data=data)
        self.assertFalse(form.is_valid())

    def test_carnet_identidad_solo_digitos(self):
        data = self.valid_data.copy()
        data['carnet_identidad'] = '1234567890a'
        form = ContribuyenteForm(data=data)
        self.assertFalse(form.is_valid())

    def test_codigo_zpc_se_convierte_a_mayusculas(self):
        data = self.valid_data.copy()
        data['codigo_zpc'] = 'zpc-001'
        form = ContribuyenteForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['codigo_zpc'], 'ZPC-001')

    def test_numero_contribuyente_solo_digitos(self):
        data = self.valid_data.copy()
        data['numero_contribuyente'] = 'ABC123'
        form = ContribuyenteForm(data=data)
        self.assertFalse(form.is_valid())

    def test_campos_requeridos(self):
        form = ContribuyenteForm(data={})
        self.assertFalse(form.is_valid())
        required_fields = ['carnet_identidad', 'numero_contribuyente', 'codigo_zpc', 'tipo_cuenta']
        for field in required_fields:
            self.assertIn(field, form.errors)


class BusquedaFormTest(TestCase):
    def test_form_valido_vacio(self):
        form = BusquedaForm(data={})
        self.assertTrue(form.is_valid())

    def test_form_valido_con_q(self):
        form = BusquedaForm(data={'q': '123456'})
        self.assertTrue(form.is_valid())

    def test_form_valido_con_tipo_cuenta(self):
        form = BusquedaForm(data={'tipo_cuenta': 'natural'})
        self.assertTrue(form.is_valid())

    def test_form_valido_con_anio(self):
        form = BusquedaForm(data={'anio': 2026})
        self.assertTrue(form.is_valid())
