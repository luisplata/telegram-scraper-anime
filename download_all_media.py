"""Entry point: descargar toda la media de un canal (imágenes y videos).

Uso:
  python download_all_media.py <canal|username|id> [limite]
"""
import sys
from app.usecases.media_downloader import download_all_media


def main(argv):
    if len(argv) < 1:
        print("Uso: python download_all_media.py <canal> [limite]")
        return
    channel = argv[0]
    limit = int(argv[1]) if len(argv) > 1 else 100
    result = download_all_media(channel, limit=limit)
    print(f"Resultado: {result}")


if __name__ == '__main__':
    main(sys.argv[1:])
