import json
import os
import re
import logging
import re

from Anime.model import Anime, Episode
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

def get_all_caps(message, messages, titulo) -> list[Episode]:
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
            cap = Episode(
                title=f"{limpiar_titulo(titulo)} - Capítulo {cap_num}",
                number=cap_num,
                link=f"https://t.me/c/{msg_rel.peer_id.channel_id}/{msg_rel.id}",
                message_id=msg_rel.id
            )
            # print(f"Capítulo encontrado: {cap.title} - {cap.number} message_id {cap.message_id}")
            caps.append(cap)
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
    # print(nuevo_dict)

    data_existente = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                data_existente = json.load(file)
                # print(f"📂 Archivo {path} encontrado, cargando datos existentes.")
        except json.JSONDecodeError:
            print(f"⚠️ Error al decodificar JSON en {path}. Se sobrescribirá con datos nuevos.")
        except Exception as e:
            print(f"❌ Error inesperado al leer {path}: {e}")

    # Fusionar episodios
    episodios_exist = {ep["number"]: ep for ep in data_existente.get("caps", [])}
    for nuevo_ep in nuevo_dict.get("caps", []):
        episodios_exist[nuevo_ep["number"]] = nuevo_ep
    nuevo_dict["caps"] = list(episodios_exist.values())

    # Fusionar otros campos si están vacíos en el nuevo
    for field in ["image", "genres", "alterNames"]:
        if not nuevo_dict.get(field) and data_existente.get(field):
            nuevo_dict[field] = data_existente[field]

    # Guardar el JSON final
    with open(path, "w", encoding="utf-8") as file:
        json.dump(nuevo_dict, file, indent=2, ensure_ascii=False)
        print(f"💾 Archivo actualizado: {path}")

    return path, nuevo_dict