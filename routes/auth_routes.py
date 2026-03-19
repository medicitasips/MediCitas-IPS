"""
routes/auth_routes.py – Login, logout y registro de cuenta.

Blueprint: 'auth'  |  prefijo URL: /auth
La sesión almacena:
    session['id_usuario']
    session['username']
    session['rol']          ← 'admin' | 'medico' | 'paciente'
"""

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session)
from models.usuario_model  import verificar_credenciales, crear_usuario, username_existe
from models.paciente_model import crear_paciente, documento_existe
from models.catalogo_model import listar_eps

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ── Login ─────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "id_usuario" in session:
        return redirect(_redirect_por_rol(session["rol"]))

    # Mensaje cuando la sesión se cierra por inactividad o cierre de pestaña
    if request.args.get("timeout"):
        flash("Tu sesión se cerró automáticamente por inactividad o cierre del navegador.", "warning")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        usuario = verificar_credenciales(username, password)
        if not usuario:
            flash("Usuario o contraseña incorrectos.", "danger")
            return render_template("auth/login.html")

        session.permanent = True
        session["id_usuario"] = usuario["id_usuario"]
        session["username"]   = usuario["username"]
        session["rol"]        = usuario["rol"]

        flash(f"Bienvenido, {usuario['username']}.", "success")
        return redirect(_redirect_por_rol(usuario["rol"]))

    return render_template("auth/login.html")


# ── Logout ────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout/silencioso", methods=["POST"])
def logout_silencioso():
    """
    Endpoint para cierre de sesión automático desde JavaScript.
    Usado por:
      - sendBeacon() al cerrar la pestaña/navegador
      - fetch() al detectar inactividad prolongada
    Retorna 204 (No Content) para mínimo overhead.
    """
    session.clear()
    from flask import Response
    return Response(status=204)


# ── Registro de paciente ──────────────────────────────────────

@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Registro público: crea usuario con rol 'paciente' + perfil."""
    eps_lista = listar_eps()

    if request.method == "POST":
        username  = request.form.get("username",  "").strip()
        password  = request.form.get("password",  "").strip()
        password2 = request.form.get("password2", "").strip()
        documento = request.form.get("documento", "").strip()
        nombre    = request.form.get("nombre",    "").strip()
        apellido  = request.form.get("apellido",  "").strip()
        telefono  = request.form.get("telefono",  "").strip()
        correo    = request.form.get("correo",    "").strip()
        id_eps    = request.form.get("id_eps",    "").strip()

        # Validaciones
        errores = []
        if not username or len(username) < 4:
            errores.append("El nombre de usuario debe tener al menos 4 caracteres.")
        if username_existe(username):
            errores.append(f"El usuario '{username}' ya está en uso.")
        if not password or len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if password != password2:
            errores.append("Las contraseñas no coinciden.")
        if not documento or not documento.isdigit():
            errores.append("El documento debe contener solo números.")
        if documento_existe(documento):
            errores.append("Ya existe un paciente con ese documento.")
        if not nombre or not apellido:
            errores.append("Nombre y apellido son obligatorios.")
        if not id_eps:
            errores.append("Seleccione una EPS.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("auth/registro.html",
                                   eps_lista=eps_lista,
                                   form_data=request.form)

        # Crear usuario
        res_usr = crear_usuario(username, password, "paciente")
        if not res_usr["ok"]:
            flash(f"Error al crear usuario: {res_usr['error']}", "danger")
            return render_template("auth/registro.html",
                                   eps_lista=eps_lista,
                                   form_data=request.form)

        # Crear perfil de paciente
        res_pac = crear_paciente(res_usr["id"], documento, nombre,
                                 apellido, telefono, correo, int(id_eps))
        if not res_pac["ok"]:
            flash(f"Usuario creado pero error en perfil: {res_pac['error']}", "warning")
        else:
            flash("Cuenta creada exitosamente. Inicia sesión.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/registro.html",
                           eps_lista=eps_lista,
                           form_data={})


# ── Helper privado ────────────────────────────────────────────

def _redirect_por_rol(rol: str) -> str:
    rutas = {
        "admin":    url_for("admin.dashboard"),
        "medico":   url_for("medico.dashboard"),
        "paciente": url_for("paciente.dashboard"),
    }
    return rutas.get(rol, url_for("auth.login"))
