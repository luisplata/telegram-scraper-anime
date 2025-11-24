from telethon.sync import TelegramClient
from contextlib import AbstractContextManager
from config import API_ID, API_HASH, SESSION_NAME


class TelethonAdapter(AbstractContextManager):
    """Context manager simple que expone un cliente de Telethon ya iniciado.

    Uso:
        with TelethonAdapter() as client:
            # usar client (instancia de TelegramClient)
    """

    def __init__(self, session_name: str = SESSION_NAME, api_id: int = API_ID, api_hash: str = API_HASH):
        self._session = session_name
        self._api_id = api_id
        self._api_hash = api_hash
        self.client = None

    def __enter__(self):
        self.client = TelegramClient(self._session, self._api_id, self._api_hash)
        # Telethon client soporta .start() o usarse como context manager
        self.client.start()
        return self.client

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.client:
                self.client.disconnect()
        finally:
            self.client = None
