# ==================================================
# IAMD CHAT — Persistencia SQLite (solo números)
# ==================================================
import os
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.environ.get("IAMD_DB", "data/iamd_chat.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    sala        TEXT NOT NULL,
    idioma      TEXT NOT NULL DEFAULT 'ES',
    patron      TEXT NOT NULL DEFAULT 'cubico',
    creado      TEXT NOT NULL,
    ultimo_visto TEXT
);

CREATE TABLE IF NOT EXISTS mensajes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sala          TEXT NOT NULL,
    emisor        TEXT NOT NULL,
    idioma_origen TEXT NOT NULL,
    patron        TEXT NOT NULL,
    numeros       TEXT NOT NULL,
    fecha         TEXT NOT NULL,
    leido         INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS traducciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    mensaje_id    INTEGER NOT NULL REFERENCES mensajes(id) ON DELETE CASCADE,
    idioma        TEXT NOT NULL,
    texto         TEXT NOT NULL,
    UNIQUE(mensaje_id, idioma)
);

CREATE INDEX IF NOT EXISTS idx_mensajes_sala ON mensajes(sala, id);
CREATE INDEX IF NOT EXISTS idx_trad_mensaje  ON traducciones(mensaje_id);
"""


def init_db():
    with conexion() as con:
        con.executescript(SCHEMA)


@contextmanager
def conexion():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def registrar_usuario(nombre, sala, idioma, patron):
    now = datetime.utcnow().isoformat()
    with conexion() as con:
        cur = con.execute(
            "INSERT INTO usuarios (nombre, sala, idioma, patron, creado, ultimo_visto) "
            "VALUES (?,?,?,?,?,?)",
            (nombre, sala, idioma, patron, now, now),
        )
        return cur.lastrowid


def actualizar_visto(nombre, sala):
    with conexion() as con:
        con.execute(
            "UPDATE usuarios SET ultimo_visto=? WHERE nombre=? AND sala=?",
            (datetime.utcnow().isoformat(), nombre, sala),
        )


def guardar_mensaje(sala, emisor, idioma_origen, patron, numeros):
    with conexion() as con:
        cur = con.execute(
            "INSERT INTO mensajes (sala, emisor, idioma_origen, patron, numeros, fecha) "
            "VALUES (?,?,?,?,?,?)",
            (
                sala, emisor, idioma_origen, patron,
                json.dumps(numeros, ensure_ascii=False),
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid


def guardar_traduccion(mensaje_id, idioma, texto):
    with conexion() as con:
        con.execute(
            "INSERT OR IGNORE INTO traducciones (mensaje_id, idioma, texto) "
            "VALUES (?,?,?)",
            (mensaje_id, idioma, texto),
        )


def obtener_traduccion(mensaje_id, idioma):
    with conexion() as con:
        row = con.execute(
            "SELECT texto FROM traducciones WHERE mensaje_id=? AND idioma=?",
            (mensaje_id, idioma),
        ).fetchone()
        return row["texto"] if row else None


def historial_sala(sala, limite=50, desde_id=0):
    with conexion() as con:
        rows = con.execute(
            "SELECT id, sala, emisor, idioma_origen, patron, numeros, fecha "
            "FROM mensajes WHERE sala=? AND id>? ORDER BY id ASC LIMIT ?",
            (sala, desde_id, limite),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "sala": r["sala"],
            "emisor": r["emisor"],
            "idioma_origen": r["idioma_origen"],
            "patron": r["patron"],
            "numeros": json.loads(r["numeros"]),
            "fecha": r["fecha"],
        }
        for r in rows
    ]


def contar_mensajes(sala=None):
    with conexion() as con:
        if sala:
            return con.execute(
                "SELECT COUNT(*) c FROM mensajes WHERE sala=?", (sala,)
            ).fetchone()["c"]
        return con.execute("SELECT COUNT(*) c FROM mensajes").fetchone()["c"]