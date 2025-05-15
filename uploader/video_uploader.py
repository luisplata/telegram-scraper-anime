import requests

def subir_video(file_path):
    url = "https://tu-servicio-streaming.com/api/upload"
    with open(file_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()  # para lanzar error si status no es 2xx
            data = response.json()
            video_url = data.get('url')
            if video_url:
                print(f"Video subido correctamente: {video_url}")
                return video_url
            else:
                print("No se encontró el link en la respuesta.")
        except Exception as e:
            print(f"Error subiendo video: {e}")
    return None
