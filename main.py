from telegram_client import obtener_mensajes_recientes, descargar_video_de_mensaje
from uploader import subir_video, eliminar_archivo
from utils import formatear_nombre_video, limpiar_nombre
from db_manager import agregar_anime, actualizar_estado_anime, buscar_anime
from config import VIEW_URL
import os

def main():
    mensajes = obtener_mensajes_recientes(limit=50)
    if not mensajes:
        print("No se encontraron mensajes para procesar.")
        return

    for message in mensajes:
        if not message.media or not hasattr(message.media, 'document'):
            continue

        texto = message.message if message.message else "video_sin_titulo"
        if not message.message:
                print("Mensaje sin texto. Saltando.")
                continue
        nombre_anime, cap_num = formatear_nombre_video(texto)
        nombre_anime_limpio = limpiar_nombre(nombre_anime)
        nombre_archivo_base = f"{nombre_anime_limpio}_cap_{cap_num}"


        # Buscar en la DB
        anime_existente = buscar_anime(nombre_anime, int(cap_num))
        if not anime_existente:
            agregar_anime(nombre_anime, int(cap_num), "")
            anime_existente = buscar_anime(nombre_anime, int(cap_num))

        # Crear entrada inicial si no existe
        if not anime_existente:
            agregar_anime(nombre_anime, int(cap_num), "")

        # Descargar si no se ha descargado
        if not anime_existente or not anime_existente.get("descargado", False):
            print(f"Descargando video: {nombre_archivo_base}")
            exito, archivo_path = descargar_video_de_mensaje(message, nombre_archivo_base, int(cap_num))
            if exito:
                actualizar_estado_anime(nombre_anime, int(cap_num), descargado=True)
            else:
                print("Fallo la descarga, saltando...")
                continue

        # Subir si no se ha subido
        if not anime_existente.get("subido", False):
            if os.path.exists(archivo_path):
                print(f"Subiendo video: {archivo_path}")
                title = f"{nombre_anime} Capítulo {cap_num}"
                filecode = subir_video(archivo_path, title)
                if filecode:
                    actualizar_estado_anime(nombre_anime, int(cap_num), subido=True, link=f"{VIEW_URL}/{filecode}")
                    eliminar_archivo(archivo_path)
                else:
                    print("Fallo la subida, saltando...")
                    continue
            else:
                print(f"Archivo no encontrado: {archivo_path}")
                continue

        # Compartir (en un futuro)
        if not anime_existente or not anime_existente.get("compartido", False):
            # Simulación de compartir
            print(f"Compartiendo: {nombre_anime} Capítulo {cap_num}")
            actualizar_estado_anime(nombre_anime, int(cap_num), compartido=True)

    print("\nProceso completo.")

if __name__ == "__main__":
    main()
