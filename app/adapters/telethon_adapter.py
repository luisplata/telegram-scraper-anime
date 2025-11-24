from telethon.sync import TelegramClient
from contextlib import AbstractContextManager
from telethon import errors
from config import API_ID, API_HASH, SESSION_NAME, BOT_TOKEN
import logging
import app.logger_config  # ensure logging is configured for CLI runs

logger = logging.getLogger(__name__)


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
                logger.info("Iniciando Telethon en modo BOT")
                # iniciar como bot evita pedir teléfono
                self.client.start(bot_token=BOT_TOKEN)
            else:
                logger.info("Iniciando Telethon en modo usuario (se puede pedir teléfono/código)")
                # para cuentas de usuario Telethon pedirá teléfono/código si no hay sesión
                self.client.start()
            logger.info("Telethon iniciado correctamente")
        except errors.rpcerrorlist.PhoneNumberInvalidError as e:
            logger.exception("Número de teléfono inválido")
            raise RuntimeError("El número de teléfono proporcionado es inválido. Usa formato internacional completo, por ejemplo: +34123456789.") from e
        except Exception:
            logger.exception("Error iniciando Telethon")
            # Re-raise to allow caller to see original Telethon exceptions if needed
            raise
        return self.client

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.client:
                logger.info("Desconectando Telethon")
                self.client.disconnect()
                logger.info("Telethon desconectado")
        finally:
            self.client = None
