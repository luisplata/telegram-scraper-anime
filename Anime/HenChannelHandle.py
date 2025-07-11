import requests
from Anime.ChannelHandle import ChannelHandle
import os

from Anime.model import Anime, Episode, Source
from Anime.tasks.validate_message_to_ficha import enviar_anime_completo, extraer_titulo_y_cap, get_all_caps, limpiar_nombre_archivo, limpiar_titulo, save_anime_to_json, validar_si_es_una_ficha_anime
from telegram_client import descargar_video_de_mensaje
from telethon.sync import TelegramClient
from db_manager import AnimeDB
from config import API_WEBHOOK_TOKEN, API_WEBHOOK_URL
import logging

from uploader import subir_video

logger = logging.getLogger(__name__)

class HenChannelHandle(ChannelHandle):
    key = "he_anime"
    channel_id = 2428772016

    def process_messages(
        self,
        client: TelegramClient,
        db: AnimeDB,
        limit: int = 50,
        max_anime_to_process: int = 1,
        dias: int = -1,
    ) -> int:
        archivos_subidos = 0
        MAX_SUBIDAS = 150
        anime_to_process = 0
        entity = client.get_entity(self.channel_id)
        last_id = 0
        anime_list : list[Anime] = []
        print(f"Iniciando procesamiento de mensajes en el canal {self.channel_id}...")
        while archivos_subidos < MAX_SUBIDAS and anime_to_process < max_anime_to_process:
            messages = list(client.iter_messages(entity, limit=limit, offset_id=last_id))
            for message in messages:
                if anime_to_process >= max_anime_to_process:
                    break
                texto = getattr(message, 'text', '') or ''
                print(f"Procesando mensaje: {message.id} - {texto[:50]}...")
                if validar_si_es_una_ficha_anime(texto):
                    titulo, cap, generos, sinopsis, subtitulos = extraer_titulo_y_cap(texto)
                    titulo_limpio = limpiar_nombre_archivo(limpiar_titulo(titulo))
                    anime = Anime(
                        name=titulo.split(" "),
                        slug=titulo_limpio.replace(" ", "-"),
                        description=sinopsis,
                        image=""
                        )
                    anime.genres = generos
                    # print(f"Procesando ficha: {titulo} - {cap} episodios")
                    caps = get_all_caps(message, messages, titulo, db)
                    for cap in caps:
                        anime.add_cap(cap)
                        
                    # print tutulo y cantidad de caps
                    # print(f"Ficha procesada: {titulo} - {len(anime.caps)}")
                    anime_to_process += 1
            path, data = save_anime_to_json(anime)
            # enviamos el json guardado al API
            if not path:
                print(f"Error al guardar el anime {titulo} en {path}")
                continue
            # anime_json = cargar_anime_json(path)
            print(f"Enviando anime {anime.name} a la API...")
            response = enviar_anime_completo(data, webhook="https://back.h.animebell.peryloth.com/api/webhook/send-anime-full", token="Animebell@1")
            if response.status_code == 200:
                print(f"Anime {anime.name} enviado correctamente a la API.")
                archivos_subidos += 1
            else:
                print(f"Error al enviar el anime {anime.name} a la API: {response.text}")
                continue
            # print(f"Guardando anime: {titulo} en {path} con {data} episodios.")
            anime_list.append(anime)
        print(f"Total de fichas procesadas: {len(anime_list)}")
        for anime in anime_list:
            for cap in anime.caps:
                print(f"🔍 Buscando mensaje para capítulo: {cap.title} - ID: {cap.message_id}")
                try:
                    msg = client.get_messages(entity, ids=cap.message_id)
                    if msg:
                        download, path =self.download_process(cap, anime, client, msg, db)
                        if not download:
                            return archivos_subidos
                        
                        upload,final_url = self.upload_process(cap=cap, anime=anime, db=db, webhook=API_WEBHOOK_URL, token=API_WEBHOOK_TOKEN)
                        source = Source(name="HenChannel", url=final_url)
                        cap.add_source(source)
                        print(f"✅ Capítulo {cap.title} procesado correctamente.")
                        # Compartir el anime si es posible
                        # self.share_anime(anime, cap, client, db)
                        if upload:
                            pass
                        else:
                            pass
                        
                except Exception as e:
                    print(f"❌ Error al buscar o descargar el mensaje {cap.message_id}: {e}")
        path, data = save_anime_to_json(anime)
        print(f"{data}")

                    
    def download_process(self, cap: Episode, anime: Anime, client: TelegramClient, msg, db: AnimeDB) -> tuple[bool, str]:
        """
        Descarga el capítulo desde el mensaje de Telegram y actualiza la base de datos.

        Retorna True si el capítulo ya fue descargado previamente o se descargó correctamente ahora.
        Retorna False si hubo un error o no se pudo descargar.
        """
        try:
            cap_data = db.buscar_anime(anime.slug.replace("-", " "), cap.number)
            file_path = os.path.join(HenChannelHandle.key, anime.slug, "videos", f"{anime.slug}_cap_{cap.number}")

            if cap_data and cap_data.get('descargado', False):
                print(f"✅ Capítulo {cap.number} ya descargado previamente.")
                cap.path = file_path
                return True, file_path

            print(f"📥 Descargando capítulo: {cap.title}")
            exito, file_path_file = descargar_video_de_mensaje(client, msg, file_path, cap.number)

            if not exito:
                print(f"❌ Falló la descarga del capítulo {cap.number}")
                return False, None

            cap.path = file_path_file
            print(f"✅ Capítulo descargado en: {file_path_file}")

            actualizado = db.actualizar_estado_anime(cap_data.get('anime'), cap_data.get('cap'), descargado=True)
            if actualizado:
                print(f"✅ Estado del capítulo {cap.number} actualizado en la base de datos.")

            return True, file_path_file

        except Exception as e:
            print(f"❌ Error inesperado durante la descarga del capítulo {cap.number}: {e}")
            return False, None
        
    def upload_process(self, file_path  ):
        subir_video()

    def share_process(self, cap: Episode, anime: Anime, db: AnimeDB, webhook, token, anime_data) -> tuple[bool, str]:
        """
        Sube un capítulo si no está subido, o retorna su URL si ya existe en la base de datos.

        Returns:
            (True, url) si se subió o ya estaba subido.
            (False, None) si ocurrió un error.
        """
        headers = {
            "X-Webhook-Token": token,
            "Content-Type": "application/json"
        }
        try:
            # print(anime_data)
            # print(headers)
            response = requests.post(webhook, json=anime_data, headers=headers)
            response.raise_for_status()
            print("✅ Webhook enviado con éxito.")
            db.actualizar_estado_anime(anime.slug, cap.number, subido=True)
            return True
        except Exception as e:
            print(f"Error al enviar webhook: {e}")
            return False