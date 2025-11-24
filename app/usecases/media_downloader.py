"""Casos de uso para descargar medios desde Telegram.

Esta capa actúa como "use case" y usa un adaptador de Telethon para comunicarse
con Telegram. Intenta reutilizar la lógica existente en `download_channel_media.py`.
"""
import os
from typing import Optional
from config import DOWNLOAD_FOLDER
from app.adapters.telethon_adapter import TelethonAdapter

from app.usecases.channel_media_downloader import ChannelMediaDownloader


def download_all_media(channel_name: str, limit: int = 100):
    """Descarga los últimos `limit` mensajes con media del canal indicado."""
    with TelethonAdapter() as client:
        if ChannelMediaDownloader:
            downloader = ChannelMediaDownloader(client, channel_name, limit=limit)
            downloader.descargar_medios()
            return downloader.db_path
        # Fallback mínimo: descargar mensajes con media manualmente
        entity = client.get_entity(channel_name)
        messages = client.iter_messages(entity, reverse=True, limit=limit)
        base = os.path.join(DOWNLOAD_FOLDER, channel_name)
        os.makedirs(base, exist_ok=True)
        for msg in messages:
            if getattr(msg, 'media', None):
                fname = f"msg_{msg.id}.dat"
                path = os.path.join(base, fname)
                client.download_media(msg, file=path)
        return base


def download_by_search(channel_name: str, search: str, limit: int = 100):
    """Descarga mensajes que coincidan con `search` (texto) en el canal."""
    with TelethonAdapter() as client:
        if ChannelMediaDownloader:
            downloader = ChannelMediaDownloader(client, channel_name, limit=limit, search=search)
            downloader.descargar_medios()
            return downloader.db_path
        entity = client.get_entity(channel_name)
        messages = client.iter_messages(entity, reverse=True, limit=limit, search=search)
        base = os.path.join(DOWNLOAD_FOLDER, channel_name, search)
        os.makedirs(base, exist_ok=True)
        for msg in messages:
            if getattr(msg, 'media', None):
                fname = f"msg_{msg.id}.dat"
                path = os.path.join(base, fname)
                client.download_media(msg, file=path)
        return base


def download_by_message_id(channel_name: str, message_id: int, out_folder: Optional[str] = None):
    """Descarga la media correspondiente a un `message_id` de un canal.

    Retorna la ruta del archivo descargado o None.
    """
    with TelethonAdapter() as client:
        entity = client.get_entity(channel_name)
        msg = client.get_messages(entity, ids=message_id)
        if not msg or not getattr(msg, 'media', None):
            return None
        out_folder = out_folder or os.path.join(DOWNLOAD_FOLDER, str(channel_name))
        os.makedirs(out_folder, exist_ok=True)
        # Intentamos obtener un nombre razonable
        base_name = f"msg_{message_id}"
        file_path = os.path.join(out_folder, base_name)
        # Telethon infiere extensión si no se provee
        client.download_media(msg, file=file_path)
        # Si se descargó sin extensión, devolver la ruta tal cual
        # Para mantener compatibilidad con otros scripts, devolvemos la carpeta/base
        return file_path
