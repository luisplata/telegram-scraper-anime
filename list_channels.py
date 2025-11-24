"""Entrypoint: listar canales/dialogs accesibles por la cuenta.

Uso:
  python list_channels.py [limite]

Imprime una lista simple con `id | title | username | is_channel`.
"""
import sys
from app.adapters.telethon_adapter import TelethonAdapter


def main(argv):
    limit = None
    if len(argv) >= 1:
        try:
            limit = int(argv[0])
        except ValueError:
            print("limite debe ser un número")
            return

    with TelethonAdapter() as client:
        # Telethon permite iterar dialogs; usamos iter_dialogs para no cargar todo en memoria
        it = client.iter_dialogs(limit=limit)
        print("id | title | username | is_channel")
        for dialog in it:
            entity = dialog.entity
            title = getattr(dialog, 'title', None) or getattr(entity, 'title', None) or getattr(entity, 'first_name', '')
            username = getattr(entity, 'username', None)
            is_channel = getattr(entity, 'broadcast', False) or getattr(entity, 'megagroup', False) or getattr(entity, 'channel', False)
            print(f"{getattr(entity, 'id', 'N/A')} | {title} | {username} | {is_channel}")


if __name__ == '__main__':
    main(sys.argv[1:])
