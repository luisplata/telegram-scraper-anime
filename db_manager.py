import json
import os

DB_PATH = "db.json"

def obtener_db():
    if not os.path.exists(DB_PATH):
        return {"animes": []}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ Error al leer la base de datos. Se usará una vacía.")
        return {"animes": []}

def guardar_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def buscar_anime(nombre, cap):
    db = obtener_db()
    for anime in db["animes"]:
        if anime["anime"].lower() == nombre.lower() and anime["cap"] == cap:
            return anime
    return None

def agregar_anime(nombre, cap, link="", audio="sub"):
    db = obtener_db()
    if buscar_anime(nombre, cap):
        return False

    nuevo = {
        "anime": nombre,
        "cap": cap,
        "link": link,
        "descargado": False,
        "subido": False,
        "compartido": False,
        "audio": audio,
    }
    db["animes"].append(nuevo)
    guardar_db(db)
    return True

def actualizar_estado_anime(nombre, cap, **kwargs):
    db = obtener_db()
    modificado = False
    for anime in db["animes"]:
        if anime["anime"].lower() == nombre.lower() and anime["cap"] == cap:
            for campo, valor in kwargs.items():
                anime[campo] = valor
            modificado = True
            break
    if modificado:
        guardar_db(db)
    return modificado


import json
import os

class AnimeDB:
    def __init__(self, db_path="db.json"):
        self.db_path = db_path
        self.data = {"animes": []}
        self.load()

    def load(self):
        if not os.path.exists(self.db_path):
            self.data = {"animes": []}
            return
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Error al leer la base de datos {self.db_path}. Se usará una vacía.")
            self.data = {"animes": []}

    def save(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def buscar_anime(self, nombre, cap):
        for anime in self.data["animes"]:
            if anime["anime"].lower() == nombre.lower() and anime["cap"] == cap:
                return anime
        return None

    def agregar_anime(self, nombre, cap, link="", audio="sub"):
        if self.buscar_anime(nombre, cap):
            return False
        nuevo = {
            "anime": nombre,
            "cap": cap,
            "link": link,
            "descargado": False,
            "subido": False,
            "compartido": False,
            "audio": audio,
        }
        self.data["animes"].append(nuevo)
        self.save()
        return True

    def actualizar_estado_anime(self, nombre, cap, **kwargs):
        modificado = False
        for anime in self.data["animes"]:
            if anime["anime"].lower() == nombre.lower() and anime["cap"] == cap:
                for campo, valor in kwargs.items():
                    anime[campo] = valor
                modificado = True
                break
        if modificado:
            self.save()
        return modificado

    def eliminar_anime(self, nombre, cap):
        original_len = len(self.data["animes"])
        self.data["animes"] = [
            anime for anime in self.data["animes"]
            if not (anime["anime"].lower() == nombre.lower() and anime["cap"] == cap)
        ]
        if len(self.data["animes"]) < original_len:
            self.save()
            return True
        return False

    def listar_animes(self):
        return self.data["animes"]

# Ejemplo de uso:
# db = AnimeDB("db.json")
# db.agregar_anime("Mi Anime", 1)
# anime = db.buscar_anime("Mi Anime", 1)
# db.actualizar_estado_anime("Mi Anime", 1, descargado=True)
# db.eliminar_anime("Mi Anime", 1)