# db.py
import pymysql
import datetime

# === CONFIGURA AQUÍ TUS CREDENCIALES ===
HOST = "localhost"
USER = "root"
PASSWORD = "RootSQL"   # <-- cámbialo
DB_NAME = "planner"

def get_connection():
    """Conexión directa a la BBDD (asegúrate de llamar ensure_database() antes)."""
    return pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

def _get_server_connection():
    """Conexión al servidor sin seleccionar base de datos."""
    return pymysql.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def ensure_database():
    """
    Crea la base de datos y tablas si no existen.
    Si las tablas están vacías, inserta datos de ejemplo.
    Es idempotente.
    """
    # 1) Crea la BBDD si no existe
    with _get_server_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4;")

    # 2) Crea tablas si no existen (en orden correcto)
    with get_connection() as conn:
        with conn.cursor() as cur:
            # proyectos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS proyectos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(30) NOT NULL,
                    orden INT NOT NULL
                );
            """)
            # dias
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dias (
                    fecha DATE PRIMARY KEY,
                    reuniones INT DEFAULT 0,     -- minutos
                    explotacion INT DEFAULT 0,   -- minutos
                    maximo INT NOT NULL          -- minutos
                );
            """)
            # tareas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tareas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    proyecto_id INT NOT NULL,
                    fecha DATE NOT NULL,
                    descripcion VARCHAR(100) NOT NULL,
                    prioridad INT NOT NULL,
                    tiempo_estimado INT NOT NULL,
                    estado VARCHAR(20) DEFAULT 'pendiente',
                    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
                );
            """)
        conn.commit()

        # 3) Si están vacías, insertar demo
        with conn.cursor() as cur:
            # Inserta proyectos primero
            cur.execute("SELECT COUNT(*) AS c FROM proyectos;")
            c_proy = cur.fetchone()["c"]
            if c_proy == 0:
                cur.executemany(
                    "INSERT INTO proyectos (nombre, orden) VALUES (%s,%s)",
                    [
                        ("Proyecto Demo", 1),
                        ("Proyecto Prueba", 2),
                        ("Migración SAP", 3),
                    ],
                )
                conn.commit()  # <-- asegúrate de que los proyectos están insertados antes de seguir

            # Inserta días
            cur.execute("SELECT COUNT(*) AS c FROM dias;")
            c_dias = cur.fetchone()["c"]
            if c_dias == 0:
                today = datetime.date.today()
                rows = []
                for i, (reun, expl, maxm) in enumerate([(60,120,480),(30,60,480),(90,90,480),(45,120,480)]):
                    d = today + datetime.timedelta(days=i)
                    rows.append((d, reun, expl, maxm))
                cur.executemany(
                    "INSERT INTO dias (fecha, reuniones, explotacion, maximo) VALUES (%s,%s,%s,%s)",
                    rows,
                )
                conn.commit()

            # Inserta tareas solo si hay proyectos
            cur.execute("SELECT COUNT(*) AS c FROM tareas;")
            c_tareas = cur.fetchone()["c"]
            cur.execute("SELECT id FROM proyectos ORDER BY orden;")
            proys = [r["id"] for r in cur.fetchall()]
            if c_tareas == 0 and len(proys) >= 1:
                # fallback si hay menos de 3 proyectos
                while len(proys) < 3:
                    proys.append(proys[-1])
                p1, p2, p3 = proys[:3]
                today = datetime.date.today()
                demo = [
                    (p1, today, "Preparar informe semanal", 1, 120, "pendiente"),
                    (p2, today, "Revisión de código Python", 2, 90, "finalizada"),
                    (p3, today + datetime.timedelta(days=1), "Configurar servidor de pruebas", 5, 180, "pendiente"),
                    (p1, today + datetime.timedelta(days=2), "Actualizar documentación", 3, 60, "pendiente"),
                    (p2, today + datetime.timedelta(days=3), "Reunión con equipo", 1, 90, "pendiente"),
                ]
                cur.executemany(
                    """INSERT INTO tareas
                       (proyecto_id, fecha, descripcion, prioridad, tiempo_estimado, estado)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    demo,
                )
                conn.commit()
            # Inserta proyecto de ejemplo si no hay ninguno
            cur.execute("SELECT COUNT(*) as n FROM proyectos")
            if cur.fetchone()["n"] == 0:
                cur.execute("INSERT INTO proyectos(nombre, orden) VALUES ('Proyecto ejemplo', 99)")
        conn.commit()

def reset_database():
    """Borra todas las tablas y datos de la base de datos."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS tareas")
            cur.execute("DROP TABLE IF EXISTS dias")
            cur.execute("DROP TABLE IF EXISTS proyectos")
        conn.commit()
    ensure_database()  # Vuelve a crear las tablas vacías

## full_reset_database ha sido deshabilitada. Usa reset_database() en su lugar.
# def full_reset_database():
#     """Borra la base de datos y la crea correctamente desde cero, con datos de ejemplo válidos."""
#     # 1. Elimina la base de datos completamente
#     with _get_server_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`;")
#             cur.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4;")
#
#     # 2. Crea las tablas en el orden correcto
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 CREATE TABLE IF NOT EXISTS proyectos (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     nombre VARCHAR(30) NOT NULL,
#                     orden INT NOT NULL
#                 );
#             """)
#             cur.execute("""
#                 CREATE TABLE IF NOT EXISTS dias (
#                     fecha DATE PRIMARY KEY,
#                     reuniones INT DEFAULT 0,
#                     explotacion INT DEFAULT 0,
#                     maximo INT NOT NULL
#                 );
#             """)
#             cur.execute("""
#                 CREATE TABLE IF NOT EXISTS tareas (
#                     id INT AUTO_INCREMENT PRIMARY KEY,
#                     proyecto_id INT NOT NULL,
#                     fecha DATE NOT NULL,
#                     descripcion VARCHAR(100) NOT NULL,
#                     prioridad INT NOT NULL,
#                     tiempo_estimado INT NOT NULL,
#                     estado VARCHAR(20) DEFAULT 'pendiente',
#                     FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
#                 );
#             """)
#         conn.commit()
#
#         # 3. Inserta datos de ejemplo válidos
#         with conn.cursor() as cur:
#             # Proyectos
#             cur.executemany(
#                 "INSERT INTO proyectos (nombre, orden) VALUES (%s,%s)",
#                 [
#                     ("Proyecto Demo", 1),
#                     ("Proyecto Prueba", 2),
#                     ("Migración SAP", 3),
#                 ],
#             )
#             conn.commit()
#
#             # Días
#             today = datetime.date.today()
#             rows = []
#             for i, (reun, expl, maxm) in enumerate([(60,120,480),(30,60,480),(90,90,480),(45,120,480)]):
#                 d = today + datetime.timedelta(days=i)
#                 rows.append((d, reun, expl, maxm))
#             cur.executemany(
#                 "INSERT INTO dias (fecha, reuniones, explotacion, maximo) VALUES (%s,%s,%s,%s)",
#                 rows,
#             )
#             conn.commit()
#
#             # Tareas (asociadas a proyectos válidos)
#             cur.execute("SELECT id FROM proyectos ORDER BY orden;")
#             proys = [r["id"] for r in cur.fetchall()]
#             while len(proys) < 3:
#                 proys.append(proys[-1])
#             p1, p2, p3 = proys[:3]
#             demo = [
#                 (p1, today, "Preparar informe semanal", 1, 120, "pendiente"),
#                 (p2, today, "Revisión de código Python", 2, 90, "finalizada"),
#                 (p3, today + datetime.timedelta(days=1), "Configurar servidor de pruebas", 5, 180, "pendiente"),
#                 (p1, today + datetime.timedelta(days=2), "Actualizar documentación", 3, 60, "pendiente"),
#                 (p2, today + datetime.timedelta(days=3), "Reunión con equipo", 1, 90, "pendiente"),
#             ]
#             cur.executemany(
#                 """INSERT INTO tareas
#                    (proyecto_id, fecha, descripcion, prioridad, tiempo_estimado, estado)
#                    VALUES (%s,%s,%s,%s,%s,%s)""",
#                 demo,
#             )
#             conn.commit()
