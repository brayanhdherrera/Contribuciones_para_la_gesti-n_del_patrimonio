from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..models import Contribucion, Contribuyente, OBLIGACION_PAGO_CHOICES

User = get_user_model()


class ContribuyenteModelTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'carnet_identidad': '90123456789',
            'numero_contribuyente': '1234567',
            'codigo_zpc': 'ZPC-001',
            'tipo_cuenta': 'natural',
        }

    def test_crear_contribuyente_valido(self):
        c = Contribuyente.objects.create(**self.valid_data)
        self.assertEqual(c.carnet_identidad, '90123456789')
        self.assertEqual(c.numero_contribuyente, '1234567')
        self.assertEqual(c.codigo_zpc, 'ZPC-001')
        self.assertEqual(c.tipo_cuenta, 'natural')
        self.assertIsNotNone(c.fecha_registro)
        self.assertIsNotNone(c.fecha_modificacion)

    def test_carnet_identidad_unico(self):
        Contribuyente.objects.create(**self.valid_data)
        with self.assertRaises(Exception):
            Contribuyente.objects.create(**self.valid_data)

    def test_carnet_identidad_invalido(self):
        data = self.valid_data.copy()
        data['carnet_identidad'] = '12345'
        with self.assertRaises(ValidationError):
            c = Contribuyente(**data)
            c.full_clean()

    def test_numero_contribuyente_unico(self):
        Contribuyente.objects.create(**self.valid_data)
        data = self.valid_data.copy()
        data['carnet_identidad'] = '98765432109'
        data['numero_contribuyente'] = '1234567'
        with self.assertRaises(Exception):
            Contribuyente.objects.create(**data)

    def test_str_representation(self):
        c = Contribuyente.objects.create(**self.valid_data)
        self.assertIn('1234567', str(c))
        self.assertIn('90123456789', str(c))

    def test_ordering(self):
        c1 = Contribuyente.objects.create(
            carnet_identidad='11111111111', numero_contribuyente='1',
            codigo_zpc='ZPC-001', tipo_cuenta='natural',
        )
        c2 = Contribuyente.objects.create(
            carnet_identidad='22222222222', numero_contribuyente='2',
            codigo_zpc='ZPC-002', tipo_cuenta='fiscal',
        )
        qs = Contribuyente.objects.all()
        self.assertEqual(qs[0], c2)
        self.assertEqual(qs[1], c1)

    def test_codigo_zpc_invalido(self):
        data = self.valid_data.copy()
        data['codigo_zpc'] = '¡invalido!'
        with self.assertRaises(ValidationError):
            c = Contribuyente(**data)
            c.full_clean()


class ContribucionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.valid_data = {
            'obligacion_pago': 'contribucion_mensual_patrimonio',
            'numero_identidad': '90123456789',
            'numero_afiliado': '1234567',
            'codigo_zpc': 'ZPC-001',
            'periodo_mes': 3,
            'periodo_anio': 2024,
            'monto_cup': 1500.00,
            'tipo_cuenta': 'natural',
            'registrado_por': self.user,
        }

    def test_crear_contribucion_valida(self):
        c = Contribucion.objects.create(**self.valid_data)
        self.assertEqual(c.obligacion_pago, 'contribucion_mensual_patrimonio')
        self.assertEqual(c.numero_identidad, '90123456789')
        self.assertEqual(c.monto_cup, 1500.00)
        self.assertIsNotNone(c.fecha_registro)
        self.assertIsNotNone(c.fecha_modificacion)

    def test_obligacion_pago_choices(self):
        choices = dict(OBLIGACION_PAGO_CHOICES)
        self.assertIn('contribucion_mensual_patrimonio', choices)
        self.assertIn('donaciones', choices)
        c = Contribucion.objects.create(**self.valid_data)
        self.assertEqual(c.get_obligacion_pago_display(), 'Contribución mensual patrimonio')

    def test_obligacion_pago_donaciones(self):
        data = self.valid_data.copy()
        data['obligacion_pago'] = 'donaciones'
        c = Contribucion.objects.create(**data)
        self.assertEqual(c.get_obligacion_pago_display(), 'Donaciones')

    def test_monto_minimo_validator(self):
        data = self.valid_data.copy()
        data['monto_cup'] = 0
        with self.assertRaises(ValidationError):
            c = Contribucion(**data)
            c.full_clean()

    def test_periodo_anio_minimo(self):
        data = self.valid_data.copy()
        data['periodo_anio'] = 1999
        with self.assertRaises(ValidationError):
            c = Contribucion(**data)
            c.full_clean()

    def test_str_representation(self):
        c = Contribucion.objects.create(**self.valid_data)
        self.assertIn('1234567', str(c))
        self.assertIn('1500', str(c))

    def test_periodo_display_property(self):
        c = Contribucion.objects.create(**self.valid_data)
        self.assertIn('Marzo', c.periodo_display)
        self.assertIn('2024', c.periodo_display)

    def test_numero_identidad_solo_digitos(self):
        data = self.valid_data.copy()
        data['numero_identidad'] = '12345abcde'
        with self.assertRaises(ValidationError):
            c = Contribucion(**data)
            c.full_clean()

    def test_numero_afiliado_acepta_alfanumerico(self):
        data = self.valid_data.copy()
        data['numero_afiliado'] = 'ABC-123'
        c = Contribucion(**data)
        c.full_clean()
        self.assertEqual(c.numero_afiliado, 'ABC-123')

    def test_codigo_zpc_formato_valido(self):
        codigos_validos = ['ZPC-001', 'ABC123', 'X-99', 'TEST-CODE']
        for codigo in codigos_validos:
            data = self.valid_data.copy()
            data['codigo_zpc'] = codigo
            try:
                c = Contribucion(**data)
                c.full_clean()
            except ValidationError:
                self.fail(f'Código ZPC válido {codigo!r} lanzó ValidationError')

    def test_codigo_zpc_formato_invalido(self):
        data = self.valid_data.copy()
        data['codigo_zpc'] = 'AB'
        with self.assertRaises(ValidationError):
            c = Contribucion(**data)
            c.full_clean()

    def test_ordering(self):
        Contribucion.objects.create(**self.valid_data)
        c2_data = self.valid_data.copy()
        c2_data['numero_afiliado'] = '999999'
        c2 = Contribucion.objects.create(**c2_data)
        qs = Contribucion.objects.all()
        self.assertEqual(qs[0], c2)

    def test_registrado_por_nullable(self):
        data = self.valid_data.copy()
        data['registrado_por'] = None
        c = Contribucion.objects.create(**data)
        self.assertIsNone(c.registrado_por)

    def test_tipo_cuenta_choices(self):
        c = Contribucion.objects.create(**self.valid_data)
        self.assertEqual(c.get_tipo_cuenta_display(), 'Natural')

    def test_fecha_registro_default(self):
        c = Contribucion.objects.create(**self.valid_data)
        self.assertIsNotNone(c.fecha_registro)
