"""Entry point: descargar toda la media de un canal (imágenes y videos).

Uso:
  python download_all_media.py <canal|username|id> [--limit N] [--verbose]

Acepta `--maxmessages` como alias de compatibilidad.
"""
import argparse
import logging
import app.logger_config
from app.usecases.media_downloader import download_all_media


def main():
    parser = argparse.ArgumentParser(description="Descargar media reciente de un canal")
    parser.add_argument("channel", help="canal (username o id)")
    parser.add_argument("--limit", "-l", type=int, default=100, help="Límite de mensajes a revisar")
    parser.add_argument("--maxmessages", "-m", type=int, help="Alias histórico de límite (compatibilidad)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger(__name__).debug("Verbose logging enabled")

    limit = args.maxmessages if args.maxmessages is not None else args.limit
    result = download_all_media(args.channel, limit=limit)
    print(f"Resultado: {result}")


if __name__ == '__main__':
    main()
