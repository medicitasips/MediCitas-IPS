"""
models/catalogo_model.py – Operaciones CRUD para los catálogos:
    • eps
    • especialidades
    • medicos
"""

from database.conexion import get_connection


# ══════════════════════════════════════════════════════════════
#  EPS
# ══════════════════════════════════════════════════════════════

def listar_eps(solo_activas: bool = True) -> list[dict]:
    filtro = "WHERE activa = 1" if solo_activas else ""
    sql = f"SELECT id_eps, nombre, activa FROM eps {filtro} ORDER BY nombre"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def obtener_eps_por_id(id_eps: int) -> dict | None:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id_eps, nombre, activa FROM eps WHERE id_eps = %s LIMIT 1", (id_eps,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def crear_eps(nombre: str) -> dict:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("INSERT INTO eps (nombre) VALUES (%s)", (nombre,))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def actualizar_eps(id_eps: int, nombre: str, activa: int) -> dict:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("UPDATE eps SET nombre = %s, activa = %s WHERE id_eps = %s",
                    (nombre, activa, id_eps))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  ESPECIALIDADES
# ══════════════════════════════════════════════════════════════

def listar_especialidades(solo_activas: bool = True) -> list[dict]:
    filtro = "WHERE activa = 1" if solo_activas else ""
    sql = f"SELECT id_especialidad, nombre, duracion_min, activa FROM especialidades {filtro} ORDER BY nombre"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def obtener_especialidad_por_id(id_esp: int) -> dict | None:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT id_especialidad, nombre, duracion_min, activa FROM especialidades WHERE id_especialidad = %s LIMIT 1", (id_esp,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def crear_especialidad(nombre: str, duracion_min: int) -> dict:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("INSERT INTO especialidades (nombre, duracion_min) VALUES (%s, %s)", (nombre, duracion_min))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def actualizar_especialidad(id_esp: int, nombre: str, duracion_min: int, activa: int) -> dict:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("UPDATE especialidades SET nombre=%s, duracion_min=%s, activa=%s WHERE id_especialidad=%s",
                    (nombre, duracion_min, activa, id_esp))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  MÉDICOS
# ══════════════════════════════════════════════════════════════

def listar_medicos(solo_activos: bool = True) -> list[dict]:
    filtro = "WHERE m.activo = 1" if solo_activos else ""
    sql = f"""
        SELECT m.id_medico, m.documento, m.nombre, m.apellido,
               m.telefono, m.correo, m.activo,
               e.id_especialidad, e.nombre AS especialidad,
               u.username
        FROM medicos m
        INNER JOIN especialidades e ON m.id_especialidad = e.id_especialidad
        INNER JOIN usuarios       u ON m.id_usuario      = u.id_usuario
        {filtro}
        ORDER BY m.apellido, m.nombre
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def obtener_medico_por_id(id_medico: int) -> dict | None:
    sql = """
        SELECT m.id_medico, m.id_usuario, m.documento, m.nombre, m.apellido,
               m.telefono, m.correo, m.activo,
               m.id_especialidad, e.nombre AS especialidad, e.duracion_min
        FROM medicos m
        INNER JOIN especialidades e ON m.id_especialidad = e.id_especialidad
        WHERE m.id_medico = %s LIMIT 1
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_medico,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def obtener_medico_por_usuario(id_usuario: int) -> dict | None:
    sql = """
        SELECT m.id_medico, m.documento, m.nombre, m.apellido,
               m.telefono, m.correo, m.activo,
               m.id_especialidad, e.nombre AS especialidad, e.duracion_min
        FROM medicos m
        INNER JOIN especialidades e ON m.id_especialidad = e.id_especialidad
        WHERE m.id_usuario = %s LIMIT 1
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_usuario,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def crear_medico(id_usuario: int, documento: str, nombre: str, apellido: str,
                 telefono: str, correo: str, id_especialidad: int) -> dict:
    sql = """
        INSERT INTO medicos (id_usuario, documento, nombre, apellido,
                             telefono, correo, id_especialidad)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(sql, (id_usuario, documento, nombre, apellido,
                          telefono, correo, id_especialidad))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def actualizar_medico(id_medico: int, nombre: str, apellido: str,
                      telefono: str, correo: str, id_especialidad: int) -> dict:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE medicos SET nombre=%s, apellido=%s, telefono=%s,
                               correo=%s, id_especialidad=%s
            WHERE id_medico=%s
        """, (nombre, apellido, telefono, correo, id_especialidad, id_medico))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

def listar_medicos_por_especialidad(id_especialidad: int) -> list[dict]:
    sql = """
        SELECT id_medico,
               CONCAT(nombre, ' ', apellido) AS nombre_completo
        FROM medicos
        WHERE id_especialidad = %s AND activo = 1
        ORDER BY apellido
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_especialidad,))
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()
