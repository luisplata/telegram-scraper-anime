"""Casos de uso para descargar medios desde Telegram.

Esta capa actúa como "use case" y usa un adaptador de Telethon para comunicarse
con Telegram. Intenta reutilizar la lógica existente en `download_channel_media.py`.
"""
import os
import logging
from typing import Optional
from config import DOWNLOAD_FOLDER
from app.adapters.telethon_adapter import TelethonAdapter
import app.logger_config  # ensure logging is configured

logger = logging.getLogger(__name__)

from app.usecases.channel_media_downloader import ChannelMediaDownloader


def download_all_media(channel_name: str, limit: int = 100):
    """Descarga los últimos `limit` mensajes con media del canal indicado."""
    logger.info("Usecase: download_all_media channel=%s limit=%s", channel_name, limit)
    with TelethonAdapter() as client:
        if ChannelMediaDownloader:
            downloader = ChannelMediaDownloader(client, channel_name, limit=limit)
            db = downloader.descargar_medios()
            logger.info("download_all_media finished, db=%s", db)
            return db
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
    logger.info("Usecase: download_by_search channel=%s search=%s limit=%s", channel_name, search, limit)
    with TelethonAdapter() as client:
        if ChannelMediaDownloader:
            downloader = ChannelMediaDownloader(client, channel_name, limit=limit, search=search)
            db = downloader.descargar_medios()
            logger.info("download_by_search finished, db=%s", db)
            return db
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
    logger.info("Usecase: download_by_message_id channel=%s message_id=%s out=%s", channel_name, message_id, out_folder)
    with TelethonAdapter() as client:
        entity = client.get_entity(channel_name)
        msg = client.get_messages(entity, ids=message_id)
        if not msg or not getattr(msg, 'media', None):
            logger.warning("No se encontró media para message_id=%s in channel=%s", message_id, channel_name)
            return None
        out_folder = out_folder or os.path.join(DOWNLOAD_FOLDER, str(channel_name))
        os.makedirs(out_folder, exist_ok=True)
        # Intentamos obtener un nombre razonable
        base_name = f"msg_{message_id}"
        file_path = os.path.join(out_folder, base_name)
        # Telethon infiere extensión si no se provea
        logger.info("Descargando media para message_id=%s -> %s", message_id, file_path)
        # progress callback similar to ChannelMediaDownloader
        last = {'p': -1}

        def _progress(current, total):
            try:
                if not total:
                    return
                pct = int(current * 100 / total)
                if pct != last['p'] and (pct % 5 == 0 or pct == 100):
                    print(f"\rDescargando {os.path.basename(file_path)}: {pct}%", end="", flush=True)
                    last['p'] = pct
            except Exception:
                pass

        # Start small watchdog to indicate activity during DC handoff
        import threading, time

        done = threading.Event()

        def _watchdog():
            start = time.time()
            spinner = ['|', '/', '-', '\\']
            i = 0
            while not done.is_set():
                elapsed = int(time.time() - start)
                if last['p'] <= 0:
                    text = f"Esperando inicio de descarga... {spinner[i%4]} {elapsed}s"
                    print(f"\r{text}", end="", flush=True)
                    try:
                        logger.debug(text)
                    except Exception:
                        pass
                time.sleep(1)
                i += 1
            try:
                logger.info("Watchdog terminado para descarga message_id=%s", message_id)
            except Exception:
                pass
            print('\r', end='', flush=True)

        watcher = threading.Thread(target=_watchdog, daemon=True)
        logger.info("Iniciando watchdog de heartbeat para message_id=%s", message_id)
        watcher.start()
        try:
            try:
                client.download_media(msg, file=file_path, progress_callback=_progress)
            except TypeError:
                client.download_media(msg, file=file_path)
        finally:
            done.set()
            watcher.join(timeout=0.1)
            logger.info("Watchdog detenido para message_id=%s", message_id)
        if last['p'] != -1:
            print()
        logger.info("Descarga finalizada para message_id=%s -> %s", message_id, file_path)
        # Si se descargó sin extensión, devolver la ruta tal cual
        # Para mantener compatibilidad con otros scripts, devolvemos la carpeta/base
        return file_path
