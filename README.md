# 🏥 MediCitas EPS – v2 (Roles + Catálogos + Validación de Horarios)

Sistema web de gestión de citas médicas con **tres roles**, catálogos administrables y detección automática de cruce de horarios.

---

## 🔐 Roles del sistema

| Rol | Acceso | Descripción |
|-----|--------|-------------|
| `admin` | `/admin/` | Gestión total: médicos, EPS, especialidades, usuarios, citas |
| `medico` | `/medico/` | Ver su agenda, marcar citas como completadas |
| `paciente` | `/paciente/` | Reservar, consultar, modificar y cancelar sus citas |

---

## 🗄️ Base de datos

### Tablas principales

| Tabla | Descripción |
|-------|-------------|
| `usuarios` | Acceso al sistema con rol |
| `pacientes` | Perfil del paciente vinculado a usuario |
| `medicos` | Perfil del médico vinculado a usuario y especialidad |
| `especialidades` | Catálogo de tipos de cita con duración en minutos |
| `eps` | Catálogo de EPS disponibles |
| `citas` | Citas médicas con `hora_inicio` y `hora_fin` calculada |

### Validación de cruce de horarios

El sistema verifica **dos condiciones** antes de crear o modificar una cita:

1. **Cruce del médico**: el médico no puede tener dos citas activas que se superpongan en el tiempo el mismo día.
2. **Cruce del paciente**: el paciente no puede tener dos citas activas solapadas el mismo día.

**Algoritmo** (intervalo [A, B] choca con [C, D] si `A < D AND B > C`):

```python
# En cita_model.py → verificar_cruce_medico / verificar_cruce_paciente
AND %s < c.hora_fin
AND %s > c.hora_inicio
```

Las citas **Canceladas** o **Completadas** NO bloquean el horario.

---

## 📁 Estructura del proyecto

```
citas_medicas_flask/
│
├── app.py                     ← Factory + seed admin
├── config.py
├── requirements.txt
├── .env.example
│
├── database/
│   └── conexion.py
│
├── models/
│   ├── usuario_model.py       ← Auth + hash de contraseñas
│   ├── catalogo_model.py      ← EPS, Especialidades, Médicos
│   ├── paciente_model.py
│   └── cita_model.py          ← CRUD + verificación de cruces
│
├── routes/
│   ├── decoradores.py         ← @login_required, @rol_requerido
│   ├── auth_routes.py         ← Login / Logout / Registro
│   ├── admin_routes.py        ← Panel administrador
│   ├── medico_routes.py       ← Portal médico
│   └── paciente_routes.py     ← Portal paciente + API AJAX
│
├── templates/
│   ├── base.html              ← Navbar dinámico por rol
│   ├── auth/                  ← login.html, registro.html
│   ├── admin/                 ← dashboard, eps, especialidades, médicos, citas, usuarios
│   ├── medico/                ← dashboard, horario, ver_cita
│   ├── paciente/              ← dashboard, reservar, editar_cita
│   ├── partials/              ← estado_badge.html
│   └── errors/                ← 403, 404, 500
│
├── static/
│   ├── css/style.css
│   └── js/main.js
│
└── sql/
    └── database.sql
```

---

## ⚙️ Instalación

```bash
# 1. Descomprimir y entrar al proyecto
unzip citas_medicas_flask_v2.zip
cd citas_medicas_flask_v2

# 2. Entorno virtual
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env
# Editar .env con tu contraseña MySQL

# 5. Crear base de datos
mysql -u root -p < sql/database.sql

# 6. Ejecutar
python app.py
```

Al arrancar, se crea automáticamente el usuario **admin** si no existe:
> `admin` / `Admin2025*`

---

## 🌐 Rutas principales

| Método | URL | Acceso |
|--------|-----|--------|
| GET/POST | `/auth/login` | Público |
| GET/POST | `/auth/registro` | Público (crea paciente) |
| GET | `/auth/logout` | Autenticado |
| GET | `/admin/` | admin |
| GET | `/admin/eps` | admin |
| GET | `/admin/especialidades` | admin |
| GET | `/admin/medicos` | admin |
| GET | `/admin/citas` | admin |
| GET | `/admin/usuarios` | admin |
| GET | `/medico/` | medico |
| GET | `/medico/horario` | medico |
| GET | `/paciente/` | paciente |
| GET/POST | `/paciente/reservar` | paciente |
| GET | `/paciente/api/medicos/<id>` | paciente (AJAX) |

---

## 🧪 Flujo de prueba recomendado

1. Inicia sesión como **admin** → crea una especialidad, una EPS y un médico.
2. Cierra sesión y **regístrate** como paciente.
3. Inicia sesión como **paciente** → reserva una cita.
4. Intenta reservar otra cita en el **mismo horario** → el sistema mostrará el conflicto.
5. Inicia sesión como el **médico** creado → verifica su agenda y marca una cita como completada.

---

## 👥 Créditos

Programa **Análisis y Desarrollo de Software – ADSO19 | SENA Colombia 🇨🇴**
