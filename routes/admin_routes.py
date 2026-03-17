"""
routes/admin_routes.py – Panel de administración.

Blueprint: 'admin'  |  prefijo URL: /admin
Acceso: solo rol 'admin'
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from routes.decoradores     import login_required, rol_requerido
from models.usuario_model   import (crear_usuario, listar_usuarios,
                                     username_existe, toggle_activo)
from models.catalogo_model  import (listar_eps, crear_eps, actualizar_eps,
                                     listar_especialidades, crear_especialidad,
                                     actualizar_especialidad,
                                     listar_medicos, crear_medico,
                                     obtener_medico_por_id, actualizar_medico,
                                     obtener_especialidad_por_id)
from models.paciente_model  import listar_pacientes
from models.cita_model      import todas_las_citas, cambiar_estado_cita

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ── Dashboard ─────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
@rol_requerido("admin")
def dashboard():
    stats = {
        "medicos":    len(listar_medicos()),
        "pacientes":  len(listar_pacientes()),
        "citas":      len(todas_las_citas()),
        "eps":        len(listar_eps(solo_activas=False)),
    }
    citas_recientes = todas_las_citas()[:10]
    return render_template("admin/dashboard.html",
                           stats=stats,
                           citas_recientes=citas_recientes)


# ════════════════  EPS  ════════════════

@admin_bp.route("/eps")
@login_required
@rol_requerido("admin")
def eps_lista():
    eps = listar_eps(solo_activas=False)
    return render_template("admin/eps_lista.html", eps=eps)


@admin_bp.route("/eps/nueva", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def eps_nueva():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        if not nombre:
            flash("El nombre es obligatorio.", "danger")
        else:
            r = crear_eps(nombre)
            if r["ok"]:
                flash(f"EPS '{nombre}' creada.", "success")
                return redirect(url_for("admin.eps_lista"))
            else:
                flash(f"Error: {r['error']}", "danger")
    return render_template("admin/eps_form.html", eps=None)


@admin_bp.route("/eps/editar/<int:id_eps>", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def eps_editar(id_eps):
    from models.catalogo_model import obtener_eps_por_id
    eps = obtener_eps_por_id(id_eps)
    if not eps:
        flash("EPS no encontrada.", "danger")
        return redirect(url_for("admin.eps_lista"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        activa = int(request.form.get("activa", 1))
        r = actualizar_eps(id_eps, nombre, activa)
        if r["ok"]:
            flash("EPS actualizada.", "success")
            return redirect(url_for("admin.eps_lista"))
        else:
            flash(f"Error: {r['error']}", "danger")

    return render_template("admin/eps_form.html", eps=eps)


# ════════════════  ESPECIALIDADES  ════════════════

@admin_bp.route("/especialidades")
@login_required
@rol_requerido("admin")
def especialidades_lista():
    esp = listar_especialidades(solo_activas=False)
    return render_template("admin/especialidades_lista.html", especialidades=esp)


@admin_bp.route("/especialidades/nueva", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def especialidad_nueva():
    if request.method == "POST":
        nombre      = request.form.get("nombre",      "").strip()
        duracion    = int(request.form.get("duracion_min", 30))
        if not nombre:
            flash("El nombre es obligatorio.", "danger")
        else:
            r = crear_especialidad(nombre, duracion)
            if r["ok"]:
                flash(f"Especialidad '{nombre}' creada.", "success")
                return redirect(url_for("admin.especialidades_lista"))
            else:
                flash(f"Error: {r['error']}", "danger")
    return render_template("admin/especialidad_form.html", especialidad=None)


@admin_bp.route("/especialidades/editar/<int:id_esp>", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def especialidad_editar(id_esp):
    esp = obtener_especialidad_por_id(id_esp)
    if not esp:
        flash("Especialidad no encontrada.", "danger")
        return redirect(url_for("admin.especialidades_lista"))

    if request.method == "POST":
        nombre   = request.form.get("nombre",      "").strip()
        duracion = int(request.form.get("duracion_min", 30))
        activa   = int(request.form.get("activa", 1))
        r = actualizar_especialidad(id_esp, nombre, duracion, activa)
        if r["ok"]:
            flash("Especialidad actualizada.", "success")
            return redirect(url_for("admin.especialidades_lista"))
        else:
            flash(f"Error: {r['error']}", "danger")

    return render_template("admin/especialidad_form.html", especialidad=esp)


# ════════════════  MÉDICOS  ════════════════

@admin_bp.route("/medicos")
@login_required
@rol_requerido("admin")
def medicos_lista():
    medicos = listar_medicos(solo_activos=False)
    return render_template("admin/medicos_lista.html", medicos=medicos)


@admin_bp.route("/medicos/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def medico_nuevo():
    especialidades = listar_especialidades()

    if request.method == "POST":
        username        = request.form.get("username",       "").strip()
        password        = request.form.get("password",       "").strip()
        documento       = request.form.get("documento",      "").strip()
        nombre          = request.form.get("nombre",         "").strip()
        apellido        = request.form.get("apellido",       "").strip()
        telefono        = request.form.get("telefono",       "").strip()
        correo          = request.form.get("correo",         "").strip()
        id_especialidad = int(request.form.get("id_especialidad", 0))

        errores = []
        if username_existe(username):
            errores.append(f"El usuario '{username}' ya existe.")
        if len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if not documento or not id_especialidad:
            errores.append("Documento y especialidad son obligatorios.")

        if errores:
            for e in errores: flash(e, "danger")
            return render_template("admin/medico_form.html",
                                   medico=None,
                                   especialidades=especialidades,
                                   form_data=request.form)

        r_usr = crear_usuario(username, password, "medico")
        if not r_usr["ok"]:
            flash(f"Error al crear usuario: {r_usr['error']}", "danger")
            return render_template("admin/medico_form.html",
                                   medico=None,
                                   especialidades=especialidades,
                                   form_data=request.form)

        r_med = crear_medico(r_usr["id"], documento, nombre, apellido,
                             telefono, correo, id_especialidad)
        if r_med["ok"]:
            flash(f"Médico {nombre} {apellido} registrado.", "success")
            return redirect(url_for("admin.medicos_lista"))
        else:
            flash(f"Error perfil médico: {r_med['error']}", "danger")

    return render_template("admin/medico_form.html",
                           medico=None,
                           especialidades=especialidades,
                           form_data={})


@admin_bp.route("/medicos/editar/<int:id_medico>", methods=["GET", "POST"])
@login_required
@rol_requerido("admin")
def medico_editar(id_medico):
    medico         = obtener_medico_por_id(id_medico)
    especialidades = listar_especialidades()

    if not medico:
        flash("Médico no encontrado.", "danger")
        return redirect(url_for("admin.medicos_lista"))

    if request.method == "POST":
        nombre          = request.form.get("nombre",          "").strip()
        apellido        = request.form.get("apellido",        "").strip()
        telefono        = request.form.get("telefono",        "").strip()
        correo          = request.form.get("correo",          "").strip()
        id_especialidad = int(request.form.get("id_especialidad", medico["id_especialidad"]))

        r = actualizar_medico(id_medico, nombre, apellido, telefono,
                              correo, id_especialidad)
        if r["ok"]:
            flash("Médico actualizado.", "success")
            return redirect(url_for("admin.medicos_lista"))
        else:
            flash(f"Error: {r['error']}", "danger")

    return render_template("admin/medico_form.html",
                           medico=medico,
                           especialidades=especialidades,
                           form_data=medico)


# ════════════════  PACIENTES  ════════════════

@admin_bp.route("/pacientes")
@login_required
@rol_requerido("admin")
def pacientes_lista():
    pacientes = listar_pacientes()
    return render_template("admin/pacientes_lista.html", pacientes=pacientes)


# ════════════════  CITAS  ════════════════

@admin_bp.route("/citas")
@login_required
@rol_requerido("admin")
def citas_lista():
    citas = todas_las_citas()
    return render_template("admin/citas_lista.html", citas=citas)


@admin_bp.route("/citas/estado/<int:id_cita>/<estado>", methods=["POST"])
@login_required
@rol_requerido("admin")
def cita_cambiar_estado(id_cita, estado):
    if estado not in ("Activa", "Cancelada", "Completada"):
        flash("Estado no válido.", "danger")
        return redirect(url_for("admin.citas_lista"))
    r = cambiar_estado_cita(id_cita, estado)
    flash("Estado actualizado." if r["ok"] else f"Error: {r['error']}",
          "success" if r["ok"] else "danger")
    return redirect(url_for("admin.citas_lista"))


# ════════════════  USUARIOS  ════════════════

@admin_bp.route("/usuarios")
@login_required
@rol_requerido("admin")
def usuarios_lista():
    usuarios = listar_usuarios()
    return render_template("admin/usuarios_lista.html", usuarios=usuarios)


@admin_bp.route("/usuarios/toggle/<int:id_usuario>", methods=["POST"])
@login_required
@rol_requerido("admin")
def usuario_toggle(id_usuario):
    if id_usuario == session["id_usuario"]:
        flash("No puedes desactivarte a ti mismo.", "warning")
    else:
        toggle_activo(id_usuario)
        flash("Estado del usuario actualizado.", "success")
    return redirect(url_for("admin.usuarios_lista"))
