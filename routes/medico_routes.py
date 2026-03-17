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
                                    cambiar_estado_cita, horario_del_dia)

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
    hoy   = date.today().isoformat()
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

    return render_template("medico/ver_cita.html", cita=cita, perfil=perfil)


# ── Marcar cita como Completada ────────────────────────────────

@medico_bp.route("/cita/completar/<int:id_cita>", methods=["POST"])
@login_required
@rol_requerido("medico")
def completar_cita(id_cita):
    perfil = obtener_medico_por_usuario(session["id_usuario"])
    cita   = obtener_cita_por_id(id_cita)

    if not cita or cita["id_medico"] != perfil["id_medico"]:
        flash("Sin permiso.", "danger")
        return redirect(url_for("medico.dashboard"))

    r = cambiar_estado_cita(id_cita, "Completada")
    flash("Cita marcada como completada." if r["ok"] else f"Error: {r['error']}",
          "success" if r["ok"] else "danger")
    return redirect(url_for("medico.dashboard"))


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
