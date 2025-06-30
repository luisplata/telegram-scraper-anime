telegram-scraper-anime

Este proyecto permite descargar y gestionar contenido multimedia (videos e imágenes) de canales de Telegram, especialmente orientado a anime, y automatizar su procesamiento y subida a otros servicios.

REQUISITOS

Python 3.8+
Telethon
Variables de entorno configuradas en un archivo .env (ver .env.example)
CONFIGURACIÓN

Renombra .env.example a .env y completa tus credenciales de Telegram y otros servicios.
Instala las dependencias: pip install -r requirements.txt
SCRIPTS

main.py

Función: Automatiza el flujo completo: descarga videos de Telegram, los sube a un servidor externo y actualiza la base de datos.

Uso: python main.py

Procesa hasta MAX_CAPS capítulos por ejecución (configurable en .env).
Guarda logs de ejecución en historico_ejecuciones.log.
download_channel_media.py

Función: Descarga todos los videos e imágenes de un canal de Telegram, guardando los metadatos en un archivo JSON.

Uso: python download_channel_media.py <nombre_canal|username|id> [limite]

Ejemplo: python download_channel_media.py Miagreyxox 50 python download_channel_media.py 123456789 100

Crea la estructura: downloads/<canal>/images/ downloads/<canal>/videos/ downloads/<canal>/db_<canal>.json

download_chanel_media_by_text.py

Función: Descarga solo los mensajes que coincidan con un texto de búsqueda (por ejemplo, un hashtag o palabra clave). Soporta álbumes (colecciones) de Telegram y guarda los archivos en un subdirectorio con el nombre de la búsqueda.

Uso: python download_chanel_media_by_text.py <nombre_canal|username|id> [limite] [texto_busqueda]

Ejemplo: python download_chanel_media_by_text.py melissajordan1 50 "#LilyPhillips"

Estructura de carpetas: downloads/<canal>/<texto_busqueda>/images/ downloads/<canal>/<texto_busqueda>/videos/ downloads/<canal>/<texto_busqueda>/db_<canal>.json

Si el texto de búsqueda coincide con un mensaje de un álbum, descarga todos los elementos del álbum.

NOTAS

Los scripts usan la sesión de Telethon, asegúrate de no ejecutar varios a la vez con la misma sesión.
Si tienes problemas con caracteres especiales en nombres de carpetas, el script los reemplaza automáticamente.
El archivo de base de datos (db_<canal>.json) contiene los metadatos de los archivos descargados.
LICENCIA

MIT