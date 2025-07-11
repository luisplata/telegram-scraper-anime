from Anime.ChannelHandle import ChannelHandle
from datetime import datetime, timedelta, timezone
import os

# Importa aquí las funciones y constantes necesarias
from telegram_client import descargar_video_de_mensaje
from uploader import subir_video, eliminar_archivo
from utils import formatear_nombre_video
from sharer import compartir_anime, validate_if_anime_can_be_shared
from config import VIEW_URL
from telethon.sync import TelegramClient
from db_manager import AnimeDB


class AnimeChannelHandle(ChannelHandle):
    key = "anime"
    channel_id = 1888892519  # Reemplaza por el ID real

    def parse_message(self, message):
        if message.text and "Episodio" in message.text:
            return f"Anime: {message.text}"
        return super().parse_message(message)

    @staticmethod
    def get_last_offset(db: AnimeDB) -> int:
        try:
            with open("last_offset.txt", "r") as f:
                return int(f.read())
        except Exception:
            return 0

    @staticmethod
    def set_last_offset(offset: int):
        with open("last_offset.txt", "w") as f:
            f.write(str(offset))

    def process_messages(
        self,
        client: TelegramClient,
        db: AnimeDB,
        limit: int = 50,
        max_anime_to_process: int = 1,
        dias: int = -1,
    ) -> int:
        """
        Procesa mensajes del canal anime.

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
        archivos_subidos = 0  # Nuevo contador
        MAX_SUBIDAS = 150
        entity = client.get_entity(self.channel_id)
        fecha_limite = None
        if dias != -1:
            fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)
            last_id = 0  # Siempre empieza desde el más reciente
        else:
            last_id = self.get_last_offset(db)  # Continúa desde donde quedó

        while archivos_subidos < MAX_SUBIDAS and anime_to_process < max_anime_to_process:
            batch_count = min(limit, max_anime_to_process - anime_to_process)
            messages = list(client.iter_messages(entity, limit=batch_count, offset_id=last_id))
            if not messages:
                break

            for message in messages:
                if archivos_subidos >= MAX_SUBIDAS or anime_to_process >= max_anime_to_process:
                    break

                if fecha_limite and message.date < fecha_limite:
                    print(f"Mensaje {message.id} fuera del rango de días ({dias} días). Deteniendo búsqueda.")
                    return anime_to_process

                if not message.media or not hasattr(message.media, "document"):
                    print("Mensaje sin media o sin documento. Saltando.")
                    continue

                texto = message.message if message.message else "video_sin_titulo"
                if not message.message:
                    print("Mensaje sin texto. Saltando.")
                    continue

                print(
                    f"\nProcesando mensaje: {texto[:60]}{'...' if len(texto) > 60 else ''}"
                )
                nombre_anime_limpio, cap_num, etiqueta_audio, nombre_anime = formatear_nombre_video(texto)

                # Validar que cap_num sea un número entero mayor que 0
                try:
                    cap_num_int = int(cap_num)
                    if cap_num_int <= 0:
                        print(f"Capítulo {cap_num} no válido. Saltando...")
                        continue
                except (ValueError, TypeError):
                    print(f"Capítulo '{cap_num}' no es un número válido. Saltando...")
                    continue

                nombre_archivo_base = f"{nombre_anime_limpio}_cap_{cap_num_int}_{etiqueta_audio}"
                print(
                    f"Nombre anime: {nombre_anime} | Capítulo: {cap_num_int} | Audio: {etiqueta_audio}"
                )

                anime_existente = db.buscar_anime(nombre_anime, int(cap_num), etiqueta_audio)
                if not anime_existente:
                    print(f"Anime/capítulo no encontrado en la base de datos. Agregando... {nombre_anime} {int(cap_num)} {etiqueta_audio}")
                    db.agregar_anime(nombre_anime, int(cap_num), "", etiqueta_audio)
                else:
                    print("Anime/capítulo encontrado en la base de datos.")
                    
                anime_existente = db.buscar_anime(nombre_anime, int(cap_num), etiqueta_audio)

                print("Validando si el anime puede ser compartido...")
                if not validate_if_anime_can_be_shared(nombre_anime):
                    print(f"❌ El anime '{nombre_anime}' no puede ser compartido. Saltando...")
                    continue

                start_time = datetime.now()
                print(
                    f"Hora inicio: '{start_time.strftime('%Y-%m-%d %H:%M:%S')}' para '{nombre_anime}' Capítulo {cap_num} {etiqueta_audio}"
                )
                anime_existente = db.buscar_anime(nombre_anime, int(cap_num), etiqueta_audio)
                print(anime_existente)
                # Descargar si no se ha descargado
                if not anime_existente.get("descargado", False):
                    print(f"Descargando video: {nombre_archivo_base}")
                    exito, archivo_path = descargar_video_de_mensaje(
                        client, message, nombre_archivo_base, int(cap_num)
                    )
                    if exito:
                        print("Descarga exitosa.")
                        db.actualizar_estado_anime(nombre_anime, int(cap_num), descargado=True)
                    else:
                        print("Fallo la descarga, saltando...")
                        continue
                else:
                    archivo_path = os.path.join("downloads", f"{nombre_archivo_base}.mp4")
                    print(f"El video ya estaba descargado: {archivo_path}")

                filecode = None
                # Subir si no se ha subido
                anime_existente = db.buscar_anime(nombre_anime, int(cap_num), etiqueta_audio)
                if not anime_existente.get("subido", False):
                    if os.path.exists(archivo_path):
                        print(f"Subiendo video: {archivo_path}")
                        title = f"{nombre_anime} Capítulo {cap_num} {etiqueta_audio}"
                        filecode = subir_video(archivo_path, title)
                        if filecode:
                            print("Subida exitosa.")
                            eliminar_archivo(archivo_path)
                            db.actualizar_estado_anime(
                                nombre_anime, int(cap_num), subido=True, link=f"{VIEW_URL}/{filecode}"
                            )
                            print("Archivo local eliminado tras la subida.")
                            archivos_subidos += 1  # <--- Incrementa aquí
                            if archivos_subidos >= MAX_SUBIDAS:
                                print("Se alcanzó el máximo de 200 archivos subidos en esta ejecución.")
                                return anime_to_process
                        else:
                            print("Fallo la subida, saltando...")
                            continue
                    else:
                        print(f"Archivo no encontrado para subir: {archivo_path}")
                        continue
                else:
                    print("El video ya estaba subido previamente.")
                    # Intenta obtener el filecode del link guardado
                    link = anime_existente.get("link", "")
                    if link and link.startswith(VIEW_URL):
                        filecode = link.replace(f"{VIEW_URL}/", "")
                        print(f"Usando filecode existente: {filecode}")
                    else:
                        print("No se encontró un filecode válido en la base de datos. Saltando compartir.")
                        continue

                # Compartir si no se ha compartido
                anime_existente = db.buscar_anime(nombre_anime, int(cap_num), etiqueta_audio)
                if not anime_existente.get("compartido", False):
                    if filecode:
                        print(f"Compartiendo anime {nombre_anime} Capítulo {cap_num} URL: {VIEW_URL}/{filecode}")
                        exito = compartir_anime(nombre_anime, cap_num, f"{VIEW_URL}/{filecode}", etiqueta_audio)
                        if exito:
                            print(f"Compartido exitosamente. Link: {VIEW_URL}/{filecode}")
                            db.actualizar_estado_anime(nombre_anime, int(cap_num), compartido=True)
                            anime_to_process += 1
                            print(f"Anime procesado: {nombre_anime} Capítulo {cap_num}")
                        else:
                            print("Fallo al compartir el anime.")
                    else:
                        print("No hay filecode disponible para compartir. Saltando...")
                else:
                    print("El anime ya había sido compartido previamente.")

            # Actualiza last_id para la siguiente tanda
            last_id = min(msg.id for msg in messages)

            # Si no hay límite de días, guarda el offset para la próxima ejecución
            if dias == -1:
                self.set_last_offset(last_id)

        return anime_to_process