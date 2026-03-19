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


def historial_paciente(id_paciente: int) -> list[dict]:
    """
    Retorna todas las citas COMPLETADAS de un paciente,
    incluyendo la nota de consulta si existe (LEFT JOIN).
    Ordenadas de más reciente a más antigua.
    Usado para el historial médico visible por el médico.
    """
    sql = """
        SELECT
            c.id_cita,
            c.fecha,
            c.hora_inicio,
            c.hora_fin,
            c.motivo,
            p.id_paciente,
            p.documento     AS pac_documento,
            p.nombre        AS pac_nombre,
            p.apellido      AS pac_apellido,
            p.telefono      AS pac_telefono,
            p.correo        AS pac_correo,
            m.id_medico,
            m.nombre        AS med_nombre,
            m.apellido      AS med_apellido,
            e.nombre        AS especialidad,
            eps.nombre      AS eps_nombre,
            n.id_nota,
            n.diagnostico,
            n.tratamiento,
            n.proxima_cita,
            n.observaciones,
            n.fecha_registro AS nota_fecha
        FROM citas c
        INNER JOIN pacientes      p   ON c.id_paciente     = p.id_paciente
        INNER JOIN medicos        m   ON c.id_medico       = m.id_medico
        INNER JOIN especialidades e   ON c.id_especialidad = e.id_especialidad
        INNER JOIN eps                ON c.id_eps          = eps.id_eps
        LEFT  JOIN notas_consulta n   ON n.id_cita         = c.id_cita
        WHERE c.id_paciente = %s
          AND c.estado      = 'Completada'
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


# ══════════════════════════════════════════════════════════════
#  DISPONIBILIDAD – calendario visual
# ══════════════════════════════════════════════════════════════

def disponibilidad_mes(id_medico: int, anio: int, mes: int,
                       duracion_min: int) -> dict:
    """
    Calcula la disponibilidad de un médico para todo un mes.

    Retorna un dict {fecha_iso: estado} donde estado puede ser:
        'disponible'  → tiene al menos un slot libre
        'lleno'       → todos los slots del día están ocupados
        'pasado'      → fecha anterior a hoy (no reservable)

    Horario laboral: 08:00 a 17:00.
    Los slots se generan según duracion_min.
    Solo se consideran días de lunes a sábado.
    """
    import calendar
    from datetime import date, timedelta

    hoy  = date.today()
    _, num_dias = calendar.monthrange(anio, mes)

    # Obtener todas las citas activas del médico en ese mes
    sql = """
        SELECT DATE_FORMAT(fecha, '%%Y-%%m-%%d') AS fecha,
               hora_inicio, hora_fin
        FROM citas
        WHERE id_medico = %s
          AND YEAR(fecha)  = %s
          AND MONTH(fecha) = %s
          AND estado = 'Activa'
        ORDER BY fecha, hora_inicio
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_medico, anio, mes))
        citas_mes = cur.fetchall()
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

    # Agrupar citas por fecha
    citas_por_fecha: dict[str, list] = {}
    for c in citas_mes:
        fd = c["fecha"]
        if fd not in citas_por_fecha:
            citas_por_fecha[fd] = []
        citas_por_fecha[fd].append({
            "inicio": _str_to_min(str(c["hora_inicio"])),
            "fin":    _str_to_min(str(c["hora_fin"])),
        })

    resultado = {}
    for dia in range(1, num_dias + 1):
        fecha = date(anio, mes, dia)
        fecha_iso = fecha.isoformat()

        # Domingos bloqueados
        if fecha.weekday() == 6:
            resultado[fecha_iso] = "bloqueado"
            continue

        # Días pasados
        if fecha < hoy:
            resultado[fecha_iso] = "pasado"
            continue

        # Generar slots del día
        slots = _generar_slots(duracion_min)
        citas_dia = citas_por_fecha.get(fecha_iso, [])

        # Verificar si queda al menos un slot libre
        hay_libre = False
        for slot_inicio in slots:
            slot_fin = slot_inicio + duracion_min
            solapado = any(
                slot_inicio < c["fin"] and slot_fin > c["inicio"]
                for c in citas_dia
            )
            if not solapado:
                hay_libre = True
                break

        resultado[fecha_iso] = "disponible" if hay_libre else "lleno"

    return resultado


def slots_disponibles_dia(id_medico: int, fecha: str,
                          duracion_min: int) -> list[str]:
    """
    Retorna lista de horas de inicio disponibles para un médico
    en una fecha específica, con la duración de la especialidad.

    Formato de retorno: ['08:00', '08:30', '09:00', ...]
    """
    from datetime import date as date_cls

    # No retornar slots de días pasados
    hoy = date_cls.today().isoformat()
    if fecha < hoy:
        return []

    # Citas activas del médico ese día
    sql = """
        SELECT hora_inicio, hora_fin
        FROM citas
        WHERE id_medico = %s AND fecha = %s AND estado = 'Activa'
    """
    conn = None
    try:
        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        cur.execute(sql, (id_medico, fecha))
        citas = [
            {
                "inicio": _str_to_min(str(c["hora_inicio"])),
                "fin":    _str_to_min(str(c["hora_fin"])),
            }
            for c in cur.fetchall()
        ]
    finally:
        if conn and conn.is_connected(): cur.close(); conn.close()

    slots = _generar_slots(duracion_min)
    disponibles = []

    for slot_inicio in slots:
        slot_fin = slot_inicio + duracion_min
        # No poner citas que se pasen de las 17:00
        if slot_fin > 17 * 60:
            continue
        solapado = any(
            slot_inicio < c["fin"] and slot_fin > c["inicio"]
            for c in citas
        )
        if not solapado:
            h = slot_inicio // 60
            m = slot_inicio % 60
            disponibles.append(f"{h:02d}:{m:02d}")

    return disponibles


# ── Helpers privados ──────────────────────────────────────────

def _str_to_min(valor: str) -> int:
    """Convierte 'HH:MM:SS' o timedelta string a minutos totales."""
    import datetime
    # MySQL puede retornar timedelta para columnas TIME
    if "day" in str(valor):
        # formato: '0:08:00' o '1 day, 2:30:00'
        partes = str(valor).replace("day, ", "days,").split("days,")
        tiempo = partes[-1].strip()
    else:
        tiempo = str(valor)
    partes_t = tiempo.split(":")
    h = int(partes_t[0])
    m = int(partes_t[1]) if len(partes_t) > 1 else 0
    return h * 60 + m


def _generar_slots(duracion_min: int) -> list[int]:
    """
    Genera lista de minutos desde las 08:00 hasta las 17:00
    con pasos de duracion_min. Retorna valores en minutos absolutos.
    """
    inicio  = 8 * 60   # 08:00 = 480 min
    fin     = 17 * 60  # 17:00 = 1020 min
    return list(range(inicio, fin, duracion_min))
