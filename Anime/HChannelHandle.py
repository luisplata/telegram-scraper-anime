from Anime.ChannelHandle import ChannelHandle
from datetime import datetime, timedelta, timezone
import os
import time

from telegram_client import descargar_video_de_mensaje
from uploader import subir_video, eliminar_archivo
from utils import formatear_nombre_video
from sharer import compartir_anime, validate_if_anime_can_be_shared
from config import VIEW_URL
from telethon.sync import TelegramClient
from db_manager import AnimeDB

class HChannelHandle(ChannelHandle):
    key = "h_anime"
    channel_id = 2428772016  # Reemplaza por el ID real del canal H

    def parse_message(self, message):
        # Personaliza la lógica de parseo para este canal
        if message.text and "H-Episodio" in message.text:
            return f"H-Anime: {message.text}"
        return super().parse_message(message)

    @staticmethod
    def get_last_offset(db: AnimeDB) -> int:
        try:
            with open("last_offset_h.txt", "r") as f:
                return int(f.read())
        except Exception:
            return 0

    @staticmethod
    def set_last_offset(offset: int):
        with open("last_offset_h.txt", "w") as f:
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
        Procesa mensajes del canal H-Anime.

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
        archivos_subidos = 0
        MAX_SUBIDAS = 150
        entity = client.get_entity(self.channel_id)
        fecha_limite = None
        if dias != -1:
            fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)
            last_id = 0
        else:
            last_id = self.get_last_offset(db)

        while archivos_subidos < MAX_SUBIDAS and anime_to_process < max_anime_to_process:
            batch_count = min(limit, max_anime_to_process - anime_to_process)
            messages = list(client.iter_messages(entity, limit=batch_count, offset_id=last_id))
            if not messages:
                break

            for message in messages:
                if archivos_subidos >= MAX_SUBIDAS or anime_to_process >= max_anime_to_process:
                    break

                print(f"Mensaje ID {message.id}: {getattr(message, 'text', '')}")

                # Verifica el tipo de adjunto
                if message.photo:
                    print("→ El mensaje tiene una FOTO.")
                elif message.video:
                    print("→ El mensaje tiene un VIDEO.")
                elif getattr(message, 'media', None) and getattr(message.media, 'document', None):
                    print("→ El mensaje tiene un DOCUMENTO (puede ser video, archivo, etc).")
                elif getattr(message, 'media', None) and getattr(message.media, 'webpage', None):
                    print("→ El mensaje tiene un ENLACE WEB.")
                elif getattr(message, 'media', None) and getattr(message.media, 'grouped_id', None):
                    print("→ El mensaje es parte de una COLECCIÓN/ÁLBUM.")
                else:
                    print("→ El mensaje NO tiene adjunto.")

                time.sleep(1)  # Espera 1 segundo antes de continuar

            last_id = min(msg.id for msg in messages)
            if dias == -1:
                self.set_last_offset(last_id)

        return anime_to_process