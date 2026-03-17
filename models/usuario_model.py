"""
models/usuario_model.py – CRUD de usuarios y autenticación.

Roles disponibles: 'admin' | 'medico' | 'paciente'
Las contraseñas se almacenan con hash Werkzeug (pbkdf2:sha256).
"""

from werkzeug.security import generate_password_hash, check_password_hash
from database.conexion import get_connection


# ── CREATE ────────────────────────────────────────────────────

def crear_usuario(username: str, password: str, rol: str) -> dict:
    """Crea un usuario nuevo. Retorna {'ok': True, 'id': int} o {'ok': False, 'error': str}."""
    sql = """
        INSERT INTO usuarios (username, password_hash, rol)
        VALUES (%s, %s, %s)
    """
    conn = None
    try:
        conn   = get_connection()
        cur    = conn.cursor()
        cur.execute(sql, (username, generate_password_hash(password), rol))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


# ── READ ──────────────────────────────────────────────────────

def obtener_usuario_por_username(username: str) -> dict | None:
    sql = "SELECT id_usuario, username, password_hash, rol, activo FROM usuarios WHERE username = %s LIMIT 1"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (username,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def obtener_usuario_por_id(id_usuario: int) -> dict | None:
    sql = "SELECT id_usuario, username, rol, activo FROM usuarios WHERE id_usuario = %s LIMIT 1"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_usuario,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def listar_usuarios() -> list[dict]:
    sql = "SELECT id_usuario, username, rol, activo, fecha_registro FROM usuarios ORDER BY rol, username"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


# ── AUTH ──────────────────────────────────────────────────────

def verificar_credenciales(username: str, password: str) -> dict | None:
    """
    Verifica usuario y contraseña.
    Retorna el dict del usuario si es válido y activo, o None.
    """
    usuario = obtener_usuario_por_username(username)
    if not usuario:
        return None
    if not usuario["activo"]:
        return None
    if not check_password_hash(usuario["password_hash"], password):
        return None
    return usuario


# ── UPDATE ────────────────────────────────────────────────────

def cambiar_password(id_usuario: int, nueva_password: str) -> dict:
    sql = "UPDATE usuarios SET password_hash = %s WHERE id_usuario = %s"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(sql, (generate_password_hash(nueva_password), id_usuario))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def toggle_activo(id_usuario: int) -> dict:
    sql = "UPDATE usuarios SET activo = NOT activo WHERE id_usuario = %s"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(sql, (id_usuario,))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def username_existe(username: str) -> bool:
    return obtener_usuario_por_username(username) is not None
