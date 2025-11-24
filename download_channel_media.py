"""Entrypoint mínimo que delega la lógica en la capa de usecases."""
import sys
from app.usecases.media_downloader import download_all_media, download_by_search


def main(argv):
    if len(argv) < 1:
        print("Uso: python download_channel_media.py <nombre_canal> [limite] [texto_busqueda]")
        return
    channel_name = argv[0]
    limit = int(argv[1]) if len(argv) > 1 else 100
    search = argv[2] if len(argv) > 2 else None
    if search:
        result = download_by_search(channel_name, search, limit=limit)
    else:
        result = download_all_media(channel_name, limit=limit)
    print(f"Resultado: {result}")


if __name__ == '__main__':
    main(sys.argv[1:])