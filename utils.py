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

    partes = texto_mensaje.split("»")
    if len(partes) < 2:
        nombre_anime = texto_mensaje.strip()
        return limpiar_nombre(nombre_anime), "00", "NoSub", nombre_anime

    nombre_anime = partes[0].strip()
    resto = partes[1].strip()

    # Extraer número de episodio
    match = re.search(r"(Episodio|Capítulo)\s*(\d+)", resto, re.IGNORECASE)
    numero_cap = match.group(2).zfill(2) if match else "00"

    # Detectar idioma
    resto_lower = resto.lower()
    if "audio latino" in resto_lower or "🇲🇽" in resto:
        etiqueta_audio = "dub_latino"
    else:
        etiqueta_audio = "sub_latino"

    nombre_anime_limpio = limpiar_nombre(nombre_anime)
    return nombre_anime_limpio, numero_cap, etiqueta_audio, nombre_anime
