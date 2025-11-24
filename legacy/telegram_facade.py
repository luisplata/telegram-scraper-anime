from telethon.sync import TelegramClient
from Anime.AnimeChannelHandle import AnimeChannelHandle
from config import API_ID, API_HASH, SESSION_NAME

# Ejemplo de handle específico para un canal de anime
class TelegramChannelFacade:
    def __init__(self):
        self.channels = {}  # key: {id, handle}
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.client.start()

    def add_channel(self, handle_cls):
        entity = self.client.get_entity(handle_cls.channel_id)
        handle = handle_cls(entity)
        self.channels[handle_cls.key] = {
            "id": handle_cls.channel_id,
            "handle": handle
        }

    def get_messages(self, key, limit=50, offset_id=0):
        if key not in self.channels:
            raise ValueError(f"Canal '{key}' no registrado.")
        entity = self.channels[key]["handle"].entity
        return list(self.client.iter_messages(entity, limit=limit, offset_id=offset_id))

    def parse_messages(self, key, limit=10):
        messages = self.get_messages(key, limit=limit)
        handle = self.channels[key]["handle"]
        return [handle.parse_message(msg) for msg in messages]

    def list_channels(self):
        for key, info in self.channels.items():
            print(f"Key: {key} | ID: {info['id']} | Title: {info['handle'].entity.title}")

    def close(self):
        self.client.disconnect()

# Ejemplo de uso
if __name__ == "__main__":
    facade = TelegramChannelFacade()
    facade.add_channel(AnimeChannelHandle)
    facade.list_channels()
    print("Mensajes parseados del canal anime:")
    for parsed in facade.parse_messages("anime", limit=5):
        print(parsed)
    facade.close()
