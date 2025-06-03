import os
import json
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from config import API_ID, API_HASH, SESSION_NAME

def es_imagen(message):
    return isinstance(message.media, MessageMediaPhoto)

def es_video(message):
    if isinstance(message.media, MessageMediaDocument):
        if hasattr(message.media.document, 'mime_type'):
            return message.media.document.mime_type.startswith('video')
        for attr in message.media.document.attributes:
            if hasattr(attr, 'file_name') and attr.file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                return True
    return False

def obtener_extension(message, tipo):
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

def organizar_directorios(channel_name):
    base_folder = os.path.join("downloads", channel_name)
    images_folder = os.path.join(base_folder, "images")
    videos_folder = os.path.join(base_folder, "videos")
    os.makedirs(images_folder, exist_ok=True)
    os.makedirs(videos_folder, exist_ok=True)
    db_path = os.path.join(base_folder, f"db_{channel_name}.json")
    return base_folder, images_folder, videos_folder, db_path

def download_channel_media(channel_id, client, channel_name, limit=100):
    entity = client.get_entity(channel_id)
    print(f"Descargando medios del canal: {entity.title} (ID: {entity.id})")
    # Usa el nombre del canal para carpetas y archivos
    base_folder, images_folder, videos_folder, db_path = organizar_directorios(channel_name)
    print(f"Obteniendo mensajes del canal (ID): {entity.id}")
    messages = client.iter_messages(entity, reverse=True, limit=limit)
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
        if es_imagen(msg):
            tipo = "imagen"
            ext = obtener_extension(msg, tipo)
            rel_path = os.path.join(channel_name, "images", f"img_{channel_name}_{img_count}.{ext}")
            file_path = os.path.join("downloads", rel_path)
            img_count += 1
        elif es_video(msg):
            tipo = "video"
            ext = obtener_extension(msg, tipo)
            rel_path = os.path.join(channel_name, "videos", f"video_{channel_name}_{vid_count}.{ext}")
            file_path = os.path.join("downloads", rel_path)
            vid_count += 1
        if tipo:
            try:
                client.download_media(msg, file=file_path)
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
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump({"media": media_db}, f, indent=2, ensure_ascii=False)
    print(f"Guardado en {db_path}")

def get_channel_id_by_name(client, channel_name):
    """
    Busca el canal por nombre visible o username entre los canales del usuario y retorna su ID.
    """
    for dialog in client.get_dialogs():
        # Busca por username (sin @) o por nombre visible
        username = getattr(dialog.entity, 'username', None)
        if (
            (username and username.lower() == channel_name.lower()) or
            (dialog.name.lower() == channel_name.lower())
        ):
            print(f"Canal encontrado: {dialog.name} (ID: {dialog.entity.id})")
            return dialog.entity.id
    print(f"No se encontró el canal con nombre o username '{channel_name}'.")
    exit(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python download_channel_media.py <nombre_canal> [limite]")
        print("Ejemplo: python download_channel_media.py Miagreyxox 50")
    else:
        channel_name = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
            channel_id = get_channel_id_by_name(client, channel_name)
            download_channel_media(channel_id, client=client, channel_name=channel_name, limit=limit)