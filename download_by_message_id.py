"""Entry point: descargar la media de un mensaje por su ID en un canal.

Uso:
  python download_by_message_id.py <canal|username|id> <message_id> [--out-folder OUT] [--nombre NAME] [--maxmessages N] [--verbose]

`--nombre` permite dar un nombre base al archivo resultante (se conserva la extensión).
`--maxmessages` se acepta por compatibilidad con otras CLI, pero no afecta a esta operación.
"""
import argparse
import logging
import os
import glob
import app.logger_config
from app.usecases.media_downloader import download_by_message_id


def main():
    parser = argparse.ArgumentParser(description="Descarga media por message_id desde un canal")
    parser.add_argument("channel", help="canal (username o id)")
    parser.add_argument("message_id", type=int, help="ID del mensaje a descargar")
    parser.add_argument("--out-folder", "-o", dest="out", help="Carpeta de salida (opcional)")
    parser.add_argument("--nombre", "-n", dest="nombre", help="Nombre base para el archivo descargado (sin extensión)")
    parser.add_argument("--maxmessages", "-m", dest="maxmessages", type=int, help="(opt) máximo de mensajes — no aplica aquí pero se acepta para compatibilidad")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger(__name__).debug("Verbose logging enabled")

    result_base = download_by_message_id(args.channel, args.message_id, out_folder=args.out)
    if not result_base:
        print("No se encontró media para ese message_id o la descarga falló.")
        return

    # download_by_message_id devuelve la ruta base (sin extensión inferida).
    # Buscamos archivo(s) que empiecen por esa base y les aplicamos el nuevo nombre si se pidió.
    matched = glob.glob(f"{result_base}*")
    if not matched:
        print(f"Descargado (ruta devuelta): {result_base} — no se encontraron archivos exactos con glob.")
        return

    if args.nombre:
        renamed_paths = []
        for path in matched:
            dirname = os.path.dirname(path)
            ext = os.path.splitext(path)[1]
            new_path = os.path.join(dirname, f"{args.nombre}{ext}")
            # Evitar sobreescribir
            if os.path.exists(new_path):
                print(f"Advertencia: {new_path} ya existe, no se sobrescribe.")
                continue
            os.rename(path, new_path)
            renamed_paths.append(new_path)
        if renamed_paths:
            print("Archivos renombrados:")
            for p in renamed_paths:
                print(p)
        else:
            print("No se renombraron archivos (posible conflicto de nombres).")
    else:
        print("Archivos descargados:")
        for p in matched:
            print(p)


if __name__ == '__main__':
    main()
