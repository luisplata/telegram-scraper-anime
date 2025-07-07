from Anime.HChannelHandle import HChannelHandle
from db_manager import AnimeDB
from config import SESSION_NAME, API_ID, API_HASH, MAX_CAPS
from telethon.sync import TelegramClient
import sys

def main():
    db = AnimeDB("animes.db")
    # Lee el parámetro de días desde la línea de comandos, por defecto -1
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else -1
    with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        entity = client.get_entity(HChannelHandle.channel_id)
        handle = HChannelHandle(entity)
        handle.process_messages(
            client,
            db,
            limit=50,
            max_anime_to_process=1,
            dias=dias
        )

if __name__ == "__main__":
    main()