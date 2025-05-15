from telethon.sync import TelegramClient
from dotenv import load_dotenv
import os

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = "anon"

def listar_canales_y_ids():
    with TelegramClient(session_name, api_id, api_hash) as client:
        dialogs = client.get_dialogs()
        for dialog in dialogs:
            name = dialog.name
            entity_id = dialog.entity.id
            username = getattr(dialog.entity, 'username', None)
            print(f"Nombre: {name} | ID: {entity_id} | Username: {username}")




if __name__ == "__main__":
    listar_canales_y_ids()
