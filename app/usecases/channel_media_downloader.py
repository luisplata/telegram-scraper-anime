import os
import json
import re
import logging
from typing import Optional, List
import app.logger_config  # ensure logging is configured

logger = logging.getLogger(__name__)

# Telethon types pueden no estar disponibles en tiempo de importación (tests locales).
try:
    from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, PeerChannel
except Exception:
    MessageMediaPhoto = object
    MessageMediaDocument = object
    PeerChannel = object


class ChannelMediaDownloader:
    """Clase que encapsula la lógica de descarga de `download_channel_media.py`.

    Esta versión no crea el cliente; espera recibir un cliente de Telethon ya conectado.
    """

    def __init__(self, client, channel_name: str, limit: int = 100, search: Optional[str] = None):
        self.client = client
        self.channel_name = channel_name
        self.limit = limit
        self.search = search
        logger.info("Inicializando ChannelMediaDownloader: channel=%s limit=%s search=%s", channel_name, limit, search)
        self.channel_id = self.get_channel_id_by_name(channel_name)
        self.subfolder = self.limpiar_texto(search) if search else None
        self.base_folder, self.images_folder, self.videos_folder, self.db_path = self.organizar_directorios(channel_name, self.subfolder)

    def limpiar_texto(self, texto: Optional[str]) -> str:
        if not texto:
            return ""
        # Permitir solo letras, números, guiones y guion bajo
        return re.sub('[^A-Za-z0-9_-]', '_', texto.strip())

    def organizar_directorios(self, channel_name: str, subfolder: Optional[str] = None):
        base_folder = os.path.join("downloads", channel_name)
        if subfolder:
            base_folder = os.path.join(base_folder, subfolder)
        images_folder = os.path.join(base_folder, "images")
        videos_folder = os.path.join(base_folder, "videos")
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(videos_folder, exist_ok=True)
        db_path = os.path.join(base_folder, f"db_{channel_name}.json")
        return base_folder, images_folder, videos_folder, db_path

    def es_imagen(self, message) -> bool:
        media = getattr(message, 'media', None)
        if media is None:
            return False
        try:
            if isinstance(media, MessageMediaPhoto):
                return True
        except Exception:
            pass
        # Fallback: si no tiene 'document', lo tratamos como foto
        return not hasattr(media, 'document')

    def es_video(self, message) -> bool:
        media = getattr(message, 'media', None)
        if media is None:
            return False
        try:
            if isinstance(media, MessageMediaDocument):
                if hasattr(media.document, 'mime_type') and media.document.mime_type:
                    return media.document.mime_type.startswith('video')
                for attr in getattr(media.document, 'attributes', []):
                    if hasattr(attr, 'file_name') and attr.file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                        return True
        except Exception:
            pass
        # Fallback: si tiene 'document' y hay mime_type o attributes, asumimos video
        if hasattr(media, 'document'):
            doc = getattr(media, 'document')
            if getattr(doc, 'mime_type', '').startswith('video'):
                return True
            for attr in getattr(doc, 'attributes', []):
                if hasattr(attr, 'file_name') and attr.file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                    return True
        return False

    def obtener_coleccion(self, entity, grouped_id) -> List:
        return list(self.client.iter_messages(entity, reverse=True, grouped=grouped_id))

    def obtener_extension(self, message, tipo: str) -> str:
        if tipo == "imagen":
            return "jpg"
        if tipo == "video":
            if hasattr(message.media.document, 'mime_type') and message.media.document.mime_type:
                mime = message.media.document.mime_type
                if mime == "video/mp4":
                    return "mp4"
                elif mime == "video/x-matroska":
                    return "mkv"
                elif mime == "video/x-msvideo":
                    return "avi"
                elif mime == "video/quicktime":
                    return "mov"
            for attr in message.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    ext = os.path.splitext(attr.file_name)[1].lstrip('.')
                    return ext or "mp4"
        return "dat"

    def get_channel_id_by_name(self, channel_name: str):
        try:
            channel_id_int = int(channel_name)
            for dialog in self.client.get_dialogs():
                if dialog.entity.id == channel_id_int:
                    return dialog.entity.id
        except ValueError:
            pass
        for dialog in self.client.get_dialogs():
            username = getattr(dialog.entity, 'username', None)
            if (
                (username and username.lower() == channel_name.lower()) or
                (dialog.name and dialog.name.lower() == channel_name.lower())
            ):
                logger.info("Canal encontrado: %s -> id=%s", channel_name, dialog.entity.id)
                return dialog.entity.id
        logger.error("No se encontró el canal con nombre, username o ID '%s'", channel_name)
        raise ValueError(f"No se encontró el canal con nombre, username o ID '{channel_name}'.")

    def buscar_mensajes(self):
        entity = self.client.get_entity(self.channel_id)
        if self.search:
            messages = self.client.iter_messages(entity, reverse=True, limit=self.limit, search=self.search)
        else:
            messages = self.client.iter_messages(entity, reverse=True, limit=self.limit)
        logger.info("Buscando mensajes en canal_id=%s limit=%s search=%s", self.channel_id, self.limit, self.search)
        return messages

    def descargar_medios(self):
        messages = list(self.buscar_mensajes())
        logger.info("Mensajes recuperados: %s", len(messages))
        media_db = []
        img_count = 1
        vid_count = 1
        procesados = set()
        entity = self.client.get_entity(self.channel_id)

        for msg in messages:
            if msg.id in procesados:
                logger.debug("Mensaje ya procesado: %s", msg.id)
                continue
            if not getattr(msg, 'media', None):
                logger.debug("Mensaje sin media: %s", msg.id)
                continue

            if getattr(msg, 'grouped_id', None):
                logger.info("Álbum detectado grouped_id=%s centrado en msg=%s", msg.grouped_id, msg.id)
                same_group_msgs = self.obtener_album_completo(msg.grouped_id, msg.id)
                for grouped_msg in same_group_msgs:
                    if grouped_msg.id in procesados:
                        continue
                    if not getattr(grouped_msg, 'media', None):
                        continue
                    img_count, vid_count = self._descargar_mensaje(grouped_msg, media_db, img_count, vid_count)
                    procesados.add(grouped_msg.id)
                continue

            img_count, vid_count = self._descargar_mensaje(msg, media_db, img_count, vid_count)
            procesados.add(msg.id)

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump({"media": media_db}, f, indent=2, ensure_ascii=False)
        logger.info("Descarga finalizada. DB guardada en %s, elementos=%s", self.db_path, len(media_db))
        return self.db_path

    def _descargar_mensaje(self, msg, media_db, img_count, vid_count):
        tipo = None
        file_path = None
        ext = None
        rel_path = None
        if self.es_imagen(msg):
            tipo = "imagen"
            ext = self.obtener_extension(msg, tipo)
            rel_path = os.path.join(self.channel_name, self.subfolder, "images", f"img_{self.channel_name}_{img_count}.{ext}") if self.subfolder else os.path.join(self.channel_name, "images", f"img_{self.channel_name}_{img_count}.{ext}")
            file_path = os.path.join("downloads", rel_path)
            img_count += 1
        elif self.es_video(msg):
            tipo = "video"
            ext = self.obtener_extension(msg, tipo)
            rel_path = os.path.join(self.channel_name, self.subfolder, "videos", f"video_{self.channel_name}_{vid_count}.{ext}") if self.subfolder else os.path.join(self.channel_name, "videos", f"video_{self.channel_name}_{vid_count}.{ext}")
            file_path = os.path.join("downloads", rel_path)
            vid_count += 1
        if tipo:
            logger.info("Descargando mensaje id=%s tipo=%s -> %s", msg.id, tipo, file_path)
            try:
                # Progress callback: show percentage during download
                last = {'p': -1}

                def _progress(current, total):
                    try:
                        if not total:
                            return
                        pct = int(current * 100 / total)
                        # report when percent increases or at 100%
                        if pct != last['p'] and (pct % 5 == 0 or pct == 100):
                            print(f"\rDescargando {os.path.basename(file_path)}: {pct}%", end="", flush=True)
                            last['p'] = pct
                    except Exception:
                        pass

                # Start a small watchdog thread that prints a heartbeat while no
                # progress events have occurred yet (useful during DC handoff).
                import threading, time

                done = threading.Event()

                def _watchdog():
                    start = time.time()
                    spinner = ['|', '/', '-', '\\']
                    i = 0
                    while not done.is_set():
                        elapsed = int(time.time() - start)
                        # only show heartbeat if no progress yet
                        if last['p'] <= 0:
                            text = f"Esperando inicio de descarga... {spinner[i%4]} {elapsed}s"
                            print(f"\r{text}", end="", flush=True)
                            try:
                                logger.debug(text)
                            except Exception:
                                pass
                        time.sleep(1)
                        i += 1
                    # clear line after done
                    try:
                        logger.info("Watchdog terminado para descarga: %s", os.path.basename(file_path))
                    except Exception:
                        pass
                    print('\r', end='', flush=True)

                watcher = threading.Thread(target=_watchdog, daemon=True)
                logger.info("Iniciando watchdog de heartbeat para %s", os.path.basename(file_path))
                watcher.start()

                # Telethon supports `progress_callback` in download_media; if not, fallback
                try:
                    self.client.download_media(msg, file=file_path, progress_callback=_progress)
                except TypeError:
                    # older Telethon versions may not accept progress_callback
                    self.client.download_media(msg, file=file_path)
                finally:
                    done.set()
                    watcher.join(timeout=0.1)
                    logger.info("Watchdog detenido para %s", os.path.basename(file_path))
                # ensure newline after progress printing
                if last['p'] != -1:
                    print()
                logger.info("Descargado mensaje id=%s -> %s", msg.id, file_path)
            except Exception:
                logger.exception("Error descargando mensaje id=%s", msg.id)
            media_db.append({
                "id": msg.id,
                "tipo": tipo,
                "fecha": str(msg.date),
                "caption": getattr(msg, 'text', '') or "",
                "procesado": False,
                "archivo": rel_path.replace("\\", "\\\\")
            })
        return img_count, vid_count

    def obtener_album_completo(self, grouped_id, mensaje_id_centro):
        entity = self.client.get_entity(PeerChannel(self.channel_id))
        mensajes_despues = list(self.client.iter_messages(entity, offset_id=mensaje_id_centro, reverse=True, limit=500))
        mensajes_antes = list(self.client.iter_messages(entity, offset_id=mensaje_id_centro, reverse=False, limit=500))
        todos = mensajes_antes + mensajes_despues
        return [m for m in todos if getattr(m, 'grouped_id', None) == grouped_id]
