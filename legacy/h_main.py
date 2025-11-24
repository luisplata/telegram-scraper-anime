from Anime.HenChannelHandle import HenChannelHandle
from Anime.HChannelHandle import HChannelHandle
from db_manager import AnimeDB
from config import SESSION_NAME, API_ID, API_HASH, MAX_CAPS
from telethon.sync import TelegramClient
import sys
import logging
logger = logging.getLogger(__name__)

def main():
    db = AnimeDB(f"{HChannelHandle.key}.db")
    # Lee el parámetro de días desde la línea de comandos, por defecto -1
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else -1
    with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        entity = client.get_entity(HenChannelHandle.channel_id)
        handle = HenChannelHandle(entity)
        print(f"Procesando mensajes del canal {HenChannelHandle.channel_id}...")
        handle.process_messages(
            client,
            db,
            limit=100,
            max_anime_to_process=1,
            dias=dias
        )

if __name__ == "__main__":
    main()
