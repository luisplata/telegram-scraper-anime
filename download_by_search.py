"""Entry point: buscar por texto dentro de un canal y descargar media coincidente.

Uso:
  python download_by_search.py <canal|username|id> [limite] "texto_busqueda"
"""
import sys
from app.usecases.media_downloader import download_by_search


def main(argv):
    if len(argv) < 3:
        print("Uso: python download_by_search.py <canal> [limite] \"texto_busqueda\"")
        return
    channel = argv[0]
    try:
        limit = int(argv[1])
        search = argv[2]
    except ValueError:
        # si el usuario pasa solo 2 args: canal y texto
        limit = 100
        search = argv[1]

    result = download_by_search(channel, search, limit=limit)
    print(f"Resultado: {result}")


if __name__ == '__main__':
    main(sys.argv[1:])
