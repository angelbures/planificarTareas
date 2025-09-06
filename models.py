from db import get_connection

# ---------- PROYECTOS ----------
def get_proyectos(order_by="orden"):
    sql = f"SELECT * FROM proyectos ORDER BY {order_by}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

def add_proyecto(nombre, orden):
    # Si orden es None, calcula max(orden)+10; si viene valor, se respeta
    with get_connection() as conn:
        with conn.cursor() as cur:
            if orden is None:
                cur.execute("SELECT IFNULL(MAX(orden), 0) AS m FROM proyectos")
                m = cur.fetchone()["m"] if cur.rowcount != 0 else 0
                orden_calc = int(m) + 10
            else:
                orden_calc = orden
            cur.execute("INSERT INTO proyectos(nombre, orden) VALUES (%s, %s)", (nombre, orden_calc))
        conn.commit()

def update_proyecto(id, nombre, orden):
    sql = "UPDATE proyectos SET nombre=%s, orden=%s WHERE id=%s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (nombre, orden, id))
        conn.commit()

def delete_proyecto(id):
    sql = "DELETE FROM proyectos WHERE id=%s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id,))
        conn.commit()

# ---------- DIAS ----------
def get_dias(ref_fecha):
    sql = """
        SELECT d.*, 
        (maximo - reuniones - explotacion) AS disponible,
        IFNULL((SELECT SUM(tiempo_estimado) FROM tareas t WHERE t.fecha=d.fecha),0) as suma_tareas
        FROM dias d
        WHERE fecha >= %s AND fecha <= DATE_ADD(%s, INTERVAL 14 DAY)
        ORDER BY fecha
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (ref_fecha, ref_fecha))
            return cur.fetchall()

def add_dia(fecha, reuniones, explotacion, maximo):
    sql = "INSERT INTO dias(fecha, reuniones, explotacion, maximo) VALUES (%s,%s,%s,%s)"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (fecha, reuniones, explotacion, maximo))
        conn.commit()

def update_dia(fecha, reuniones, explotacion, maximo):
    sql = "UPDATE dias SET reuniones=%s, explotacion=%s, maximo=%s WHERE fecha=%s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (reuniones, explotacion, maximo, fecha))
        conn.commit()

def delete_dia(fecha):
    sql = "DELETE FROM dias WHERE fecha=%s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (fecha,))
        conn.commit()

def get_max_fecha_dia():
    sql = "SELECT MAX(fecha) as max_fecha FROM dias"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            return row["max_fecha"] if row else None

# ---------- TAREAS ----------
def get_tareas(ref_fecha, order=1):
    if order == 1:
        sql = """SELECT t.*, p.nombre as proyecto 
                 FROM tareas t 
                 LEFT JOIN proyectos p ON t.proyecto_id=p.id
                 WHERE t.fecha >= %s
                 ORDER BY t.fecha, t.prioridad, p.nombre"""
    else:
        # Orden por proyecto (según p.orden asc), luego prioridad y fecha (asc)
        sql = """SELECT t.*, p.nombre as proyecto 
                 FROM tareas t 
                 LEFT JOIN proyectos p ON t.proyecto_id=p.id
                 WHERE t.fecha >= %s
                 ORDER BY p.orden ASC, t.prioridad ASC, t.fecha ASC, t.id ASC"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (ref_fecha,))
            return cur.fetchall()

def add_tarea(proyecto_id, fecha, descripcion, prioridad, tiempo_estimado):
    # Si no se pasa proyecto_id, busca el proyecto con mayor orden
    if proyecto_id is None:
        sql_max = "SELECT id FROM proyectos ORDER BY orden DESC LIMIT 1"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_max)
                row = cur.fetchone()
                proyecto_id = row["id"] if row else None
    sql = """INSERT INTO tareas(proyecto_id, fecha, descripcion, prioridad, tiempo_estimado) 
             VALUES (%s,%s,%s,%s,%s)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (proyecto_id, fecha, descripcion, prioridad, tiempo_estimado))
        conn.commit()

def update_tarea(id, proyecto_id, fecha, descripcion, prioridad, tiempo_estimado, estado):
    sql = """UPDATE tareas 
             SET proyecto_id=%s, fecha=%s, descripcion=%s, prioridad=%s, tiempo_estimado=%s, estado=%s
             WHERE id=%s"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (proyecto_id, fecha, descripcion, prioridad, tiempo_estimado, estado, id))
        conn.commit()

def delete_tarea(id):
    sql = "DELETE FROM tareas WHERE id=%s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id,))
        conn.commit()
