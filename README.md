# 🏥 MediCitas EPS

> Sistema web de gestión de citas médicas desarrollado con **Python + Flask + MySQL**.  
> Proyecto formativo del programa **Análisis y Desarrollo de Software (ADSO19) – SENA Colombia 🇨🇴**

---

## 📸 Vista previa

<!-- Reemplaza esta línea con una captura de pantalla de tu app en Railway -->
![MediCitas EPS – Página principal](https://img.shields.io/badge/Estado-En%20producción-10b981?style=for-the-badge)

---

## 📋 Descripción

**MediCitas EPS** es una aplicación web full-stack que digitaliza el proceso de agendamiento de citas médicas para una Entidad Promotora de Salud (EPS). Elimina los procesos manuales que generan pérdida de información, cruces de horarios y demoras en la atención.

El sistema implementa tres roles diferenciados con portales independientes, un motor de validación de conflictos de horario en tiempo real y un chatbot conversacional integrado en la página principal para el agendamiento asistido de citas.

---

## ✨ Funcionalidades principales

### 👤 Paciente
- Registro de cuenta con vinculación a EPS
- Reserva de citas médicas con selección de especialidad, médico, fecha y hora
- Validación automática de cruces de horario (sin solapamientos)
- Consulta, modificación y cancelación de citas activas
- Chatbot de agendamiento paso a paso desde la página principal

### 👨‍⚕️ Médico
- Agenda diaria con vista de línea de tiempo
- Consulta de historial completo de citas
- Detalle del paciente en cada cita
- Marcado de citas como completadas

### 🛡️ Administrador
- Panel de control con KPIs del sistema
- Gestión de catálogos: EPS, especialidades (con duración), médicos
- Vista global de todas las citas con cambio de estado
- Control de usuarios (activar / desactivar)

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.11+ · Flask 3.0 |
| **Base de datos** | MySQL 8.x |
| **ORM / Queries** | SQL nativo con `mysql-connector-python` |
| **Seguridad** | Werkzeug · hash `pbkdf2:sha256` |
| **Frontend** | HTML5 · CSS3 · JavaScript ES6 |
| **UI Framework** | Bootstrap 5.3 · Bootstrap Icons |
| **Motor de plantillas** | Jinja2 |
| **Tipografía** | Plus Jakarta Sans · DM Serif Display |
| **Despliegue** | Railway (PaaS) + MySQL integrado |

---

## 🗄️ Modelo de base de datos

```
usuarios ──┬── pacientes ──── citas ──┬── medicos ──── especialidades
           └── medicos               ├── pacientes
                                     ├── especialidades
                                     └── eps
```

**Tablas:** `usuarios` · `pacientes` · `medicos` · `especialidades` · `eps` · `citas`

### Validación de cruces de horario
Antes de crear o modificar una cita, el sistema verifica que no haya solapamiento usando la fórmula de intersección de intervalos:

```
A < D  AND  B > C
```
donde `[A, B]` es el nuevo intervalo y `[C, D]` es una cita activa existente.  
La verificación se aplica tanto al **médico** como al **paciente**.

---

## 📁 Estructura del proyecto

```
citas_medicas_flask/
├── app.py                    # Application Factory + seed DB
├── config.py                 # Configuración por entorno
├── requirements.txt
├── database/
│   └── conexion.py           # Factory de conexión MySQL
├── models/
│   ├── usuario_model.py      # Auth + hash de contraseñas
│   ├── catalogo_model.py     # EPS · especialidades · médicos
│   ├── paciente_model.py
│   └── cita_model.py         # CRUD + validación de cruces
├── routes/
│   ├── decoradores.py        # @login_required · @rol_requerido
│   ├── auth_routes.py        # /auth  – login · logout · registro
│   ├── admin_routes.py       # /admin – panel administrador
│   ├── medico_routes.py      # /medico – portal médico
│   ├── paciente_routes.py    # /paciente – portal paciente
│   └── chatbot_routes.py     # /chatbot – API REST del asistente
├── templates/
│   ├── base.html             # Layout maestro + chatbot widget
│   ├── index.html            # Landing page pública
│   ├── auth/                 # login · registro
│   ├── admin/                # dashboard · eps · especialidades · médicos · citas · usuarios
│   ├── medico/               # dashboard · horario · ver_cita
│   ├── paciente/             # dashboard · reservar · editar_cita
│   └── partials/             # macros Jinja2 reutilizables
├── static/
│   ├── css/
│   │   ├── style.css         # Estilos personalizados (800+ líneas)
│   │   └── chatbot.css       # Estilos del widget de chatbot
│   └── js/
│       ├── main.js           # Validaciones · UX cliente
│       └── chatbot.js        # Flujo del asistente paso a paso
└── sql/
    └── database.sql          # Script completo de creación de BD
```

---

## 🚀 Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/citas_medicas_flask.git
cd citas_medicas_flask

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# → editar .env con tus credenciales MySQL

# 5. Crear la base de datos
mysql -u root -p < sql/database.sql

# 6. Ejecutar
python app.py
# → http://localhost:5000
```

Al iniciar por primera vez se crea automáticamente el usuario administrador:

| Usuario | Contraseña |
|---------|-----------|
| `admin` | `Admin2025*` |

---

## ☁️ Despliegue en Railway

1. Conectar el repositorio de GitHub en [Railway](https://railway.app)
2. Agregar el servicio **MySQL** desde el panel
3. Configurar las variables de entorno en el servicio Flask:

```
FLASK_ENV       = production
SECRET_KEY      = (clave segura aleatoria)
MYSQL_HOST      = (desde Railway MySQL)
MYSQL_PORT      = (desde Railway MySQL)
MYSQL_USER      = (desde Railway MySQL)
MYSQL_PASSWORD  = (desde Railway MySQL)
MYSQL_DB        = eps_citas
```

Railway detecta `requirements.txt` e instala dependencias automáticamente.  
Al arrancar, la app crea la base de datos, las tablas y el usuario admin.

---

## 🔐 Roles y acceso

| Rol | URL | Acceso |
|-----|-----|--------|
| Administrador | `/admin/` | Panel total del sistema |
| Médico | `/medico/` | Agenda y atención |
| Paciente | `/paciente/` | Reservas y consultas |

Protegido con decoradores `@login_required` y `@rol_requerido(rol)`.

---

## 🤖 Chatbot de agendamiento

Widget flotante en la página principal que guía al paciente en 8 pasos:

```
Autenticación → Especialidad → Médico → EPS → Fecha → Hora → Motivo → Confirmación
```

- Lógica pura en Flask (sin IA externa ni costos adicionales)
- Validación de cruces de horario en tiempo real
- Muestra la EPS del paciente preseleccionada
- Permite corregir cualquier paso sin reiniciar
- Soporte para múltiples citas en la misma sesión

---

## 📦 Dependencias

```
Flask==3.0.3
mysql-connector-python==8.4.0
Werkzeug==3.0.3
python-dotenv==1.0.1
```

---

## 📄 Licencia

Proyecto educativo de uso libre desarrollado en el marco del programa  
**Análisis y Desarrollo de Software (ADSO19) — SENA Colombia**

---

<div align="center">
  Desarrollado con ❤️ · Python · Flask · MySQL · Bootstrap 5
</div>
