"""models/paciente_model.py – CRUD de pacientes (v2)."""
from database.conexion import get_connection


def crear_paciente(id_usuario: int, documento: str, nombre: str,
                   apellido: str, telefono: str, correo: str, id_eps: int) -> dict:
    sql = """
        INSERT INTO pacientes (id_usuario, documento, nombre, apellido, telefono, correo, id_eps)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(sql, (id_usuario, documento, nombre, apellido, telefono, correo, id_eps))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def obtener_paciente_por_usuario(id_usuario: int) -> dict | None:
    sql = """
        SELECT p.id_paciente, p.documento, p.nombre, p.apellido,
               p.telefono, p.correo, p.id_eps, e.nombre AS eps_nombre
        FROM pacientes p
        INNER JOIN eps e ON p.id_eps = e.id_eps
        WHERE p.id_usuario = %s LIMIT 1
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_usuario,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def obtener_paciente_por_documento(documento: str) -> dict | None:
    sql = """
        SELECT p.id_paciente, p.documento, p.nombre, p.apellido,
               p.telefono, p.correo, p.id_eps, e.nombre AS eps_nombre
        FROM pacientes p
        INNER JOIN eps e ON p.id_eps = e.id_eps
        WHERE p.documento = %s LIMIT 1
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (documento,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def listar_pacientes() -> list[dict]:
    sql = """
        SELECT p.id_paciente, p.documento, p.nombre, p.apellido,
               p.telefono, p.correo, e.nombre AS eps_nombre
        FROM pacientes p
        INNER JOIN eps e ON p.id_eps = e.id_eps
        ORDER BY p.apellido, p.nombre
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def actualizar_paciente(id_paciente: int, telefono: str,
                        correo: str, id_eps: int) -> dict:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("UPDATE pacientes SET telefono=%s, correo=%s, id_eps=%s WHERE id_paciente=%s",
                    (telefono, correo, id_eps, id_paciente))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def documento_existe(documento: str) -> bool:
    return obtener_paciente_por_documento(documento) is not None
