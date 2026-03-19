"""
models/nota_model.py – CRUD de notas de consulta.

Cada cita completada puede tener exactamente una nota (relación 1-a-1).
La nota se crea al mismo tiempo que se marca la cita como Completada.
"""

from database.conexion import get_connection


def crear_nota(id_cita: int, diagnostico: str, tratamiento: str = "",
               proxima_cita: str = "", observaciones: str = "") -> dict:
    """
    Inserta una nota de consulta para una cita.
    Si ya existe una nota para esa cita, la actualiza (upsert).

    Retorna: {'ok': True} | {'ok': False, 'error': str}
    """
    sql = """
        INSERT INTO notas_consulta
            (id_cita, diagnostico, tratamiento, proxima_cita, observaciones)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            diagnostico  = VALUES(diagnostico),
            tratamiento  = VALUES(tratamiento),
            proxima_cita = VALUES(proxima_cita),
            observaciones = VALUES(observaciones),
            fecha_registro = CURRENT_TIMESTAMP
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(sql, (id_cita,
                          diagnostico.strip(),
                          tratamiento.strip(),
                          proxima_cita.strip(),
                          observaciones.strip()))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def obtener_nota_por_cita(id_cita: int) -> dict | None:
    """
    Retorna la nota de consulta de una cita, o None si no existe.
    """
    sql = """
        SELECT id_nota, id_cita, diagnostico, tratamiento,
               proxima_cita, observaciones, fecha_registro
        FROM notas_consulta
        WHERE id_cita = %s
        LIMIT 1
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_cita,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def notas_por_paciente(id_paciente: int) -> list[dict]:
    """
    Retorna todas las notas de consulta de un paciente,
    unidas con los datos de la cita y el médico.
    Útil para el historial clínico.
    """
    sql = """
        SELECT
            n.id_nota,
            n.diagnostico,
            n.tratamiento,
            n.proxima_cita,
            n.observaciones,
            n.fecha_registro,
            c.id_cita,
            c.fecha         AS cita_fecha,
            c.hora_inicio,
            c.hora_fin,
            e.nombre        AS especialidad,
            m.nombre        AS med_nombre,
            m.apellido      AS med_apellido
        FROM notas_consulta n
        INNER JOIN citas          c ON n.id_cita         = c.id_cita
        INNER JOIN medicos        m ON c.id_medico        = m.id_medico
        INNER JOIN especialidades e ON c.id_especialidad  = e.id_especialidad
        WHERE c.id_paciente = %s
        ORDER BY c.fecha DESC, c.hora_inicio DESC
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_paciente,))
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()
