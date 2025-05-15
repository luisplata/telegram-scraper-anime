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

def agregar_anime(nombre, cap, link=""):
    db = obtener_db()
    if buscar_anime(nombre, cap):
        return False

    nuevo = {
        "anime": nombre,
        "cap": cap,
        "link": link,
        "descargado": False,
        "subido": False,
        "compartido": False
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
