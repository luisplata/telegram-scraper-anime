from telegram_client import obtener_mensajes_recientes, descargar_video_de_mensaje
from uploader import subir_video, eliminar_archivo
from utils import formatear_nombre_video, limpiar_nombre
from db_manager import agregar_anime, actualizar_estado_anime, buscar_anime
from config import VIEW_URL, SESSION_NAME, API_ID, API_HASH, MAX_CAPS
from telethon.sync import TelegramClient
from sharer import buscar_anime_en_api, compartir_anime
import os
from datetime import datetime
import csv

def guardar_log_ejecucion(nombre_anime, cap_num, inicio, fin, duracion):
    log_path = "historico_ejecuciones.log"
    existe = os.path.exists(log_path)
    with open(log_path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["anime", "capitulo", "hora_inicio", "hora_fin", "duracion"])
        writer.writerow([
            nombre_anime,
            cap_num,
            inicio.strftime("%Y-%m-%d %H:%M:%S"),
            fin.strftime("%Y-%m-%d %H:%M:%S"),
            str(duracion)
        ])

def main():
    max_anime_to_process = MAX_CAPS
    anime_to_process = 0
    offset_id = 0
    with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        while anime_to_process < max_anime_to_process: 
            start_time = datetime.now()
            print("Hora inicio:", start_time.strftime("%Y-%m-%d %H:%M:%S"))
            mensajes = obtener_mensajes_recientes(client, limit=50, offset_id=offset_id)
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

                nombre_anime_limpio, cap_num, etiqueta_audio, nombre_anime = formatear_nombre_video(texto)
                nombre_archivo_base = f"{nombre_anime_limpio}_cap_{cap_num}_{etiqueta_audio}"

                # Buscar en la DB
                anime_existente = buscar_anime(nombre_anime, int(cap_num))
                if not anime_existente:
                    agregar_anime(nombre_anime, int(cap_num), "", etiqueta_audio)
                    anime_existente = buscar_anime(nombre_anime, int(cap_num))

                # Descargar si no se ha descargado
                if not anime_existente or not anime_existente.get("descargado", False):
                    print(f"Descargando video: {nombre_archivo_base}")
                    exito, archivo_path = descargar_video_de_mensaje(client, message, nombre_archivo_base, int(cap_num))
                    if exito:
                        actualizar_estado_anime(nombre_anime, int(cap_num), descargado=True)
                    else:
                        print("Fallo la descarga, saltando...")
                        continue
                else:
                    archivo_path = os.path.join("downloads", f"{nombre_archivo_base}.mp4")
                
                filecode = None
                # Subir si no se ha subido
                if not anime_existente.get("subido", False):
                    if os.path.exists(archivo_path):
                        print(f"Subiendo video: {archivo_path}")
                        title = f"{nombre_anime} Capítulo {cap_num} {etiqueta_audio}"
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

                if not anime_existente.get("compartido", False):
                    exito = compartir_anime(nombre_anime, cap_num, f"{VIEW_URL}/{filecode}", etiqueta_audio)
                    if exito:
                        actualizar_estado_anime(nombre_anime, int(cap_num), compartido=True)
                        print(f"Anime procesado: {nombre_anime} Capítulo {cap_num} total: {anime_to_process}")
                
                anime_to_process += 1
                end_time = datetime.now()
                duracion = end_time - start_time
                print("Hora fin:", end_time.strftime("%Y-%m-%d %H:%M:%S"))
                print("Duración:", str(end_time - start_time))
                guardar_log_ejecucion(nombre_anime, cap_num, start_time, end_time, duracion)
                        
                if anime_to_process >= max_anime_to_process:
                    break
            offset_id = mensajes[-1].id
            print(f"Offset ID actualizado a: {offset_id}")
        
        print("\nProceso completo.")

if __name__ == "__main__":
    main()
