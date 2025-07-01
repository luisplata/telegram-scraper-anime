import sqlite3
from typing import Optional, Any, Dict

class AnimeDB:
    def __init__(self, db_path="animes.db"):
        self.db_path = db_path
        self.lock_path = db_path + ".lock"
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS animes (
                    anime TEXT NOT NULL,
                    cap INTEGER NOT NULL,
                    link TEXT,
                    descargado BOOLEAN DEFAULT 0,
                    subido BOOLEAN DEFAULT 0,
                    compartido BOOLEAN DEFAULT 0,
                    audio TEXT DEFAULT 'sub',
                    PRIMARY KEY (anime, cap)
                )
            """)
            conn.commit()

    def buscar_anime(self, nombre: str, cap: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT * FROM animes WHERE LOWER(anime)=LOWER(?) AND cap=?",
                (nombre, cap)
            )
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None

    def agregar_anime(self, nombre: str, cap: int, link: str = "", audio: str = "sub") -> bool:
        if self.buscar_anime(nombre, cap):
            return False
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO animes (anime, cap, link, descargado, subido, compartido, audio) VALUES (?, ?, ?, 0, 0, 0, ?)",
                (nombre, cap, link, audio)
            )
            conn.commit()
            return True

    def actualizar_estado_anime(self, nombre: str, cap: int, **kwargs) -> bool:
        if not kwargs:
            return False
        keys = []
        values = []
        for campo, valor in kwargs.items():
            keys.append(f"{campo}=?")
            values.append(valor)
        values.extend([nombre, cap])
        with self._connect() as conn:
            cur = conn.execute(
                f"UPDATE animes SET {', '.join(keys)} WHERE LOWER(anime)=LOWER(?) AND cap=?",
                tuple(values)
            )
            conn.commit()
            return cur.rowcount > 0

    def eliminar_anime(self, nombre: str, cap: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM animes WHERE LOWER(anime)=LOWER(?) AND cap=?",
                (nombre, cap)
            )
            conn.commit()
            return cur.rowcount > 0

    def listar_animes(self):
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM animes")
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

# Recuerda agregar 'filelock' a tu requirements.txt