"""
routes/chatbot_routes.py – API REST del chatbot de agendamiento.

Blueprint: 'chatbot'  |  prefijo URL: /chatbot
Todos los endpoints retornan JSON.
No requiere sesión Flask activa; el estado del flujo
se maneja en el cliente (localStorage) y en cada llamada.
"""

from flask import Blueprint, request, jsonify

from models.usuario_model   import verificar_credenciales
from models.paciente_model  import obtener_paciente_por_usuario
from models.catalogo_model  import (listar_especialidades, listar_eps,
                                     listar_medicos_por_especialidad,
                                     obtener_especialidad_por_id)
from models.cita_model      import (crear_cita,
                                     disponibilidad_mes,
                                     slots_disponibles_dia)

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


# ── Helpers internos ──────────────────────────────────────────

def _str_hora(valor) -> str:
    """
    Convierte un timedelta (retornado por MySQL para TIME)
    o un string a formato HH:MM.
    """
    import datetime
    if isinstance(valor, datetime.timedelta):
        total = int(valor.total_seconds())
        h, m  = divmod(total // 60, 60)
        return f"{h:02d}:{m:02d}"
    return str(valor)[:5] if valor else ""


# ── 1. Autenticar paciente ─────────────────────────────────────

@chatbot_bp.route("/auth", methods=["POST"])
def auth():
    """
    Verifica credenciales y retorna el perfil del paciente.

    Body JSON:  { "username": "...", "password": "..." }
    Respuesta:
        ok=True  → { ok, id_paciente, nombre, apellido, id_eps, eps_nombre }
        ok=False → { ok, error }
    """
    data     = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"ok": False, "error": "Usuario y contraseña son obligatorios."})

    usuario = verificar_credenciales(username, password)
    if not usuario:
        return jsonify({"ok": False, "error": "Usuario o contraseña incorrectos."})

    if usuario["rol"] != "paciente":
        return jsonify({"ok": False, "error": "Este chatbot es exclusivo para pacientes."})

    perfil = obtener_paciente_por_usuario(usuario["id_usuario"])
    if not perfil:
        return jsonify({"ok": False, "error": "No se encontró el perfil del paciente."})

    return jsonify({
        "ok":          True,
        "id_paciente": perfil["id_paciente"],
        "nombre":      perfil["nombre"],
        "apellido":    perfil["apellido"],
        "id_eps":      perfil["id_eps"],
        "eps_nombre":  perfil["eps_nombre"],
    })


# ── 2. Listar especialidades ───────────────────────────────────

@chatbot_bp.route("/especialidades", methods=["GET"])
def especialidades():
    """
    Retorna la lista de especialidades activas.

    Respuesta: { ok, especialidades: [{id, nombre, duracion_min}] }
    """
    try:
        datos = listar_especialidades(solo_activas=True)
        return jsonify({
            "ok": True,
            "especialidades": [
                {
                    "id":           e["id_especialidad"],
                    "nombre":       e["nombre"],
                    "duracion_min": e["duracion_min"],
                }
                for e in datos
            ],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── 3. Listar médicos por especialidad ─────────────────────────

@chatbot_bp.route("/medicos/<int:id_especialidad>", methods=["GET"])
def medicos(id_especialidad: int):
    """
    Retorna los médicos activos de una especialidad.

    Respuesta: { ok, medicos: [{id, nombre_completo}] }
    """
    try:
        datos = listar_medicos_por_especialidad(id_especialidad)
        return jsonify({
            "ok":     True,
            "medicos": [
                {"id": m["id_medico"], "nombre": m["nombre_completo"]}
                for m in datos
            ],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── 4. Listar EPS ──────────────────────────────────────────────

@chatbot_bp.route("/eps", methods=["GET"])
def eps():
    """
    Retorna la lista de EPS activas.

    Respuesta: { ok, eps: [{id, nombre}] }
    """
    try:
        datos = listar_eps(solo_activas=True)
        return jsonify({
            "ok":  True,
            "eps": [{"id": e["id_eps"], "nombre": e["nombre"]} for e in datos],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── 5. Crear cita ──────────────────────────────────────────────

@chatbot_bp.route("/agendar", methods=["POST"])
def agendar():
    """
    Crea la cita médica con validación de cruce de horario.

    Body JSON:
    {
        "id_paciente":     int,
        "id_medico":       int,
        "id_especialidad": int,
        "id_eps":          int,
        "fecha":           "YYYY-MM-DD",
        "hora_inicio":     "HH:MM",
        "motivo":          "..." (opcional)
    }

    Respuesta éxito:  { ok: true, id_cita, hora_inicio, hora_fin }
    Respuesta error:  { ok: false, error, cruce (opcional) }
    """
    data = request.get_json(silent=True) or {}

    # Validar campos obligatorios
    required = ["id_paciente","id_medico","id_especialidad","id_eps","fecha","hora_inicio"]
    for campo in required:
        if not data.get(campo):
            return jsonify({"ok": False, "error": f"El campo '{campo}' es obligatorio."})

    # Obtener duración de la especialidad
    esp = obtener_especialidad_por_id(int(data["id_especialidad"]))
    if not esp:
        return jsonify({"ok": False, "error": "Especialidad no encontrada."})

    resultado = crear_cita(
        id_paciente     = int(data["id_paciente"]),
        id_medico       = int(data["id_medico"]),
        id_especialidad = int(data["id_especialidad"]),
        id_eps          = int(data["id_eps"]),
        fecha           = data["fecha"],
        hora_inicio     = data["hora_inicio"],
        duracion_min    = esp["duracion_min"],
        motivo          = data.get("motivo", ""),
    )

    if not resultado["ok"]:
        # Serializar timedelta en los objetos de cruce si existen
        cruce_serializado = []
        for c in resultado.get("cruce", []):
            cruce_serializado.append({
                k: _str_hora(v) if hasattr(v, "total_seconds") else v
                for k, v in c.items()
            })
        return jsonify({
            "ok":    False,
            "error": resultado["error"],
            "cruce": cruce_serializado,
        })

    # Calcular hora_fin para mostrar en la confirmación
    from datetime import datetime, timedelta
    hora_fin_dt = (
        datetime.strptime(data["hora_inicio"], "%H:%M")
        + timedelta(minutes=esp["duracion_min"])
    )

    return jsonify({
        "ok":         True,
        "id_cita":    resultado["id"],
        "hora_inicio": data["hora_inicio"],
        "hora_fin":    hora_fin_dt.strftime("%H:%M"),
    })


# ── 6. Disponibilidad mensual (sin sesión Flask) ───────────────

@chatbot_bp.route("/disponibilidad/<int:id_medico>/<int:anio>/<int:mes>", methods=["GET"])
def chatbot_disponibilidad_mes(id_medico, anio, mes):
    """
    Igual que /paciente/api/disponibilidad pero sin @login_required.
    El chatbot maneja su propia autenticación.

    Query param: duracion (int, minutos)
    Respuesta: { "2026-03-01": "disponible", ... }
    """
    duracion = int(request.args.get("duracion", 30))
    try:
        datos = disponibilidad_mes(id_medico, anio, mes, duracion)
        return jsonify(datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── 7. Slots disponibles del día (sin sesión Flask) ────────────

@chatbot_bp.route("/slots/<int:id_medico>/<fecha>", methods=["GET"])
def chatbot_slots_dia(id_medico, fecha):
    """
    Igual que /paciente/api/slots pero sin @login_required.

    Query param: duracion (int, minutos)
    Respuesta: { "slots": ["08:00", "08:30", ...] }
    """
    duracion = int(request.args.get("duracion", 30))
    try:
        slots = slots_disponibles_dia(id_medico, fecha, duracion)
        return jsonify({"slots": slots})
    except Exception as e:
        return jsonify({"slots": [], "error": str(e)}), 500
