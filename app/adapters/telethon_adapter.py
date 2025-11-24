from telethon.sync import TelegramClient
from contextlib import AbstractContextManager
from telethon import errors
from config import API_ID, API_HASH, SESSION_NAME, BOT_TOKEN


class TelethonAdapter(AbstractContextManager):
    """Context manager que expone un cliente de Telethon ya iniciado.

    Si `BOT_TOKEN` está presente en el entorno se intentará iniciar como bot
    (`client.start(bot_token=...)`). En caso contrario se inicia la sesión de
    usuario y Telethon podrá pedir el número de teléfono y el código.

    El adaptador captura errores comunes (ej. número de teléfono inválido)
    y los convierte en mensajes más claros para el usuario.
    """

    def __init__(self, session_name: str = SESSION_NAME, api_id: int = API_ID, api_hash: str = API_HASH):
        self._session = session_name
        self._api_id = api_id
        self._api_hash = api_hash
        self.client = None

    def __enter__(self):
        self.client = TelegramClient(self._session, self._api_id, self._api_hash)
        try:
            if BOT_TOKEN:
                # iniciar como bot evita pedir teléfono
                self.client.start(bot_token=BOT_TOKEN)
            else:
                # para cuentas de usuario Telethon pedirá teléfono/código si no hay sesión
                self.client.start()
        except errors.rpcerrorlist.PhoneNumberInvalidError:
            raise RuntimeError("El número de teléfono proporcionado es inválido. Usa formato internacional completo, por ejemplo: +34123456789.")
        except Exception:
            # Re-raise to allow caller to see original Telethon exceptions if needed
            raise
        return self.client

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.client:
                self.client.disconnect()
        finally:
            self.client = None
