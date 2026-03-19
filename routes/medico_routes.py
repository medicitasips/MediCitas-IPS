"""
routes/medico_routes.py – Portal del médico.

Blueprint: 'medico'  |  prefijo URL: /medico
Acceso: solo rol 'medico'
"""

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, session)

from routes.decoradores    import login_required, rol_requerido
from models.catalogo_model import obtener_medico_por_usuario
from models.cita_model     import (citas_por_medico, obtener_cita_por_id,
                                    cambiar_estado_cita, horario_del_dia,
                                    historial_paciente)
from models.nota_model     import crear_nota, obtener_nota_por_cita
from models.paciente_model import obtener_paciente_por_usuario

medico_bp = Blueprint("medico", __name__, url_prefix="/medico")


# ── Dashboard ─────────────────────────────────────────────────

@medico_bp.route("/")
@login_required
@rol_requerido("medico")
def dashboard():
    perfil = obtener_medico_por_usuario(session["id_usuario"])
    if not perfil:
        flash("Perfil médico no encontrado. Contacte al administrador.", "warning")
        return redirect(url_for("auth.login"))

    from datetime import date
    hoy         = date.today().isoformat()
    citas_hoy   = horario_del_dia(perfil["id_medico"], hoy)
    todas_citas = citas_por_medico(perfil["id_medico"])

    return render_template("medico/dashboard.html",
                           perfil=perfil,
                           citas_hoy=citas_hoy,
                           todas_citas=todas_citas,
                           hoy=hoy)


# ── Ver detalle de cita ────────────────────────────────────────

@medico_bp.route("/cita/<int:id_cita>")
@login_required
@rol_requerido("medico")
def ver_cita(id_cita):
    perfil = obtener_medico_por_usuario(session["id_usuario"])
    cita   = obtener_cita_por_id(id_cita)

    if not cita or cita["id_medico"] != perfil["id_medico"]:
        flash("Cita no encontrada o sin permiso.", "danger")
        return redirect(url_for("medico.dashboard"))

    nota = obtener_nota_por_cita(id_cita)
    return render_template("medico/ver_cita.html",
                           cita=cita, perfil=perfil, nota=nota)


# ── Formulario para completar cita + nota ─────────────────────

@medico_bp.route("/cita/completar/<int:id_cita>", methods=["GET", "POST"])
@login_required
@rol_requerido("medico")
def completar_cita(id_cita):
    perfil = obtener_medico_por_usuario(session["id_usuario"])
    cita   = obtener_cita_por_id(id_cita)

    if not cita or cita["id_medico"] != perfil["id_medico"]:
        flash("Sin permiso.", "danger")
        return redirect(url_for("medico.dashboard"))

    if cita["estado"] != "Activa":
        flash("Solo puedes completar citas activas.", "warning")
        return redirect(url_for("medico.ver_cita", id_cita=id_cita))

    if request.method == "POST":
        diagnostico   = request.form.get("diagnostico",   "").strip()
        tratamiento   = request.form.get("tratamiento",   "").strip()
        proxima_cita  = request.form.get("proxima_cita",  "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        if not diagnostico:
            flash("El diagnóstico es obligatorio.", "danger")
            return render_template("medico/completar_cita.html",
                                   cita=cita, perfil=perfil)

        # 1. Marcar cita como Completada
        r = cambiar_estado_cita(id_cita, "Completada")
        if not r["ok"]:
            flash(f"Error al completar la cita: {r['error']}", "danger")
            return render_template("medico/completar_cita.html",
                                   cita=cita, perfil=perfil)

        # 2. Guardar nota de consulta
        rn = crear_nota(id_cita, diagnostico, tratamiento,
                        proxima_cita, observaciones)
        if not rn["ok"]:
            flash(f"Cita completada, pero no se pudo guardar la nota: {rn['error']}", "warning")
        else:
            flash("¡Cita completada y nota de consulta registrada!", "success")

        return redirect(url_for("medico.ver_cita", id_cita=id_cita))

    return render_template("medico/completar_cita.html",
                           cita=cita, perfil=perfil)


# ── Horario del día filtrable ──────────────────────────────────

@medico_bp.route("/horario")
@login_required
@rol_requerido("medico")
def horario():
    perfil = obtener_medico_por_usuario(session["id_usuario"])
    from datetime import date
    fecha  = request.args.get("fecha", date.today().isoformat())
    citas  = horario_del_dia(perfil["id_medico"], fecha)
    return render_template("medico/horario.html",
                           perfil=perfil,
                           citas=citas,
                           fecha=fecha)


# ── Historial médico de un paciente ───────────────────────────

@medico_bp.route("/paciente/<int:id_paciente>/historial")
@login_required
@rol_requerido("medico")
def historial_paciente_view(id_paciente):
    """
    Vista consolidada del historial clínico de un paciente.
    Solo accesible por médicos. Muestra todas las consultas
    completadas con sus notas (si existen).
    """
    perfil_medico = obtener_medico_por_usuario(session["id_usuario"])

    # Obtener datos del paciente desde cualquier cita
    from models.paciente_model import obtener_paciente_por_id
    paciente = obtener_paciente_por_id(id_paciente)

    if not paciente:
        flash("Paciente no encontrado.", "danger")
        return redirect(url_for("medico.dashboard"))

    historial = historial_paciente(id_paciente)

    return render_template("medico/historial_paciente.html",
                           perfil=perfil_medico,
                           paciente=paciente,
                           historial=historial)
