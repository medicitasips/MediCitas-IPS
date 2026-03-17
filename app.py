"""
app.py – Punto de entrada y Application Factory (v2 – roles).

Uso:
    python app.py          # arranca en modo desarrollo

Al iniciar, seed_db() crea el usuario admin por defecto si no existe:
    username : admin
    password : Admin2025*
    rol      : admin
"""

import os
from flask import Flask, render_template, session, redirect, url_for

from config import config_map

from routes.auth_routes    import auth_bp
from routes.admin_routes   import admin_bp
from routes.paciente_routes import paciente_bp
from routes.medico_routes  import medico_bp


def create_app(env: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_map[env])

    # ── Blueprints ────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(paciente_bp)
    app.register_blueprint(medico_bp)

    # ── Ruta raíz → redirige según sesión ────────────────────
    @app.route("/")
    def index():
        rol = session.get("rol")
        if rol == "admin":
            return redirect(url_for("admin.dashboard"))
        if rol == "medico":
            return redirect(url_for("medico.dashboard"))
        if rol == "paciente":
            return redirect(url_for("paciente.dashboard"))
        # Sin sesión → página pública de bienvenida
        return render_template("index.html")

    # ── Errores globales ──────────────────────────────────────
    @app.errorhandler(403)
    def prohibido(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def no_encontrado(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def error_interno(e):
        return render_template("errors/500.html"), 500

    # ── Contexto global para plantillas ──────────────────────
    @app.context_processor
    def inject_session():
        return {"current_user": {
            "id":       session.get("id_usuario"),
            "username": session.get("username"),
            "rol":      session.get("rol"),
        }}

    # ── Seed DB ───────────────────────────────────────────────
    with app.app_context():
        _seed_db()

    return app


def _seed_db():
    """Crea el usuario admin por defecto si no existe."""
    try:
        from models.usuario_model import username_existe, crear_usuario
        if not username_existe("admin"):
            r = crear_usuario("admin", "Admin2025*", "admin")
            if r["ok"]:
                print("✅  Usuario admin creado  (admin / Admin2025*)")
    except Exception as e:
        print(f"⚠️  seed_db: {e}")


if __name__ == "__main__":
    entorno = os.getenv("FLASK_ENV", "development")
    app = create_app(entorno)
    app.run(
        host  = "0.0.0.0",
        port  = int(os.getenv("PORT", 5550)),
        debug = app.config["DEBUG"],
    )
