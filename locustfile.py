import random
import re
from locust import HttpUser, task, between
from django.utils import timezone


MESES = list(range(1, 13))
OBLIGACIONES = ['contribucion', 'donacion']
TIPO_CUENTA = ['natural', 'fiscal']
ZPC_CODES = ['ZPC-001', 'ZPC-002', 'ZPC-003', 'ZPC-004', 'ZPC-005']


def fake_ci():
    return f"{random.randint(10000000, 99999999)}{random.randint(10, 99):02d}"


def fake_afiliado():
    return str(random.randint(100000, 999999))


def fake_zpc():
    return random.choice(ZPC_CODES)


def fake_monto():
    return round(random.uniform(100.0, 5000.0), 2)


class ContribucionesUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://localhost:8000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.verify = False
        self.csrf_token = None
        self.logged_in = False
        self.known_contribucion_pks = []
        self.known_contribuyente_pks = []

    def _extract_csrf(self, text):
        match = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            text
        )
        if match:
            return match.group(1)
        match = re.search(
            r'csrfmiddlewaretoken=([^;&]+)',
            text
        )
        if match:
            return match.group(1)
        return None

    def on_start(self):
        resp = self.client.get("/accounts/login/")
        self.csrf_token = self._extract_csrf(resp.text)
        if not self.csrf_token:
            resp = self.client.get("/accounts/login/")
            self.csrf_token = self._extract_csrf(resp.text)

        login_resp = self.client.post(
            "/accounts/login/",
            data={
                "username": "admin",
                "password": "admin123",
                "csrfmiddlewaretoken": self.csrf_token,
            },
            headers={"Referer": "/accounts/login/"},
        )
        self.logged_in = "Sesión iniciada" in login_resp.text or login_resp.status_code == 200 and "/accounts/login/" not in login_resp.url

        if self.logged_in:
            dash_resp = self.client.get("/contribuciones/")
            if dash_resp.status_code == 200:
                pks = re.findall(r'/contribuciones/(\d+)/', dash_resp.text)
                self.known_contribucion_pks = list(set(pks))[:20]

    def _ensure_logged_in(self):
        if not self.logged_in:
            self.on_start()
        return self.logged_in

    @task(25)
    def view_dashboard(self):
        if not self._ensure_logged_in():
            return
        self.client.get("/contribuciones/", name="/contribuciones/ (dashboard)")

    @task(20)
    def view_contribuciones_list(self):
        if not self._ensure_logged_in():
            return
        self.client.get("/contribuciones/lista/", name="/contribuciones/lista/")

    @task(10)
    def view_contribuciones_list_page2(self):
        if not self._ensure_logged_in():
            return
        self.client.get(
            "/contribuciones/lista/?page=2",
            name="/contribuciones/lista/ (paginated)",
        )

    @task(15)
    def view_contribucion_detail(self):
        if not self._ensure_logged_in():
            return
        if self.known_contribucion_pks:
            pk = random.choice(self.known_contribucion_pks)
            self.client.get(
                f"/contribuciones/{pk}/",
                name="/contribuciones/[pk]/",
            )

    @task(8)
    def view_contribuyentes_list(self):
        if not self._ensure_logged_in():
            return
        self.client.get(
            "/contribuciones/contribuyentes/",
            name="/contribuciones/contribuyentes/",
        )

    @task(8)
    def search_contribuyente(self):
        if not self._ensure_logged_in():
            return
        term = str(random.randint(10000000, 99999999))
        self.client.get(
            f"/contribuciones/buscar-contribuyente/?q={term}",
            name="/contribuciones/buscar-contribuyente/ (autocomplete)",
        )

    @task(5)
    def view_create_contribucion_form(self):
        if not self._ensure_logged_in():
            return
        resp = self.client.get(
            "/contribuciones/nueva/",
            name="/contribuciones/nueva/ (GET form)",
        )
        self.csrf_token = self._extract_csrf(resp.text) or self.csrf_token

    @task(3)
    def create_contribucion(self):
        if not self._ensure_logged_in():
            return
        resp = self.client.get("/contribuciones/nueva/")
        token = self._extract_csrf(resp.text)
        if not token:
            return
        self.client.post(
            "/contribuciones/nueva/",
            data={
                "csrfmiddlewaretoken": token,
                "obligacion_pago": random.choice(OBLIGACIONES),
                "numero_identidad": fake_ci(),
                "numero_afiliado": fake_afiliado(),
                "codigo_zpc": fake_zpc(),
                "periodo_mes": random.choice(MESES),
                "periodo_anio": 2025,
                "monto_cup": str(fake_monto()),
                "tipo_cuenta": random.choice(TIPO_CUENTA),
            },
            headers={"Referer": "/contribuciones/nueva/"},
            name="/contribuciones/nueva/ (POST create)",
        )

    @task(3)
    def export_csv(self):
        if not self._ensure_logged_in():
            return
        self.client.get(
            "/contribuciones/exportar/csv/",
            name="/contribuciones/exportar/csv/",
        )

    @task(5)
    def view_contribuyente_detail(self):
        if not self._ensure_logged_in():
            return
        if self.known_contribuyente_pks:
            pk = random.choice(self.known_contribuyente_pks)
            self.client.get(
                f"/contribuciones/contribuyentes/{pk}/",
                name="/contribuciones/contribuyentes/[pk]/",
            )
