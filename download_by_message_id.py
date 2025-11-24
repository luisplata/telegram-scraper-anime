"""Entry point: descargar la media de un mensaje por su ID en un canal.

Uso:
  python download_by_message_id.py <canal|username|id> <message_id> [out_folder]
"""
import sys
from app.usecases.media_downloader import download_by_message_id


def main(argv):
    if len(argv) < 2:
        print("Uso: python download_by_message_id.py <canal> <message_id> [out_folder]")
        return
    channel = argv[0]
    try:
        message_id = int(argv[1])
    except ValueError:
        print("message_id debe ser un número")
        return
    out = argv[2] if len(argv) > 2 else None
    result = download_by_message_id(channel, message_id, out_folder=out)
    print(f"Resultado: {result}")


if __name__ == '__main__':
    main(sys.argv[1:])
