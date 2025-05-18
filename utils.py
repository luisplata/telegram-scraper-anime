import re

def limpiar_nombre(texto, max_length=50):
    texto = re.sub(r'[\\/*?:"<>|]', '_', texto)  # reemplaza caracteres inválidos
    texto = texto.strip()
    texto = texto.replace(' ', '_')  # reemplaza espacios por guiones bajos
    if len(texto) > max_length:
        texto = texto[:max_length].rstrip()
    return texto

def formatear_nombre_video(texto_mensaje):
    if not texto_mensaje:
        return "video_sin_titulo", "00", "sub", "video_sin_titulo"

    # Buscar episodio/capítulo en todo el texto
    match = re.search(r"(Episodio|Cap[ií]tulo)\s*(\d+)", texto_mensaje, re.IGNORECASE)
    numero_cap = match.group(2).zfill(2) if match else "00"

    # Detectar idioma
    texto_lower = texto_mensaje.lower()
    if "audio latino" in texto_lower or "🇲🇽" in texto_mensaje:
        etiqueta_audio = "dub_latino"
    else:
        etiqueta_audio = "sub_latino"

    # Quitar episodio y subtítulo/idioma del nombre del anime
    nombre_anime = texto_mensaje
    # Quitar "Episodio XX" o "Capítulo XX"
    nombre_anime = re.sub(r"(Episodio|Cap[ií]tulo)\s*\d+", "", nombre_anime, flags=re.IGNORECASE)
    # Quitar "Sub Español", "Audio Latino", etc.
    nombre_anime = re.sub(r"(Sub Español|Audio Latino|Sub Español|Sub|Español|Latino|🇲🇽)", "", nombre_anime, flags=re.IGNORECASE)
    nombre_anime = nombre_anime.strip(" -–—:|")

    nombre_anime_limpio = limpiar_nombre(nombre_anime)
    return nombre_anime_limpio, numero_cap, etiqueta_audio, nombre_anime