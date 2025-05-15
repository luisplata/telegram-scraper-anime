import os
import requests
from config import API_KEY, API_URL

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

def eliminar_archivo(file_path):
    try:
        os.remove(file_path)
        print(f"Archivo local eliminado: {file_path}")
    except Exception as e:
        print(f"Error al eliminar archivo local: {e}")
