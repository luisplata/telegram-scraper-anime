# logger_config.py
import logging
import os

# Asegura que exista el directorio para los logs
os.makedirs("logs", exist_ok=True)

# Configura el logger raíz
logging.basicConfig(
    level=logging.INFO,  # Cambia a DEBUG si quieres más detalles
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/scraper.log", encoding="utf-8"),  # Archivo
        logging.StreamHandler()  # Consola
    ]
)
