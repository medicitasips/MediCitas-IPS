"""
routes/chatbot_routes.py – API REST del chatbot de agendamiento.

Blueprint: 'chatbot'  |  prefijo URL: /chatbot
Todos los endpoints retornan JSON.
No requiere sesión Flask activa; el estado del flujo
se maneja en el cliente y en cada llamada.
"""

from flask import Blueprint, request, jsonify

from models.usuario_model   import verificar_credenciales
from models.paciente_model  import obtener_paciente_por_usuario
from models.catalogo_model  import (listar_especialidades, listar_eps,
                                     listar_medicos_por_especialidad,
                                     obtener_especialidad_por_id)
from models.cita_model      import crear_cita

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


def _str_hora(valor) -> str:
    import datetime
    if isinstance(valor, datetime.timedelta):
        total = int(valor.total_seconds())
        h, m  = divmod(total // 60, 60)
        return f"{h:02d}:{m:02d}"
    return str(valor)[:5] if valor else ""


@chatbot_bp.route("/auth", methods=["POST"])
def auth():
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


@chatbot_bp.route("/especialidades", methods=["GET"])
def especialidades():
    try:
        datos = listar_especialidades(solo_activas=True)
        return jsonify({
            "ok": True,
            "especialidades": [
                {"id": e["id_especialidad"], "nombre": e["nombre"], "duracion_min": e["duracion_min"]}
                for e in datos
            ],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@chatbot_bp.route("/medicos/<int:id_especialidad>", methods=["GET"])
def medicos(id_especialidad: int):
    try:
        datos = listar_medicos_por_especialidad(id_especialidad)
        return jsonify({
            "ok":     True,
            "medicos": [{"id": m["id_medico"], "nombre": m["nombre_completo"]} for m in datos],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@chatbot_bp.route("/eps", methods=["GET"])
def eps():
    try:
        datos = listar_eps(solo_activas=True)
        return jsonify({
            "ok":  True,
            "eps": [{"id": e["id_eps"], "nombre": e["nombre"]} for e in datos],
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@chatbot_bp.route("/agendar", methods=["POST"])
def agendar():
    data = request.get_json(silent=True) or {}

    required = ["id_paciente","id_medico","id_especialidad","id_eps","fecha","hora_inicio"]
    for campo in required:
        if not data.get(campo):
            return jsonify({"ok": False, "error": f"El campo '{campo}' es obligatorio."})

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
        cruce_serializado = []
        for c in resultado.get("cruce", []):
            cruce_serializado.append({
                k: _str_hora(v) if hasattr(v, "total_seconds") else v
                for k, v in c.items()
            })
        return jsonify({"ok": False, "error": resultado["error"], "cruce": cruce_serializado})

    from datetime import datetime, timedelta
    hora_fin_dt = (
        datetime.strptime(data["hora_inicio"], "%H:%M")
        + timedelta(minutes=esp["duracion_min"])
    )
    return jsonify({
        "ok":          True,
        "id_cita":     resultado["id"],
        "hora_inicio": data["hora_inicio"],
        "hora_fin":    hora_fin_dt.strftime("%H:%M"),
    })
