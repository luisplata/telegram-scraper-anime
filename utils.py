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
        return "video_sin_titulo", "00"
    partes = texto_mensaje.split("»")
    if len(partes) < 2:
        nombre_anime = limpiar_nombre(texto_mensaje.strip())
        return nombre_anime, "00"
    
    nombre_anime = partes[0].strip()
    resto = partes[1].strip()
    
    match = re.search(r"(Episodio|Capítulo)\s*(\d+)", resto, re.IGNORECASE)
    if match:
        numero_cap = match.group(2).zfill(2)
    else:
        numero_cap = "00"
    
    nombre_anime_limpio = limpiar_nombre(nombre_anime)
    return nombre_anime_limpio, numero_cap
