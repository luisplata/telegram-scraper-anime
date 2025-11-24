# telegram-scraper-anime

Proyecto para buscar y descargar contenido multimedia (videos/imágenes) desde canales de Telegram, enfocado en material de anime. Incluye utilidades para organizar archivos, almacenar metadatos, y subir archivos a un servidor externo.

**Features:**
- **Descarga de medios:** descarga imágenes y videos de canales o búsquedas dentro de un canal.
- **Soporte a álbumes:** detecta y descarga todos los elementos de un álbum (grouped_id).
- **Base de datos ligera:** guarda metadatos en JSON o en SQLite (`db_manager.py`) para seguimiento de estado (descargado/subido/compartido).
- **Subida remota:** utilidades para enviar archivos a un servidor externo (`uploader.py`).

**Requisitos:**
- Python 3.8+
- Dependencias: ver `requirements.txt` (ej. `telethon`, `requests`, `python-dotenv`, `filelock`).
- Un archivo de variables de entorno `.env` con credenciales (ver `config.py`).

**Instalación rápida:**
```bash
python -m venv venv
source venv/Scripts/activate    # en Windows + bash.exe
pip install -r requirements.txt
```

**Configuración:**
- Crea un archivo `.env` con las variables requeridas. `config.py` carga estas variables con `python-dotenv`. Entidades importantes:
	- `API_ID`, `API_HASH` (credenciales de Telegram)
	- `SESSION_NAME` (nombre de la sesión de Telethon)
	- `API_KEY`, `API_URL`, `API_WEBHOOK_URL`, etc. (según integraciones)
	- `MAX_CAPS` (límite de procesamiento, opcional)

**Principales scripts / módulos:**
- `download_channel_media.py` : Descarga imágenes y videos de un canal. Uso:
	```bash
	python download_channel_media.py <canal>|<username>|<id> [limite] [texto_busqueda]
	```
	Crea la estructura `downloads/<canal>/(images|videos)/` y un `db_<canal>.json` con metadatos.
- `download_chanel_media_by_text.py` : Variante para buscar por texto/hashtag y descargar solo mensajes coincidentes.
- `telegram_client.py` : Funciones utilitarias para listar canales, obtener mensajes y descargar media (cliente simple de Telethon).
- `telegram_facade.py` : Fachada para manejar múltiples canales con handlers específicos (`Anime.AnimeChannelHandle`).
- `uploader.py` : Lógica para obtener un servidor de subida y enviar archivos.
- `db_manager.py` : Implementa una base SQLite (`AnimeDB`) para llevar control más estructurado de animes, capítulos y estados.
- `config.py` : Carga variables de entorno con `dotenv`.

- Nuevos entrypoints (arquitectura hexagonal):
	- `search_by_string.py` : Busca por texto/hashtag en un canal y descarga la media coincidente.
		```bash
		python search_by_string.py <canal> [limite] "texto_busqueda"
		```
	- `download_all_media.py` : Descarga todas las medias recientes de un canal.
		```bash
		python download_all_media.py <canal> [limite]
		```
	- `download_by_message_id.py` : Descarga la media de un mensaje específico por su ID.
		```bash
		python download_by_message_id.py <canal> <message_id> [out_folder]
		```

Estas entradas son scripts mínimos (entrypoints). La lógica se encuentra en `app/adapters/telethon_adapter.py` y `app/usecases/media_downloader.py`.

**Uso básico (ejemplos):**
- Descargar medios de un canal (100 mensajes por defecto):
	```bash
	python download_channel_media.py el_nombre_del_canal 100
	```
- Descargar por texto/hashtag:
	```bash
	python download_channel_media.py el_nombre_del_canal 200 "#miEtiqueta"
	```
- Subir un archivo (ejemplo desde Python):
	```py
	from uploader import subir_video
	subir_video('downloads/mi_canal/videos/video_...mp4', title='Capítulo 1')
	```

**Estructura del repositorio (archivos clave):**
- `download_channel_media.py` — Descarga y organiza archivos en `downloads/`.
- `download_chanel_media_by_text.py` — Descarga filtrada por texto.
- `telegram_client.py` — Helpers y funciones de descarga.
- `telegram_facade.py` — Fachada para manejar canales con handlers.
- `uploader.py` — Subida a servicio externo.
- `db_manager.py` — Manejo de SQLite para seguimiento de animes/capitulos.
- `requirements.txt` — Dependencias.

**Notas y buenas prácticas:**
- No ejecutar varios procesos que usen la misma sesión de Telethon simultáneamente.
- Asegúrate de tener permisos y respetar las políticas de contenido y copyright al descargar y distribuir archivos.
- Algunos scripts pueden escribir rutas con barras escapadas en JSON para compatibilidad en Windows.

**Tests:**
- Hay tests básicos para los usecases en `tests/test_media_usecases.py` que usan un cliente simulado. Ejecuta:
	```bash
	pip install -r requirements.txt
	pytest -q
	```

Si quieres, puedo:
- Añadir ejemplos de `.env` o validar que `config.py` cubra todas las variables.
- Añadir instrucciones para usar `db_manager.py` desde la línea de comandos.

**Licencia:** MIT