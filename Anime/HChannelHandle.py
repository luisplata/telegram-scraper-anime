from Anime.ChannelHandle import ChannelHandle
from datetime import datetime, timedelta, timezone
import os
import re
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
    channel_id = 2428772016  # Reemplaza por el ID real del canal H

    def parse_message(self, message):
        # Personaliza la lógica de parseo para este canal
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
                if mime == "video/mp4":
                    return "mp4"
                elif mime == "video/x-matroska":
                    return "mkv"
                elif mime == "video/x-msvideo":
                    return "avi"
                elif mime == "video/quicktime":
                    return "mov"
            # fallback por nombre de archivo
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
        """
        Procesa mensajes del canal H-Anime.

        Args:
            client (TelegramClient): Cliente de Telethon.
            db (AnimeDB): Instancia de la base de datos de animes.
            limit (int): Número máximo de mensajes a revisar.
            max_anime_to_process (int): Número máximo de animes a procesar.
            dias (int): Límite de días hacia atrás para buscar mensajes. Si es -1, busca todos.

        Returns:
            int: Número de animes procesados.
        """
        anime_to_process = 0
        archivos_subidos = 0
        MAX_SUBIDAS = 150
        entity = client.get_entity(self.channel_id)
        fecha_limite = None
        if dias != -1:
            fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)
            last_id = 0
        else:
            last_id = self.get_last_offset(db)

        series = []  # <-- Mover la declaración aquí

        while archivos_subidos < MAX_SUBIDAS and anime_to_process < max_anime_to_process:
            messages = list(client.iter_messages(entity, limit=limit, offset_id=last_id))
            # if not messages:
            #     break

            for message in messages:
                if archivos_subidos >= MAX_SUBIDAS or anime_to_process >= max_anime_to_process:
                    break

                texto = getattr(message, 'text', '') or ''
                if "Título:" in texto:
                    # Es ficha
                    titulo_ficha, cap_ficha, generos, sinopsis, subtitulo = self.extraer_titulo_y_cap(texto)
                    print(f"Ficha encontrada: {titulo_ficha} - Caps: {cap_ficha}")
                    # time.sleep(1)
                    # Aquí es donde se agrega el capítulo a la serie
                    anime = Anime(
                        name=titulo_ficha.split(),  # separa el nombre en palabras como en tu JSON original
                        slug=self.limpiar_titulo(titulo_ficha).replace(" ", "-"),
                        description=sinopsis,
                        image=""
                    )
                    self.subfolder = self.limpiar_titulo(titulo_ficha)
                    # Busca mensajes relacionados en los siguientes mensajes
                    img_count = 1
                    vid_count = 1
                    for msg_rel in messages:
                        if not msg_rel.media:
                            continue
                        texto_rel = getattr(msg_rel, 'text', '') or ''
                        print(f"=====================================================")
                        print(f"limpiar_titulo msg_rel {self.limpiar_titulo(titulo_ficha)}: {self.limpiar_titulo(texto_rel)}")
                        # time.sleep(1)
                        #if self.limpiar_titulo(titulo_ficha) in self.limpiar_titulo(texto_rel):
                        # necesito comparar los strings ignorando mayúsculas y minúsculas
                        if self.limpiar_titulo(titulo_ficha) in self.limpiar_titulo(texto_rel):
                            # Busca el número de capítulo en el mensaje relacionado
                            cap_match = re.search(r'Cap[ií]tulo\s*(\d+)', texto_rel, re.IGNORECASE)
                            cap_rel = cap_match.group(1) if cap_match else None
                            print(f"=====================================================")
                            print(f"Mensaje id msg_rel ID {cap_rel}: {cap_ficha}")
                            # time.sleep(1)
                            print(f"=====================================================")
                            print(f"→ Relacionado: Mensaje ID {msg_rel.id}: {texto_rel}")
                            if self.es_imagen(msg_rel):
                                tipo = "imagen"
                                ext = self.obtener_extension(msg_rel, tipo)
                                rel_path = os.path.join(self.key, self.subfolder, "images", f"img_{self.key}_{img_count}.{ext}") if self.subfolder else os.path.join(self.key, "images", f"img_{self.key}_{img_count}.{ext}")
                                file_path = os.path.join("downloads", rel_path)
                                img_count += 1
                            elif self.es_video(msg_rel):
                                tipo = "video"
                                ext = self.obtener_extension(msg_rel, tipo)
                                rel_path = os.path.join(self.key, self.subfolder, "videos", f"video_{self.key}_{vid_count}.{ext}") if self.subfolder else os.path.join(self.key, "videos", f"video_{self.key}_{vid_count}.{ext}")
                                file_path = os.path.join("downloads", rel_path)
                                vid_count += 1
                            # if tipo:
                            #     try:
                            #         client.download_media(msg_rel, file=file_path)
                            #         print(f"Descargado: {file_path}")
                            #     except Exception as e:
                            #         print(f"Error al descargar {file_path}: {e}")
                            if tipo == "imagen":
                                # if not os.path.exists(os.path.dirname(file_path)):
                                #     os.makedirs(os.path.dirname(file_path))
                                # client.download_media(msg_rel, file=file_path)
                                # anime.image = file_path
                                # para no hacer nada
                                anime.image = f"https://mega.nz/embed/!fakeid!{msg_rel.id}"
                                print(f"Imagen relacionada: {file_path}")
                            else:
                                episode = Episode(
                                    title=f"{titulo_ficha} - Episodio {cap_rel}",
                                    number= int(cap_rel) if cap_rel else 0,
                                    link=VIEW_URL.format(msg_rel.id)  # puedes usar un link o dejarlo vacío si no tienes
                                )
                                
                                episode.add_source(Source(
                                    name="Local", 
                                    url=f"https://mega.nz/embed/!fakeid!{msg_rel.id}"
                                ))
                                anime.add_cap(episode)
                                anime_to_process += 1  # Aumentar el contador de animes procesados
                                archivos_subidos += 1  # Aumentar el contador de archivos subidos
                            
                    series.append(anime)
                    time.sleep(1)  # Espera 1 segundo antes de continuar
                    guardar_anime(anime, filename=f"anime_{self.key}_{anime.slug}.json")

            last_id = min(msg.id for msg in messages)
            if dias == -1:
                self.set_last_offset(last_id)
        return anime_to_process

    @staticmethod
    def limpiar_titulo(texto):
        # Quita asteriscos y espacios extra
        return re.sub(r'[\*\n]+', ' ', texto).strip().lower()

    @staticmethod
    def extraer_titulo_y_cap(ficha_texto):
        # Busca el título después de 'Título:'
        titulo_match = re.search(r'T[ií]tulo:\s*(.+)', ficha_texto, re.IGNORECASE)
        if titulo_match:
            titulo = HChannelHandle.limpiar_titulo(titulo_match.group(1))
        else:
            # Si no encuentra, usa la primera línea como fallback
            lineas = ficha_texto.split('\n')
            titulo = HChannelHandle.limpiar_titulo(lineas[0])

        # Busca el número de capítulos: acepta "Capitulos:", "Capítulos:", "Episodios:" y variantes con símbolos
        cap_match = re.search(r'(Cap[ií]tulos?|Episodios?):\s*(\d+)', ficha_texto, re.IGNORECASE)
        cap = cap_match.group(2) if cap_match else None
        
        # ahora buscamos los generos
        generos_match = re.search(r'G[eé]neros:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
        if generos_match:
            generos = [g.strip() for g in generos_match.group(1).split(',')]
        else:
            generos = []
            
        # ahora la sinopsis
        sinopsis_match = re.search(r'Sin[oó]psis:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
        if sinopsis_match:
            sinopsis = sinopsis_match.group(1).strip()
        else:
            sinopsis = "Sin sinopsis disponible."
            
        # ahora los subtitulos
        subtitulos_match = re.search(r'Subt[ií]tulos?:\s*([^\n]+)', ficha_texto, re.IGNORECASE)
        if subtitulos_match:
            subtitulos = [s.strip() for s in subtitulos_match.group(1).split(',')]
        else:
            subtitulos = ["Español"]
            
        return titulo, cap, generos, sinopsis, subtitulos
        
def guardar_anime(anime: Anime, filename="anime_h.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(anime.to_dict(), f, indent=2, ensure_ascii=False)