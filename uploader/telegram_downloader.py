import os
import re
import requests
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")

session_name = "anon"
download_folder = "downloads"

def limpiar_nombre(texto, max_length=50):
    texto = re.sub(r'[\\/*?:"<>|]', '_', texto)  # reemplaza caracteres inválidos
    texto = texto.strip()
    texto = texto.replace(' ', '_')  # reemplaza espacios por guiones bajos
    if len(texto) > max_length:
        texto = texto[:max_length].rstrip()
    return texto

def formatear_nombre_video(texto_mensaje):
    partes = texto_mensaje.split("»")
    if len(partes) < 2:
        nombre_anime = limpiar_nombre(texto_mensaje.strip())
        return nombre_anime, "00"
    
    nombre_anime = partes[0].strip()
    resto = partes[1].strip()
    
    match = re.search(r"(Episodio|Capítulo)\s*(\d+)", resto, re.IGNORECASE)
    if match:
        numero_cap = match.group(2).zfill(2)
    else:
        numero_cap = "00"
    
    nombre_anime_limpio = limpiar_nombre(nombre_anime)
    return nombre_anime_limpio, numero_cap


def extraer_nombre_capitulo(texto):
    match = re.search(r'(.*?)\s*Capítulo\s*(\d+)', texto, re.IGNORECASE | re.DOTALL)
    if match:
        nombre_anime = match.group(1).strip()
        cap_num = match.group(2).zfill(2)
        return nombre_anime, cap_num
    else:
        return texto.strip(), "00"

def obtener_canal_por_id(client, canal_id):
    for dialog in client.get_dialogs():
        if dialog.entity.id == canal_id:
            return dialog.entity
    raise ValueError(f"No se encontró el canal con ID '{canal_id}'")

def obtener_canal_por_nombre(client, nombre):
    for dialog in client.get_dialogs():
        if dialog.name.strip() == nombre.strip():
            return dialog.entity
    raise ValueError(f"No se encontró el canal '{nombre}'")

def obtener_upload_server():
    url = f"{API_URL}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == 200 and data.get("msg") == "OK":
            upload_url = data.get("result")
            print(f"Upload server disponible: {upload_url}")
            return upload_url
        else:
            print(f"Servicio no disponible: {data}")
    except Exception as e:
        print(f"Error consultando upload server: {e}")
    return None

def subir_video(file_path, title="", description=""):
    upload_url = obtener_upload_server()
    if not upload_url:
        print("No se pudo obtener el upload server, archivo no será borrado.")
        return None

    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'key': API_KEY,
            'file_title': title,
            'file_descr': description,
        }
        try:
            response = requests.post(upload_url, files=files, data=data)
            response.raise_for_status()
            result = response.json()
            if result.get("status") == 200 and result.get("msg") == "OK":
                archivos = result.get("files", [])
                if archivos:
                    file_info = archivos[0]
                    print(f"Archivo subido: {file_info.get('filename')} con código {file_info.get('filecode')}")
                    return file_info.get("filecode")
                else:
                    print("No se devolvieron archivos en la respuesta.")
            else:
                print(f"Error en la respuesta de subida: {result}")
        except Exception as e:
            print(f"Error subiendo archivo: {e}")

    return None

def descargar_y_subir_videos():
    os.makedirs(download_folder, exist_ok=True)

    with TelegramClient(session_name, api_id, api_hash) as client:
        channel = obtener_canal_por_id(client, 1888892519)

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
        videos_descargados = 0

        for message in messages.messages:
            if message.media and hasattr(message.media, 'document'):
                for attr in message.media.document.attributes:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                        if file_name.endswith('.mp4'):
                            texto = message.message if message.message else "video_sin_titulo"
                            nombre_anime, cap_num = formatear_nombre_video(texto)
                            # nombre_anime, cap_num = extraer_nombre_capitulo(texto)
                            nombre_anime_limpio = limpiar_nombre(nombre_anime)
                            nombre_final = f"{nombre_anime_limpio}_cap_{cap_num}.mp4"
                            file_path = os.path.join(download_folder, nombre_final)

                            contador = 1
                            base_name = f"{nombre_anime_limpio}_cap_{cap_num}"
                            while os.path.exists(file_path):
                                nombre_final = f"{base_name}_{contador}.mp4"
                                file_path = os.path.join(download_folder, nombre_final)
                                contador += 1

                            print(f"\nMensaje: {texto}")
                            print(f"Guardando video como: {nombre_final}")
                            client.download_media(message.media, file=file_path)
                            print(f"Guardado en: {file_path}")

                            # Subir video
                            title = f"{nombre_anime} Capítulo {cap_num}"
                            filecode = subir_video(file_path, title)
                            if filecode:
                                try:
                                    os.remove(file_path)
                                    print(f"Archivo local eliminado: {file_path}")
                                except Exception as e:
                                    print(f"Error al eliminar archivo local: {e}")
                            else:
                                print("Archivo no eliminado por fallo en subida.")

                            videos_descargados += 1

        print(f"\nDescarga y subida finalizada. Total de videos procesados: {videos_descargados}")

if __name__ == "__main__":
    descargar_y_subir_videos()
