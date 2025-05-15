import os
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from config import API_ID, API_HASH, SESSION_NAME, DOWNLOAD_FOLDER, CHANNEL_ID
from utils import limpiar_nombre, formatear_nombre_video

def obtener_canal_por_id(client, canal_id):
    for dialog in client.get_dialogs():
        if dialog.entity.id == canal_id:
            return dialog.entity
    raise ValueError(f"No se encontró el canal con ID '{canal_id}'")

def listar_canales(client):
    print("Lista de canales disponibles:")
    for dialog in client.get_dialogs():
        entity = dialog.entity
        print(f"Nombre: {dialog.name} | ID: {entity.id} | Username: {getattr(entity, 'username', None)}")

def descargar_videos():
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    videos_descargados = 0

    with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        listar_canales(client)
        channel = obtener_canal_por_id(client, CHANNEL_ID)
        
        messages = client(GetHistoryRequest(
            peer=channel,
            limit=50,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        print(f"Iniciando descarga de videos del canal: {channel.title}")

        for message in messages.messages:
            if message.media and hasattr(message.media, 'document'):
                for attr in message.media.document.attributes:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                        if file_name.endswith('.mp4'):
                            texto = message.message if message.message else "video_sin_titulo"
                            nombre_anime, cap_num = formatear_nombre_video(texto)
                            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                            nombre_final = f"{timestamp}_{nombre_anime}_cap_{cap_num}.mp4"
                            file_path = os.path.join(DOWNLOAD_FOLDER, nombre_final)

                            contador = 1
                            base_name = f"{nombre_anime}_cap_{cap_num}"
                            while os.path.exists(file_path):
                                nombre_final = f"{base_name}_{contador}.mp4"
                                file_path = os.path.join(DOWNLOAD_FOLDER, nombre_final)
                                contador += 1

                            print(f"\nMensaje: {texto}")
                            print(f"Guardando video como: {nombre_final}")
                            client.download_media(message.media, file=file_path)
                            print(f"Guardado en: {file_path}")

                            videos_descargados += 1

    print(f"\nDescarga finalizada. Total de videos descargados: {videos_descargados}")
    return videos_descargados, DOWNLOAD_FOLDER


def obtener_mensajes_recientes(limit=50):
    with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        canal = obtener_canal_por_id(client, 1888892519)
        history = client(GetHistoryRequest(
            peer=canal,
            limit=limit,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        return history.messages



def descargar_video_de_mensaje(message, nombre_archivo_base, cap_num):
    filename = f"{nombre_archivo_base}.mp4"
    folder = "downloads"
    filepath = os.path.join(folder, filename)

    try:
        os.makedirs(folder, exist_ok=True)
        message.download_media(file=filepath)
        return True, filepath
    except Exception as e:
        print(f"Error al descargar: {e}")
        return False, None
