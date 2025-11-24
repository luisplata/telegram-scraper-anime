"""Entry point: buscar por texto dentro de un canal y descargar media coincidente.

Uso:
  python download_by_search.py <canal|username|id> <texto_busqueda> [--limit N] [--verbose]

También acepta `--maxmessages` por compatibilidad.
"""
import argparse
import logging
import app.logger_config
from app.usecases.media_downloader import download_by_search


def main():
    parser = argparse.ArgumentParser(description="Buscar por texto en un canal y descargar media")
    parser.add_argument("channel", help="canal (username o id)")
    parser.add_argument("search", help="texto a buscar (entre comillas si contiene espacios)")
    parser.add_argument("--limit", "-l", type=int, default=100, help="Límite de mensajes a revisar")
    parser.add_argument("--maxmessages", "-m", type=int, help="Alias histórico de límite (compatibilidad)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    # enable verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger(__name__).debug("Verbose logging enabled")

    limit = args.maxmessages if args.maxmessages is not None else args.limit

    result = download_by_search(args.channel, args.search, limit=limit)
    print(f"Resultado: {result}")


if __name__ == '__main__':
    main()
