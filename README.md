# telegram-scraper-anime

Proyecto para buscar y descargar contenido multimedia (videos/imágenes) desde canales de Telegram, con foco en material de anime. La implementación principal se ha movido a una estructura de `app/` (usecases + adapters). Versiones antiguas del código y utilidades están preservadas en `legacy/`.

Características principales:
- Descarga de medios (imágenes y videos) por canal o por búsquedas dentro de un canal.
- Detección y descarga de álbumes (`grouped_id`).
- Metadatos ligeros en JSON / SQLite para seguimiento del estado.

Requisitos:
- Python 3.8+
- Dependencias: ver `requirements.txt` (ej. `telethon`, `requests`, `python-dotenv`, `filelock`).
- Variables de entorno en un archivo `.env` (usa `config.py` para cargarlas).

Instalación rápida:
```bash
python -m venv venv
source venv/Scripts/activate    # en Windows + bash.exe
pip install -r requirements.txt
```

Configuración:
- Rellena `.env` con `API_ID`, `API_HASH`, `SESSION_NAME` y otras variables necesarias.

Entrypoints disponibles (doble propósito: CLI simple + reutilización en scripts):
- `download_channel_media.py` — Descarga imágenes y videos de un canal.
  ```bash
  python download_channel_media.py <canal>|<username>|<id> [limite] [texto_busqueda]
  ```
- `download_by_search.py` — Buscar por texto/hashtag en un canal y descargar la media coincidente.
  ```bash
  python download_by_search.py <canal> [limite] "texto_busqueda"
  ```
- `download_all_media.py` — Descargar las medias recientes de un canal.
  ```bash
  python download_all_media.py <canal> [limite]
  ```
- `download_by_message_id.py` — Descargar la media de un mensaje por su ID.
  ```bash
  python download_by_message_id.py <canal> <message_id> [out_folder]
  ```

Notas sobre la organización:
- La lógica principal se encuentra en `app/usecases/` y `app/adapters/`.
- Código antiguo/copias de seguridad se mantienen en `legacy/` (no son entrypoints). Esto mantiene el root limpio y evita ruido.

Uso básico (ejemplos):
```bash
python download_channel_media.py el_nombre_del_canal 100
python download_by_search.py el_nombre_del_canal 200 "#miEtiqueta"
python download_by_message_id.py el_nombre_del_canal 12345
```

Estructura destacada:
- `app/` — Nuevas implementaciones (usecases + adapters).
- `legacy/` — Implementaciones preservadas (no recomendadas para uso directo).
- `tests/` — Tests unitarios (ejecutar con `pytest`).

Tests:
```bash
pip install -r requirements.txt
pytest -q
```

Si quieres, puedo también:
- Añadir un CHANGELOG con estos cambios.
- Crear una rama y abrir un PR con la limpieza del root.

Licencia: MIT