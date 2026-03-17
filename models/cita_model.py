"""
models/cita_model.py – CRUD de citas con validación de cruces (v2).

Lógica de conflicto:
    Una nueva cita [hora_inicio_nueva, hora_fin_nueva] choca con una
    cita existente [hora_inicio_ex, hora_fin_ex] del mismo médico en
    la misma fecha si:

        hora_inicio_nueva < hora_fin_ex  AND  hora_fin_nueva > hora_inicio_ex

    Es decir, los intervalos se solapan.
    Las citas Canceladas o Completadas NO bloquean el horario.
"""

from datetime import datetime, timedelta
from database.conexion import get_connection


# ── Helpers ───────────────────────────────────────────────────

def _calcular_hora_fin(hora_inicio: str, duracion_min: int) -> str:
    """Dado '09:00' y 30 minutos, retorna '09:30'."""
    dt = datetime.strptime(hora_inicio, "%H:%M") + timedelta(minutes=duracion_min)
    return dt.strftime("%H:%M")


# ══════════════════════════════════════════════════════════════
#  VALIDACIÓN DE CRUCE DE HORARIO
# ══════════════════════════════════════════════════════════════

def verificar_cruce_medico(id_medico: int, fecha: str,
                            hora_inicio: str, hora_fin: str,
                            excluir_id_cita: int = None) -> list[dict]:
    """
    Retorna las citas activas del médico que se cruzan con el
    intervalo [hora_inicio, hora_fin] en la fecha dada.

    Si excluir_id_cita se indica (edición), esa cita no cuenta.
    """
    excluye = "AND c.id_cita != %s" if excluir_id_cita else ""
    sql = f"""
        SELECT c.id_cita, c.hora_inicio, c.hora_fin,
               p.nombre AS pac_nombre, p.apellido AS pac_apellido
        FROM citas c
        INNER JOIN pacientes p ON c.id_paciente = p.id_paciente
        WHERE c.id_medico = %s
          AND c.fecha     = %s
          AND c.estado    = 'Activa'
          AND %s < c.hora_fin
          AND %s > c.hora_inicio
          {excluye}
    """
    params = [id_medico, fecha, hora_inicio, hora_fin]
    if excluir_id_cita:
        params.append(excluir_id_cita)

    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def verificar_cruce_paciente(id_paciente: int, fecha: str,
                              hora_inicio: str, hora_fin: str,
                              excluir_id_cita: int = None) -> list[dict]:
    """
    Verifica que el paciente no tenga otra cita activa en el mismo
    intervalo de tiempo (en cualquier médico / especialidad).
    """
    excluye = "AND c.id_cita != %s" if excluir_id_cita else ""
    sql = f"""
        SELECT c.id_cita, c.hora_inicio, c.hora_fin,
               m.nombre AS med_nombre, m.apellido AS med_apellido
        FROM citas c
        INNER JOIN medicos m ON c.id_medico = m.id_medico
        WHERE c.id_paciente = %s
          AND c.fecha       = %s
          AND c.estado      = 'Activa'
          AND %s < c.hora_fin
          AND %s > c.hora_inicio
          {excluye}
    """
    params = [id_paciente, fecha, hora_inicio, hora_fin]
    if excluir_id_cita:
        params.append(excluir_id_cita)

    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  CREATE
# ══════════════════════════════════════════════════════════════

def crear_cita(id_paciente: int, id_medico: int, id_especialidad: int,
               id_eps: int, fecha: str, hora_inicio: str,
               duracion_min: int, motivo: str = "") -> dict:
    """
    Crea una cita si no hay conflicto de horario.

    Retorna:
        {'ok': True,  'id': int}
        {'ok': False, 'error': str, 'cruce': list}   ← si hay conflicto
    """
    hora_fin = _calcular_hora_fin(hora_inicio, duracion_min)

    # ── Verificar cruce del médico ──
    cruces_med = verificar_cruce_medico(id_medico, fecha, hora_inicio, hora_fin)
    if cruces_med:
        return {
            "ok": False,
            "error": "El médico ya tiene una cita en ese horario.",
            "cruce": cruces_med,
        }

    # ── Verificar cruce del paciente ──
    cruces_pac = verificar_cruce_paciente(id_paciente, fecha, hora_inicio, hora_fin)
    if cruces_pac:
        return {
            "ok": False,
            "error": "El paciente ya tiene una cita activa en ese horario.",
            "cruce": cruces_pac,
        }

    sql = """
        INSERT INTO citas
            (id_paciente, id_medico, id_especialidad, id_eps,
             fecha, hora_inicio, hora_fin, motivo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(sql, (id_paciente, id_medico, id_especialidad,
                          id_eps, fecha, hora_inicio, hora_fin, motivo))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  READ
# ══════════════════════════════════════════════════════════════

def _sql_cita_completa() -> str:
    return """
        SELECT
            c.id_cita,
            c.fecha,
            c.hora_inicio,
            c.hora_fin,
            c.estado,
            c.motivo,
            p.id_paciente,
            p.documento  AS pac_documento,
            p.nombre     AS pac_nombre,
            p.apellido   AS pac_apellido,
            p.telefono   AS pac_telefono,
            p.correo     AS pac_correo,
            m.id_medico,
            m.nombre     AS med_nombre,
            m.apellido   AS med_apellido,
            e.id_especialidad,
            e.nombre     AS especialidad,
            e.duracion_min,
            eps.id_eps,
            eps.nombre   AS eps_nombre
        FROM citas c
        INNER JOIN pacientes      p   ON c.id_paciente     = p.id_paciente
        INNER JOIN medicos        m   ON c.id_medico       = m.id_medico
        INNER JOIN especialidades e   ON c.id_especialidad = e.id_especialidad
        INNER JOIN eps                ON c.id_eps          = eps.id_eps
    """


def obtener_cita_por_id(id_cita: int) -> dict | None:
    sql = _sql_cita_completa() + " WHERE c.id_cita = %s LIMIT 1"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_cita,))
        return cur.fetchone()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def citas_por_paciente(id_paciente: int) -> list[dict]:
    sql = _sql_cita_completa() + """
        WHERE c.id_paciente = %s
        ORDER BY c.fecha DESC, c.hora_inicio ASC
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_paciente,))
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def citas_por_medico(id_medico: int) -> list[dict]:
    sql = _sql_cita_completa() + """
        WHERE c.id_medico = %s
        ORDER BY c.fecha ASC, c.hora_inicio ASC
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_medico,))
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def todas_las_citas() -> list[dict]:
    sql = _sql_cita_completa() + " ORDER BY c.fecha DESC, c.hora_inicio ASC"
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql)
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def horario_del_dia(id_medico: int, fecha: str) -> list[dict]:
    """Retorna todas las citas activas de un médico en una fecha."""
    sql = _sql_cita_completa() + """
        WHERE c.id_medico = %s AND c.fecha = %s AND c.estado = 'Activa'
        ORDER BY c.hora_inicio
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_medico, fecha))
        return cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════
#  UPDATE
# ══════════════════════════════════════════════════════════════

def actualizar_cita(id_cita: int, id_medico: int, id_especialidad: int,
                    id_eps: int, fecha: str, hora_inicio: str,
                    duracion_min: int, motivo: str,
                    id_paciente: int) -> dict:
    """
    Actualiza una cita verificando que el nuevo horario no genere cruce.
    Excluye la propia cita de la verificación de cruce.
    """
    hora_fin = _calcular_hora_fin(hora_inicio, duracion_min)

    cruces_med = verificar_cruce_medico(id_medico, fecha, hora_inicio,
                                        hora_fin, excluir_id_cita=id_cita)
    if cruces_med:
        return {"ok": False, "error": "El médico ya tiene una cita en ese nuevo horario.", "cruce": cruces_med}

    cruces_pac = verificar_cruce_paciente(id_paciente, fecha, hora_inicio,
                                          hora_fin, excluir_id_cita=id_cita)
    if cruces_pac:
        return {"ok": False, "error": "El paciente ya tiene una cita en ese nuevo horario.", "cruce": cruces_pac}

    sql = """
        UPDATE citas
        SET id_medico=%s, id_especialidad=%s, id_eps=%s,
            fecha=%s, hora_inicio=%s, hora_fin=%s, motivo=%s
        WHERE id_cita=%s
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(sql, (id_medico, id_especialidad, id_eps,
                          fecha, hora_inicio, hora_fin, motivo, id_cita))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()


def cambiar_estado_cita(id_cita: int, estado: str) -> dict:
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("UPDATE citas SET estado=%s WHERE id_cita=%s", (estado, id_cita))
        conn.commit()
        return {"ok": True}
    except Exception as e:
        if conn: conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()
