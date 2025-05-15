import os

def remove_file(path):
    try:
        os.remove(path)
    except OSError as e:
        print(f"Error al eliminar {path}: {e}")
