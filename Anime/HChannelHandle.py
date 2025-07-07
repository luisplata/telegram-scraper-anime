from Anime.ChannelHandle import ChannelHandle
from datetime import datetime, timedelta, timezone
import os
import re
import unicodedata
import time
import json

from telegram_client import descargar_video_de_mensaje
from uploader import subir_video, eliminar_archivo
from utils import formatear_nombre_video
from sharer import compartir_anime, validate_if_anime_can_be_shared
from config import VIEW_URL
from telethon.sync import TelegramClient
from db_manager import AnimeDB
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument


class Source:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def to_dict(self):
        return {
            "name": self.name,
            "url": self.url
        }

class Episode:
    def __init__(self, title: str, number: int, link: str = ""):
        self.title = title
        self.number = number
        self.link = link
        self.source = []

    def add_source(self, source: Source):
        self.source.append(source)

    def to_dict(self):
        return {
            "title": self.title,
            "number": self.number,
            "link": self.link,
            "source": [s.to_dict() for s in self.source]
        }

class Anime:
    def __init__(self, name: list[str], slug: str, description: str, image: str):
        self.name = name
        self.slug = slug
        self.description = description
        self.image = image
        self.caps = []
        self.alterNames = []
        self.genres = []

    def add_cap(self, cap: Episode):
        self.caps.append(cap)

    def to_dict(self):
        return {
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "image": self.image,
            "caps": [cap.to_dict() for cap in self.caps],
            "alterNames": self.alterNames,
            "genres": self.genres
        }


class HChannelHandle(ChannelHandle):
    key = "h_anime"
    channel_id = 2428772016  # Reemplaza con tu canal real

    def parse_message(self, message):
        if message.text and "H-Episodio" in message.text:
            return f"H-Anime: {message.text}"
        return super().parse_message(message)

    @staticmethod
    def get_last_offset(db: AnimeDB) -> int:
        try:
            with open("last_offset_h.txt", "r") as f:
                return int(f.read())
        except Exception:
            return 0

    @staticmethod
    def set_last_offset(offset: int):
        with open("last_offset_h.txt", "w") as f:
            f.write(str(offset))

    def es_imagen(self, message):
        return isinstance(message.media, MessageMediaPhoto)

    def es_video(self, message):
        if isinstance(message.media, MessageMediaDocument):
            if hasattr(message.media.document, 'mime_type'):
                return message.media.document.mime_type.startswith('video')
            for attr in message.media.document.attributes:
                if hasattr(attr, 'file_name') and attr.file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    return True
        return False

    def obtener_extension(self, message, tipo):
        if tipo == "imagen":
            return "jpg"
        if tipo == "video":
            if hasattr(message.media.document, 'mime_type'):
                mime = message.media.document.mime_type
                return {
                    "video/mp4": "mp4",
                    "video/x-matroska": "mkv",
                    "video/x-msvideo": "avi",
                    "video/quicktime": "mov"
                }.get(mime, "mp4")
            for attr in message.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    ext = os.path.splitext(attr.file_name)[1].lstrip('.')
                    return ext or "mp4"
        return "dat"

    def process_messages(
        self,
        client: TelegramClient,
        db: AnimeDB,
        limit: int = 50,
        max_anime_to_process: int = 1,
        dias: int = -1,
    ) -> int:
        anime_to_process = 0
        archivos_subidos = 0
        MAX_SUBIDAS = 150
        entity = client.get_entity(self.channel_id)
        last_id = 0 #if dias != -1 else self.get_last_offset(db)
        animes = []

        while archivos_subidos < MAX_SUBIDAS and anime_to_process < max_anime_to_process:
            messages = list(client.iter_messages(entity, limit=limit, offset_id=last_id))

            for message in messages:
                if archivos_subidos >= MAX_SUBIDAS or anime_to_process >= max_anime_to_process:
                    break

                texto = getattr(message, 'text', '') or ''
                if "Título:" in texto:
                    titulo, total_cap, generos, sinopsis, subtitulo = self.extraer_titulo_y_cap(texto)
                    print(f"Ficha encontrada: {titulo} - Caps: {total_cap}")

                    anime = Anime(
                        name=titulo.split(),
                        slug=self.limpiar_titulo(titulo).replace(" ", "-"),
                        description=texto,
                        image=""
                    )
                    anime.genres = generos
                    anime.alterNames = subtitulo
                    self.subfolder = self.limpiar_titulo(titulo)

                    img_count = 1
                    vid_count = 1

                    ficha_index = messages.index(message)
                    titulo_normalizado = self.limpiar_titulo(titulo)
                    mensajes_relacionados = messages[ficha_index-10:ficha_index+10]

                    for msg_rel in mensajes_relacionados:
                        texto_rel = getattr(msg_rel, 'text', '') or ''
                        if titulo_normalizado not in self.limpiar_titulo(texto_rel):
                            continue
                        if not msg_rel.media:
                            continue
                        texto_rel = getattr(msg_rel, 'text', '') or ''
                        if self.limpiar_titulo(titulo) in self.limpiar_titulo(texto_rel):
                            cap_match = re.search(r'Cap[ií]tulo\s*(\d+)', texto_rel, re.IGNORECASE)
                            cap_rel = cap_match.group(1) if cap_match else None
                            if not cap_rel:
                                continue
                            cap_num = int(cap_rel)

                            # Verificar si ya está en la DB
                            if db.buscar_anime(titulo, cap_num):
                                print(f"Saltando {titulo} cap {cap_num}, ya está en DB")
                                #cargar los caps del anime
                                anime.caps = [cap for cap in db.buscar_anime(titulo, cap_num).get('caps', [])]
                                continue

                            tipo = None
                            if self.es_imagen(msg_rel):
                                tipo = "imagen"
                                ext = self.obtener_extension(msg_rel, tipo)
                                rel_path = os.path.join(self.key, self.subfolder, "images", f"img_{self.key}_{img_count}.{ext}")
                                file_path = os.path.join("downloads", rel_path)
                                anime.image = f"https://mega.nz/embed/!fakeid!{msg_rel.id}"
                                img_count += 1

                            elif self.es_video(msg_rel):
                                tipo = "video"
                                ext = self.obtener_extension(msg_rel, tipo)
                                rel_path = os.path.join(self.key, self.subfolder, "videos", f"video_{self.key}_{vid_count}.{ext}")
                                file_path = os.path.join("downloads", rel_path)
                                vid_count += 1

                                episode = Episode(
                                    title=f"{titulo} - Episodio {cap_num}",
                                    number=cap_num,
                                    link=VIEW_URL.format(msg_rel.id)
                                )
                                episode.add_source(Source(name="Local", url=f"https://mega.nz/embed/!fakeid!{msg_rel.id}"))
                                anime.add_cap(episode)

                                # Agregar a la base de datos
                                db.agregar_anime(titulo, cap_num, link=episode.link, audio="sub")
                                archivos_subidos += 1
                                anime_to_process += 1

                    animes.append(anime)
                    time.sleep(1)
                    guardar_si_no_existe_o_actualizar(anime, key=f"anime_{self.key}_{HChannelHandle.limpiar_titulo_slug(anime.slug)}.json")

            if messages:
                last_id = min(msg.id for msg in messages)
                if dias == -1:
                    self.set_last_offset(last_id)

        return anime_to_process

    @staticmethod
    def limpiar_titulo(texto):
        return re.sub(r'[\*\n]+', ' ', texto).strip().lower()
    
    @staticmethod
    def limpiar_titulo_slug(texto: str) -> str:
        # 1. Normaliza acentos y caracteres unicode
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')

        # 2. Reemplaza espacios y guiones por guiones bajos
        texto = re.sub(r'[\s\-]+', '_', texto)

        # 3. Elimina todo lo que no sea letras, números o guion bajo
        texto = re.sub(r'[^a-zA-Z0-9_]', '', texto)

        # 4. Convierte todo a minúsculas y quita guiones bajos al inicio/final
        return texto.strip('_').lower()

    @staticmethod
    def extraer_titulo_y_cap(ficha_texto):
        titulo_match = re.search(r'T[ií]tulo:\s*(.+)', ficha_texto, re.IGNORECASE)
        titulo = HChannelHandle.limpiar_titulo(titulo_match.group(1)) if titulo_match else \
            HChannelHandle.limpiar_titulo(ficha_texto.split('\n')[0])

        cap_match = re.search(r'(Cap[ií]tulos?|Episodios?):\s*(\d+)', ficha_texto, re.IGNORECASE)
        cap = cap_match.group(2) if cap_match else None

        generos_match = re.search(r'G[eé]neros:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
        generos = [g.strip() for g in generos_match.group(1).split(',') if g.strip()] if generos_match else []

        sinopsis_match = re.search(r'Sin[oó]psis:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
        sinopsis = sinopsis_match.group(1).strip() if sinopsis_match else "Sin sinopsis disponible."

        subtitulos_match = re.search(r'Subt[ií]tulos?:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
        subtitulos = [s.strip() for s in subtitulos_match.group(1).split(',') if s.strip()] if subtitulos_match else ["Español"]

        return titulo, cap, generos, sinopsis, subtitulos
   
def guardar_anime(anime: Anime, filename: str):
    nuevo_dict = anime.to_dict()

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existente = json.load(f)
            except json.JSONDecodeError:
                print(f"Error leyendo {filename}, se sobrescribirá.")
                existente = None

        if existente:
            # Combinar episodios antiguos y nuevos, evitando duplicados por "number"
            episodios_antiguos = {ep['number']: ep for ep in existente.get('caps', [])}
            for nuevo_ep in nuevo_dict.get('caps', []):
                episodios_antiguos[nuevo_ep['number']] = nuevo_ep

            nuevo_dict['caps'] = list(episodios_antiguos.values())

            # Mantener campos como image, genres, etc., solo si no están en blanco
            if not nuevo_dict.get('image') and existente.get('image'):
                nuevo_dict['image'] = existente['image']
            if not nuevo_dict.get('genres') and existente.get('genres'):
                nuevo_dict['genres'] = existente['genres']
            if not nuevo_dict.get('alterNames') and existente.get('alterNames'):
                nuevo_dict['alterNames'] = existente['alterNames']

    # Guardar archivo final combinado
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(nuevo_dict, f, indent=2, ensure_ascii=False)


def anime_a_json_filename(anime: Anime, key: str) -> str:
    from Anime.HChannelHandle import HChannelHandle  # Importación aquí para evitar circularidad si aplica
    slug = HChannelHandle.limpiar_titulo_slug(anime.slug)
    return f"anime_{key}_{slug}.json"


def guardar_si_no_existe_o_actualizar(anime: Anime, key: str):
    filename = anime_a_json_filename(anime, key)
    guardar_anime(anime, filename=filename)
