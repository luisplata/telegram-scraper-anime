import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
VIEW_URL = os.getenv("VIEW_URL")
API_SEARCH_URL = os.getenv("API_SEARCH_URL")
API_WEBHOOK_URL = os.getenv("API_WEBHOOK_URL")
API_WEBHOOK_TOKEN = os.getenv("API_WEBHOOK_TOKEN")
MAX_CAPS=int(os.getenv("MAX_CAPS"))



SESSION_NAME = "anon"
DOWNLOAD_FOLDER = "downloads"
CHANNEL_ID = 1888892519  # El id del canal que usas
