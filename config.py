import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
VIEW_URL = os.getenv("VIEW_URL")

SESSION_NAME = "anon"
DOWNLOAD_FOLDER = "downloads"
CHANNEL_ID = 1888892519  # El id del canal que usas
