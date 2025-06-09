import os
import json
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from config import API_ID, API_HASH, SESSION_NAME
import re

class ChannelMediaDownloader:
    def __init__(self, client, channel_name, limit=100, search=None):
        self.client = client
        self.channel_name = channel_name
        self.limit = limit
        self.search = search
        self.channel_id = self.get_channel_id_by_name(channel_name)
        self.subfolder = self.limpiar_texto(search) if search else None
        self.base_folder, self.images_folder, self.videos_folder, self.db_path = self.organizar_directorios(channel_name, self.subfolder)
    
    def limpiar_texto(self, texto):
        if not texto:
            return ""
        # Solo letras, números, guiones y guion bajo
        return re.sub(r'[^\w\-]', '_', texto.strip())

    def organizar_directorios(self, channel_name, subfolder=None):
        base_folder = os.path.join("downloads", channel_name)
        if subfolder:
            base_folder = os.path.join(base_folder, subfolder)
        images_folder = os.path.join(base_folder, "images")
        videos_folder = os.path.join(base_folder, "videos")
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(videos_folder, exist_ok=True)
        db_path = os.path.join(base_folder, f"db_{channel_name}.json")
        return base_folder, images_folder, videos_folder, db_path

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
            for attr in message.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    ext = os.path.splitext(attr.file_name)[1].lstrip('.')
                    return ext or "mp4"
        return "dat"

    def get_channel_id_by_name(self, channel_name):
        # Si es un número, intenta buscar por ID directamente
        try:
            channel_id_int = int(channel_name)
            for dialog in self.client.get_dialogs():
                if dialog.entity.id == channel_id_int:
                    print(f"Canal encontrado por ID: {dialog.name} (ID: {dialog.entity.id})")
                    return dialog.entity.id
        except ValueError:
            pass  # No es un número, sigue buscando por nombre/username

        for dialog in self.client.get_dialogs():
            username = getattr(dialog.entity, 'username', None)
            if (
                (username and username.lower() == channel_name.lower()) or
                (dialog.name.lower() == channel_name.lower())
            ):
                print(f"Canal encontrado: {dialog.name} (ID: {dialog.entity.id})")
                return dialog.entity.id
        print(f"No se encontró el canal con nombre, username o ID '{channel_name}'.")
        exit(1)

    def buscar_mensajes(self):
        entity = self.client.get_entity(self.channel_id)
        print(f"Buscando mensajes en el canal: {entity.title} (ID: {entity.id})")
        # Si hay búsqueda, filtra por texto
        if self.search:
            messages = self.client.iter_messages(entity, reverse=True, limit=self.limit, search=self.search)
        else:
            messages = self.client.iter_messages(entity, reverse=True, limit=self.limit)
        return messages

    def descargar_medios(self):
        messages = self.buscar_mensajes()
        media_db = []
        img_count = 1
        vid_count = 1
        for msg in messages:
            if not msg.media:
                continue
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
                try:
                    self.client.download_media(msg, file=file_path)
                    print(f"Descargado: {file_path}")
                except Exception as e:
                    print(f"Error al descargar {file_path}: {e}")
                media_db.append({
                    "id": msg.id,
                    "tipo": tipo,
                    "fecha": str(msg.date),
                    "caption": msg.text or "",
                    "procesado": False,
                    "archivo": rel_path.replace("\\", "\\\\")
                })
        print(f"Total de archivos multimedia encontrados: {len(media_db)}")
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump({"media": media_db}, f, indent=2, ensure_ascii=False)
        print(f"Guardado en {self.db_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python download_channel_media_by_text.py <nombre_canal> [limite] [texto_busqueda]")
        print("Ejemplo: python download_channel_media_by_text.py Miagreyxox 50 \"palabra\"")
    else:
        channel_name = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        search = sys.argv[3] if len(sys.argv) > 3 else None
        with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
            downloader = ChannelMediaDownloader(client, channel_name, limit=limit, search=search)
            downloader.descargar_medios()