import sqlite3
from datetime import datetime
import bcrypt

DB_PATH = "data/app.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabla usuarios
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)

    # Tabla rutas
    c.execute("""
        CREATE TABLE IF NOT EXISTS rutas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            origen TEXT,
            destino TEXT,
            distancia REAL,
            duracion TEXT,
            consumo REAL,
            coste REAL,
            fecha TEXT,
            FOREIGN KEY(user_id) REFERENCES usuarios(id)
        )
    """)

    # Tabla de configuraciones (ej. logo)
    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Usuarios
# -----------------------------
def create_user(nombre, email, password, is_admin=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO usuarios (nombre, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                  (nombre, email, password_hash, is_admin))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True


def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    return user


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash)


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nombre, email, is_admin FROM usuarios")
    users = c.fetchall()
    conn.close()
    return users


# -----------------------------
# Rutas
# -----------------------------
def save_route(user_id, origen, destino, distancia, duracion, consumo, coste):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("""INSERT INTO rutas (user_id, origen, destino, distancia, duracion, consumo, coste, fecha)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (user_id, origen, destino, distancia, duracion, consumo, coste, fecha))
    conn.commit()
    conn.close()


def get_routes_by_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT origen, destino, distancia, duracion, consumo, coste, fecha FROM rutas WHERE user_id = ?", (user_id,))
    rutas = c.fetchall()
    conn.close()
    return rutas


def get_all_routes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM rutas")
    rutas = c.fetchall()
    conn.close()
    return rutas


# -----------------------------
# Configuración
# -----------------------------
def save_config(clave, valor):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES (?, ?)", (clave, valor))
    conn.commit()
    conn.close()


def get_config(clave):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT valor FROM config WHERE clave = ?", (clave,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None
