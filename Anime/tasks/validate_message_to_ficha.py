import json
import os
import re
import logging
import re
import requests

from Anime.model import Anime, Episode
from db_manager import AnimeDB
logger = logging.getLogger(__name__)

def validar_si_es_una_ficha_anime(message):
    return "Título:" in message or "Capítulos:" in message or "Episodios:" in message or \
           "Género:" in message or "Sinopsis:" in message or "Audio:" in message or \
           "Sub" in message


def extraer_titulo_y_cap(ficha_texto):
    titulo_match = re.search(r'T[ií]tulo:\s*(.+)', ficha_texto, re.IGNORECASE)
    titulo = limpiar_titulo(titulo_match.group(1)) if titulo_match else \
        limpiar_titulo(ficha_texto.split('\n')[0])

    cap_match = re.search(r'(Cap[ií]tulos?|Episodios?):\s*(\d+)', ficha_texto, re.IGNORECASE)
    cap = cap_match.group(2) if cap_match else None

    generos_match = re.search(r'G[eé]neros:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
    generos = [g.strip() for g in generos_match.group(1).split(',') if g.strip()] if generos_match else []

    sinopsis_match = re.search(r'Sin[oó]psis:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
    sinopsis = sinopsis_match.group(1).strip() if sinopsis_match else "Sin sinopsis disponible."

    subtitulos_match = re.search(r'Subt[ií]tulos?:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
    subtitulos = [s.strip() for s in subtitulos_match.group(1).split(',') if s.strip()] if subtitulos_match else ["Español"]

    return titulo, cap, generos, sinopsis, subtitulos


def limpiar_titulo(texto):
    return re.sub(r'[\*\n]+', ' ', texto).strip().lower()

def limpiar_nombre_archivo(nombre: str) -> str:
    # Elimina caracteres no válidos en Windows para rutas
    return re.sub(r'[<>:"/\\|?*]', '', nombre)

def get_all_caps(message, messages, titulo, db: AnimeDB) -> list[Episode]:
    caps = []
    ficha_index = messages.index(message)
    titulo_normalizado = limpiar_titulo(titulo)
    start = max(0, ficha_index - 20)
    end = min(len(messages), ficha_index + 20)
    mensajes_relacionados = messages[start:end]
    # print(f"Validando cnatidad de mensajes relacionados: {len(messages)} {ficha_index} {len(mensajes_relacionados)}")
    for msg_rel in mensajes_relacionados:
        texto_rel = getattr(msg_rel, 'text', '') or ''
        # print(f"Validando mensaje relacionado: {titulo} {msg_rel.id} - {texto_rel[:50]}...")
        if titulo_normalizado not in limpiar_titulo(texto_rel):
            continue
        if not msg_rel.media:
            continue
        cap_num = is_cap_to_anime(texto_rel, titulo_normalizado)
        if cap_num is not None:
            # Verificar si el capítulo ya existe en la base de datos
            if db.buscar_anime(titulo_normalizado, cap_num):
                # print(f"Capítulo {cap_num} ya existe en la base de datos para {titulo_normalizado}.")
                pass
            else:
                # print(f"Capítulo {cap_num} no encontrado en la base de datos, creando nuevo capítulo.")
                db.agregar_anime(titulo_normalizado, cap_num)
            anime_db = db.buscar_anime(titulo_normalizado, cap_num)
            cap = Episode(
                title=f"{limpiar_titulo(titulo)} - Capítulo {cap_num}",
                number=cap_num,
                link=f"link sample",
                message_id=msg_rel.id
            )
            # print(f"Capítulo encontrado: {cap.title} - {cap.number} message_id {cap.message_id}")
            caps.append(cap)
        else:
            print(f"Este es el cover image")
            pass
    return caps

def is_cap_to_anime(texto_rel, titulo):
    # Limpieza para comparar títulos
    titulo_normalizado = limpiar_titulo(titulo)
    texto_limpio = limpiar_titulo(texto_rel)

    # Regex 1: Formato común con "Capítulo" o "Capitulo"
    match1 = re.search(r'Cap[ií]tulo\s*(\d+)', texto_rel, re.IGNORECASE)

    # Regex 2: Formato con título seguido de número (Ej: "Nombre - 05" o "Nombre 05")
    match2 = re.search(rf'{re.escape(titulo_normalizado)}\s*[-–]?\s*(\d+)', texto_limpio)

    cap_num = None
    if match1:
        cap_num = int(match1.group(1))
    elif match2:
        cap_num = int(match2.group(1))

    if cap_num:
        # print(f"✅ Capítulo detectado: {cap_num} para título: {titulo} en texto: {texto_rel[:50]}...")
        return cap_num
    else:
        print(f"❌ No se encontró capítulo para título: {titulo} en texto: {texto_rel[:50]}...")
        return None


def save_anime_to_json(anime: Anime):
    path = f"anime_{anime.slug}.json"
    nuevo_dict = anime.to_dict()
    slug_actual = nuevo_dict["slug"]

    data_existente = []

    # Leer archivo si existe
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                data_existente = json.load(file)
                if not isinstance(data_existente, list):
                    print(f"⚠️ El archivo {path} no es una lista JSON. Se sobrescribirá.")
                    data_existente = []
        except json.JSONDecodeError:
            print(f"⚠️ Error al decodificar JSON en {path}. Se sobrescribirá con datos nuevos.")
        except Exception as e:
            print(f"❌ Error inesperado al leer {path}: {e}")

    # Reemplazar o agregar el anime nuevo
    reemplazado = False
    for i, existing in enumerate(data_existente):
        if existing.get("slug") == slug_actual:
            # Fusionar episodios
            episodios_exist = {ep["number"]: ep for ep in existing.get("caps", [])}
            for nuevo_ep in nuevo_dict.get("caps", []):
                episodios_exist[nuevo_ep["number"]] = nuevo_ep
            nuevo_dict["caps"] = list(episodios_exist.values())

            # Fusionar otros campos si están vacíos en el nuevo
            for field in ["image", "genres", "alterNames"]:
                if not nuevo_dict.get(field) and existing.get(field):
                    nuevo_dict[field] = existing[field]

            data_existente[i] = nuevo_dict
            reemplazado = True
            break

    if not reemplazado:
        data_existente.append(nuevo_dict)

    # Guardar el arreglo completo actualizado
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data_existente, file, indent=2, ensure_ascii=False)
        print(f"💾 Archivo actualizado: {path}")

    return path, data_existente



def cargar_anime_json(path: str) -> dict:
    """
    Carga y retorna el contenido JSON de un anime desde un archivo dado.

    Asume que el archivo contiene un único anime.
    Retorna None si el archivo no existe o tiene errores.
    """
    if not os.path.exists(path):
        print(f"⚠️ Archivo no encontrado: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error al decodificar JSON en: {path}")
    except Exception as e:
        print(f"❌ Error inesperado al leer {path}: {e}")

    return None

def enviar_anime_completo(json_anime: dict, webhook, token) -> requests.Response:
    """
    Envía un anime completo al webhook del backend.
    
    Args:
        json_anime: Un diccionario (o lista de diccionarios) con la estructura del anime.

    Returns:
        La respuesta del servidor.
    """
    url = f"{webhook}"
    headers = {
        "X-Webhook-Token": f"{token}",
        "Content-Type": "application/json"
    }

    # Asegurarse de que el payload sea una lista
    if isinstance(json_anime, dict):
        payload = [json_anime]
    elif isinstance(json_anime, list):
        payload = json_anime
    else:
        raise ValueError("El JSON del anime debe ser un dict o una lista de dicts.")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False))
        return response
    except Exception as e:
        print(f"❌ Error al enviar anime a la API: {e}")
        return None