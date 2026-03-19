"""
routes/paciente_routes.py – Portal del paciente.

Blueprint: 'paciente'  |  prefijo URL: /paciente
Acceso: solo rol 'paciente'
"""

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)

from routes.decoradores    import login_required, rol_requerido
from models.paciente_model import obtener_paciente_por_usuario, actualizar_paciente
from models.cita_model     import (citas_por_paciente, crear_cita,
                                    obtener_cita_por_id, actualizar_cita,
                                    cambiar_estado_cita,
                                    disponibilidad_mes, slots_disponibles_dia)
from models.catalogo_model import (listar_especialidades, listar_eps,
                                    listar_medicos_por_especialidad,
                                    obtener_especialidad_por_id,
                                    listar_medicos)

paciente_bp = Blueprint("paciente", __name__, url_prefix="/paciente")


# ── Dashboard ─────────────────────────────────────────────────

@paciente_bp.route("/")
@login_required
@rol_requerido("paciente")
def dashboard():
    perfil = obtener_paciente_por_usuario(session["id_usuario"])
    if not perfil:
        flash("Completa tu perfil para continuar.", "warning")
        return redirect(url_for("auth.registro"))
    citas = citas_por_paciente(perfil["id_paciente"])
    return render_template("paciente/dashboard.html",
                           perfil=perfil, citas=citas)


# ── Reservar cita ─────────────────────────────────────────────

@paciente_bp.route("/reservar", methods=["GET", "POST"])
@login_required
@rol_requerido("paciente")
def reservar():
    perfil         = obtener_paciente_por_usuario(session["id_usuario"])
    especialidades = listar_especialidades()
    eps_lista      = listar_eps()

    if not perfil:
        flash("Perfil no encontrado.", "danger")
        return redirect(url_for("paciente.dashboard"))

    if request.method == "POST":
        id_especialidad = int(request.form.get("id_especialidad", 0))
        id_medico       = int(request.form.get("id_medico",       0))
        id_eps          = int(request.form.get("id_eps",          0))
        fecha           = request.form.get("fecha",      "").strip()
        hora_inicio     = request.form.get("hora_inicio","").strip()
        motivo          = request.form.get("motivo",     "").strip()

        # Validación básica
        if not all([id_especialidad, id_medico, id_eps, fecha, hora_inicio]):
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("paciente/reservar.html",
                                   perfil=perfil,
                                   especialidades=especialidades,
                                   eps_lista=eps_lista,
                                   form_data=request.form)

        especialidad = obtener_especialidad_por_id(id_especialidad)
        duracion     = especialidad["duracion_min"] if especialidad else 30

        resultado = crear_cita(
            id_paciente     = perfil["id_paciente"],
            id_medico       = id_medico,
            id_especialidad = id_especialidad,
            id_eps          = id_eps,
            fecha           = fecha,
            hora_inicio     = hora_inicio,
            duracion_min    = duracion,
            motivo          = motivo,
        )

        if resultado["ok"]:
            flash("¡Cita reservada exitosamente!", "success")
            return redirect(url_for("paciente.dashboard"))
        else:
            flash(f"No se pudo reservar: {resultado['error']}", "danger")
            # Mostrar detalles del cruce si los hay
            cruce = resultado.get("cruce", [])
            return render_template("paciente/reservar.html",
                                   perfil=perfil,
                                   especialidades=especialidades,
                                   eps_lista=eps_lista,
                                   form_data=request.form,
                                   cruce=cruce)

    return render_template("paciente/reservar.html",
                           perfil=perfil,
                           especialidades=especialidades,
                           eps_lista=eps_lista,
                           form_data={},
                           cruce=[])


# ── Actualizar cita ───────────────────────────────────────────

@paciente_bp.route("/cita/editar/<int:id_cita>", methods=["GET", "POST"])
@login_required
@rol_requerido("paciente")
def editar_cita(id_cita):
    perfil = obtener_paciente_por_usuario(session["id_usuario"])
    cita   = obtener_cita_por_id(id_cita)

    if not cita or cita["id_paciente"] != perfil["id_paciente"]:
        flash("Cita no encontrada o sin permiso.", "danger")
        return redirect(url_for("paciente.dashboard"))

    if cita["estado"] != "Activa":
        flash("Solo puedes editar citas activas.", "warning")
        return redirect(url_for("paciente.dashboard"))

    especialidades = listar_especialidades()
    eps_lista      = listar_eps()

    if request.method == "POST":
        id_especialidad = int(request.form.get("id_especialidad", cita["id_especialidad"]))
        id_medico       = int(request.form.get("id_medico",       cita["id_medico"]))
        id_eps          = int(request.form.get("id_eps",          cita["id_eps"]))
        fecha           = request.form.get("fecha",       "").strip()
        hora_inicio     = request.form.get("hora_inicio", "").strip()
        motivo          = request.form.get("motivo",      "").strip()

        especialidad = obtener_especialidad_por_id(id_especialidad)
        duracion     = especialidad["duracion_min"] if especialidad else 30

        resultado = actualizar_cita(
            id_cita         = id_cita,
            id_medico       = id_medico,
            id_especialidad = id_especialidad,
            id_eps          = id_eps,
            fecha           = fecha,
            hora_inicio     = hora_inicio,
            duracion_min    = duracion,
            motivo          = motivo,
            id_paciente     = perfil["id_paciente"],
        )

        if resultado["ok"]:
            flash("Cita actualizada correctamente.", "success")
            return redirect(url_for("paciente.dashboard"))
        else:
            flash(f"No se pudo actualizar: {resultado['error']}", "danger")

    medicos = listar_medicos_por_especialidad(cita["id_especialidad"])
    return render_template("paciente/editar_cita.html",
                           cita=cita,
                           especialidades=especialidades,
                           eps_lista=eps_lista,
                           medicos=medicos)


# ── Cancelar cita ─────────────────────────────────────────────

@paciente_bp.route("/cita/cancelar/<int:id_cita>", methods=["POST"])
@login_required
@rol_requerido("paciente")
def cancelar_cita(id_cita):
    perfil = obtener_paciente_por_usuario(session["id_usuario"])
    cita   = obtener_cita_por_id(id_cita)

    if not cita or cita["id_paciente"] != perfil["id_paciente"]:
        flash("Cita no encontrada o sin permiso.", "danger")
    else:
        r = cambiar_estado_cita(id_cita, "Cancelada")
        flash("Cita cancelada." if r["ok"] else f"Error: {r['error']}",
              "success" if r["ok"] else "danger")

    return redirect(url_for("paciente.dashboard"))


# ── Editar perfil del paciente ────────────────────────────────

@paciente_bp.route("/perfil/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("paciente")
def editar_perfil():
    perfil    = obtener_paciente_por_usuario(session["id_usuario"])
    eps_lista = listar_eps()

    if not perfil:
        flash("Perfil no encontrado.", "danger")
        return redirect(url_for("paciente.dashboard"))

    if request.method == "POST":
        telefono = request.form.get("telefono", "").strip()
        correo   = request.form.get("correo",   "").strip()
        id_eps   = int(request.form.get("id_eps", 0))

        errores = []
        if not telefono:
            errores.append("El teléfono es obligatorio.")
        if not correo or "@" not in correo:
            errores.append("Ingresa un correo electrónico válido.")
        if not id_eps:
            errores.append("Selecciona una EPS.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("paciente/editar_perfil.html",
                                   perfil=perfil, eps_lista=eps_lista)

        resultado = actualizar_paciente(perfil["id_paciente"], telefono, correo, id_eps)

        if resultado["ok"]:
            flash("¡Perfil actualizado correctamente!", "success")
            return redirect(url_for("paciente.dashboard"))
        else:
            flash(f"Error al actualizar: {resultado['error']}", "danger")

    return render_template("paciente/editar_perfil.html",
                           perfil=perfil, eps_lista=eps_lista)


# ── API: médicos por especialidad (AJAX) ──────────────────────

@paciente_bp.route("/api/medicos/<int:id_especialidad>")
@login_required
@rol_requerido("paciente")
def api_medicos(id_especialidad):
    from flask import jsonify
    medicos = listar_medicos_por_especialidad(id_especialidad)
    return jsonify(medicos)


# ── API: disponibilidad mensual del médico (AJAX) ─────────────

@paciente_bp.route("/api/disponibilidad/<int:id_medico>/<int:anio>/<int:mes>")
@login_required
@rol_requerido("paciente")
def api_disponibilidad_mes(id_medico, anio, mes):
    """
    Retorna el estado de disponibilidad de cada día del mes.

    Query param: duracion (int, minutos de la especialidad)
    Respuesta: { "2026-03-01": "disponible", "2026-03-02": "lleno", ... }
    """
    from flask import jsonify, request as req
    duracion = int(req.args.get("duracion", 30))
    datos = disponibilidad_mes(id_medico, anio, mes, duracion)
    return jsonify(datos)


# ── API: slots disponibles de un día concreto (AJAX) ──────────

@paciente_bp.route("/api/slots/<int:id_medico>/<fecha>")
@login_required
@rol_requerido("paciente")
def api_slots_dia(id_medico, fecha):
    """
    Retorna los horarios disponibles de un médico en una fecha.

    Query param: duracion (int, minutos)
    Respuesta: { "slots": ["08:00", "08:30", ...] }
    """
    from flask import jsonify, request as req
    duracion = int(req.args.get("duracion", 30))
    slots = slots_disponibles_dia(id_medico, fecha, duracion)
    return jsonify({"slots": slots})
