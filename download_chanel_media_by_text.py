"""Entrypoint mínimo para búsqueda por texto que reutiliza la capa de usecases."""
import sys
from app.usecases.media_downloader import download_by_search


def main(argv):
    if len(argv) < 2:
        print("Uso: python download_chanel_media_by_text.py <nombre_canal> [limite] <texto_busqueda>")
        return
    channel_name = argv[0]
    try:
        limit = int(argv[1])
        search = argv[2]
    except (ValueError, IndexError):
        # si se pasa: <canal> "texto"
        limit = 100
        search = argv[1]

    result = download_by_search(channel_name, search, limit=limit)
    print(f"Resultado: {result}")


if __name__ == '__main__':
    main(sys.argv[1:])