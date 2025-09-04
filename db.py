
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
                    descripcion VARCHAR(200),
                    prioridad INT NOT NULL,
                    tiempo_estimado INT NOT NULL,   -- minutos
                    estado ENUM('pendiente','finalizada') DEFAULT 'pendiente',
                    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
                    FOREIGN KEY (fecha) REFERENCES dias(fecha) ON DELETE CASCADE
                );
            """)
        conn.commit()

        # 3) Si están vacías, insertar demo
        with conn.cursor() as cur:
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

            cur.execute("SELECT COUNT(*) AS c FROM dias;")
            c_dias = cur.fetchone()["c"]
            if c_dias == 0:
                today = datetime.date.today()
                rows = []
                # hoy y 3 días siguientes
                for i, (reun, expl, maxm) in enumerate([(60,120,480),(30,60,480),(90,90,480),(45,120,480)]):
                    d = today + datetime.timedelta(days=i)
                    rows.append((d, reun, expl, maxm))
                cur.executemany(
                    "INSERT INTO dias (fecha, reuniones, explotacion, maximo) VALUES (%s,%s,%s,%s)",
                    rows,
                )

            cur.execute("SELECT COUNT(*) AS c FROM tareas;")
            c_tareas = cur.fetchone()["c"]
            if c_tareas == 0:
                # Obtener IDs de proyectos
                cur.execute("SELECT id FROM proyectos ORDER BY orden;")
                proys = [r["id"] for r in cur.fetchall()]
                if len(proys) >= 3:
                    p1, p2, p3 = proys[:3]
                else:
                    # fallback si hay menos
                    proys = proys + [proys[-1]]*(3-len(proys)) if proys else [1,1,1]
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
