# 🏛 Sistema de Gestión de Contribuciones al Patrimonio

Backend Django + PostgreSQL — CRUD completo con autenticación, admin personalizado y exportación CSV.

---

## 📁 Estructura del proyecto

```
patrimonio_project/
│
├── manage.py
├── requirements.txt
├── .env.example                 ← Copiar a .env y configurar
├── README.md
│
├── patrimonio_project/          ← Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py              ← PostgreSQL, auth, static, mensajes
│   ├── urls.py                  ← Rutas raíz + header admin personalizado
│   └── wsgi.py
│
├── contribuciones/              ← App principal
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                ← Modelo Contribucion + validators + índices
│   ├── forms.py                 ← ContribucionForm + BusquedaForm
│   ├── views.py                 ← CRUD CBV + exportar_csv()
│   ├── urls.py                  ← 6 rutas (namespace: contribuciones)
│   ├── admin.py                 ← Admin completo + acción CSV
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── contribuciones_extras.py  ← Filtros: add_class, query_transform
│   └── templates/
│       └── contribuciones/
│           ├── contribucion_list.html
│           ├── contribucion_form.html
│           ├── contribucion_detail.html
│           └── contribucion_confirm_delete.html
│
└── templates/                   ← Templates globales
    ├── base.html                ← Layout responsive completo (sin frameworks externos)
    └── registration/
        └── login.html           ← Override del login nativo de Django
```

---

## ⚙ Requisitos previos

| Requisito  | Versión mínima |
|------------|---------------|
| Python     | 3.10+         |
| Django     | 4.2           |
| PostgreSQL | 14+           |
| pip        | cualquiera    |

---

## 🚀 Instalación paso a paso

### 1. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate          # Linux / macOS
venv\Scripts\activate             # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env`:

```env
# Generar con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=tu-clave-secreta-generada

DEBUG=True
DB_NAME=patrimonio_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Crear la base de datos en PostgreSQL

```sql
-- Desde psql o pgAdmin:
CREATE DATABASE patrimonio_db;
```

O desde terminal:

```bash
createdb -U postgres patrimonio_db
```

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario (acceso al Admin)

```bash
python manage.py createsuperuser
```

### 7. Ejecutar el servidor

```bash
python manage.py runserver
```

Abrir en el navegador: **http://localhost:8000**

---

## 🌐 URLs disponibles

| URL                                    | Vista                | Auth |
|----------------------------------------|----------------------|:----:|
| `/`                                    | → redirige al listado | ✓   |
| `/accounts/login/`                     | Login                | ✗    |
| `/accounts/logout/`                    | Logout (POST)        | ✓    |
| `/contribuciones/`                     | Listado + filtros    | ✓    |
| `/contribuciones/nueva/`               | Crear contribución   | ✓    |
| `/contribuciones/<id>/`                | Detalle              | ✓    |
| `/contribuciones/<id>/editar/`         | Editar               | ✓    |
| `/contribuciones/<id>/eliminar/`       | Eliminar             | ✓    |
| `/contribuciones/exportar/csv/`        | Descarga CSV         | ✓    |
| `/admin/`                              | Panel Django Admin   | Staff|

---

## 📋 Campos del modelo Contribucion

| Campo                      | Tipo BD             | Validaciones                                          |
|----------------------------|---------------------|-------------------------------------------------------|
| `obligacion_pago`          | VARCHAR(100)        | Obligatorio                                           |
| `numero_identidad`         | VARCHAR(11)         | Obligatorio, exactamente 11 dígitos                   |
| `numero_contribuyente_ofa` | VARCHAR(50)         | Obligatorio, solo dígitos                             |
| `codigo_zpc`               | VARCHAR(20)         | Obligatorio, A-Z 0-9 guiones, 3–20 chars             |
| `periodo_mes`              | SMALLINT (choices)  | Obligatorio, 1–12, no período futuro                  |
| `periodo_anio`             | SMALLINT            | Obligatorio, 2000 ≤ año ≤ año actual                 |
| `monto_cup`                | DECIMAL(12,2)       | Obligatorio, > 0                                      |
| `tipo_cuenta`              | VARCHAR(20) choices | corriente / ahorro / fiscal / especial               |
| `registrado_por`           | FK → User           | Set null on delete, asignado automáticamente          |
| `fecha_registro`           | TIMESTAMPTZ         | Auto, editable=False                                  |
| `fecha_modificacion`       | TIMESTAMPTZ         | auto_now                                              |

---

## 🔍 Funcionalidades incluidas

### CRUD completo
- **Listar**: tabla paginada (15/pág), con búsqueda por identidad/OFA/ZPC/obligación y filtros por tipo de cuenta y año.
- **Crear**: formulario con validaciones de modelo y de negocio. Asigna `registrado_por` automáticamente.
- **Editar**: mismo formulario, relleno con datos existentes.
- **Eliminar**: página de confirmación con resumen del registro.
- **Detalle**: vista de solo lectura con todos los campos.

### Exportación CSV
- Botón en el listado que exporta los registros **con los filtros activos**.
- Acción de admin para exportar una selección.
- BOM UTF-8 incluido para compatibilidad con Excel.

### Autenticación
- Todas las vistas requieren login (`LoginRequiredMixin` / `@login_required`).
- Redirección automática al login si no autenticado.
- Login/logout con el sistema nativo de Django.

### Admin personalizado
- Columnas, búsqueda, filtros, fieldsets por secciones.
- Campos de auditoría en sección colapsable.
- Acción "Exportar selección a CSV".
- Título y cabeceras del admin personalizados.

### Template tags
- `query_transform`: preserva parámetros GET en la paginación (filtros + página combinados).
- `add_class`: añadir clases CSS a campos de formulario desde templates.

---

## 🔒 Notas para producción

```bash
# 1. Cambiar en .env:
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com

# 2. Recolectar estáticos:
python manage.py collectstatic

# 3. Usar Gunicorn:
pip install gunicorn
gunicorn patrimonio_project.wsgi:application --bind 0.0.0.0:8000

# 4. Configurar Nginx como proxy inverso para /static/
```

---

## 🧪 Comandos útiles

```bash
# Crear migraciones nuevas tras cambiar models.py
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Shell interactivo de Django
python manage.py shell

# Ver todas las URLs registradas
python manage.py show_urls   # requiere django-extensions

# Cargar datos de prueba (si creas fixtures)
python manage.py loaddata fixtures/contribuciones_sample.json
```
