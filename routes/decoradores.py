"""
routes/decoradores.py – Decoradores de autenticación y autorización.

Uso:
    @login_required
    @rol_requerido("admin")
    def mi_vista(): ...
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(f):
    """Redirige al login si no hay sesión activa."""
    @wraps(f)
    def decorado(*args, **kwargs):
        if "id_usuario" not in session:
            flash("Debes iniciar sesión para acceder.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorado


def rol_requerido(*roles):
    """
    Verifica que el usuario tenga uno de los roles indicados.
    Debe usarse DESPUÉS de @login_required.

    Ejemplo:
        @rol_requerido("admin", "medico")
    """
    def decorador(f):
        @wraps(f)
        def decorado(*args, **kwargs):
            if session.get("rol") not in roles:
                flash("No tienes permiso para acceder a esta sección.", "danger")
                abort(403)
            return f(*args, **kwargs)
        return decorado
    return decorador
