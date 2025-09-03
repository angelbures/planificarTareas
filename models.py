from db import get_connection

# ---------- PROYECTOS ----------
def get_proyectos(order_by="orden"):
    sql = f"SELECT * FROM proyectos ORDER BY {order_by}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

def add_proyecto(nombre, orden):
    sql = "INSERT INTO proyectos(nombre, orden) VALUES (%s, %s)"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (nombre, orden))
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

# ---------- TAREAS ----------
def get_tareas(ref_fecha, order=1):
    if order == 1:
        sql = """SELECT t.*, p.nombre as proyecto 
                 FROM tareas t 
                 JOIN proyectos p ON t.proyecto_id=p.id
                 WHERE fecha >= %s
                 ORDER BY fecha, prioridad, proyecto"""
    else:
        sql = """SELECT t.*, p.nombre as proyecto 
                 FROM tareas t 
                 JOIN proyectos p ON t.proyecto_id=p.id
                 WHERE fecha >= %s
                 ORDER BY proyecto, id, prioridad, fecha"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (ref_fecha,))
            return cur.fetchall()

def add_tarea(proyecto_id, fecha, descripcion, prioridad, tiempo_estimado):
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
