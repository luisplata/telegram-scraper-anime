from Anime.ChannelHandle import ChannelHandle
from datetime import datetime, timedelta, timezone
import os
import re
import unicodedata
import time
import json

from Anime.model import Anime, Source
from Anime.tasks.validate_message_to_ficha import extraer_titulo_y_cap, get_all_caps, limpiar_nombre_archivo, limpiar_titulo, save_anime_to_json, validar_si_es_una_ficha_anime
from telegram_client import descargar_video_de_mensaje
from uploader import subir_video, eliminar_archivo
from utils import formatear_nombre_video
from sharer import compartir_anime, validate_if_anime_can_be_shared
from config import VIEW_URL
from telethon.sync import TelegramClient
from db_manager import AnimeDB
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import logging
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
                        name=[titulo],
                        slug=titulo_limpio.replace(" ", "-"),
                        description=sinopsis,
                        image=""
                        )
                    # print(f"Procesando ficha: {titulo} - {cap} episodios")
                    caps = get_all_caps(message, messages, titulo)
                    for cap in caps:
                        anime.add_cap(cap)
                        
                    # print tutulo y cantidad de caps
                    # print(f"Ficha procesada: {titulo} - {len(anime.caps)}")
                    anime_to_process += 1
            path, data = save_anime_to_json(anime)
            # print(f"Guardando anime: {titulo} en {path} con {data} episodios.")
            anime_list.append(anime)
        print(f"Total de fichas procesadas: {len(anime_list)}")
        for anime in anime_list:
            for cap in anime.caps:
                print(f"Procesando capítulo: {cap.title} - {cap.number} id: {cap.message_id}")
                    