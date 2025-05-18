import requests
from config import API_SEARCH_URL, API_WEBHOOK_URL, API_WEBHOOK_TOKEN
from difflib import SequenceMatcher
import json

def buscar_anime_en_api(nombre_anime):
    try:
        # El parámetro correcto es 'q', no 'query'
        response = requests.get(API_SEARCH_URL, params={"q": nombre_anime})
        response.raise_for_status()
        resultados = response.json()
        return resultados['data']
    except Exception as e:
        print(f"Error buscando anime: {e}")
        return []

def formatear_payload(anime: dict, cap_num: int, link: str):
    caps = anime.get("caps", [])

    # Asegura que name sea una lista de strings
    name = anime.get("title", [])
    if isinstance(name, str):
        name_list = name.split()
        title_str = name
    elif isinstance(name, list):
        name_list = name
        title_str = " ".join(name)
    else:
        name_list = []
        title_str = ""

    nuevo_capitulo = {
        "title": title_str,
        "number": int(cap_num),
        "link": link,
        "source": [
            {
                "name": "streamhg",
                "url": link
            }
        ]
    }

    caps.append(nuevo_capitulo)

    return [{
        "name": name_list,
        "slug": anime.get("slug", ""),
        "description": anime.get("description", ""),
        "image": anime.get("image", ""),
        "caps": caps
    }]


def enviar_webhook(anime_data):
    print(json.dumps(anime_data, indent=2, ensure_ascii=False))
    headers = {
        "X-Webhook-Token": API_WEBHOOK_TOKEN,
        "Content-Type": "application/json"
    }
    try:
        print(anime_data)
        print(headers)
        response = requests.post(API_WEBHOOK_URL, json=anime_data, headers=headers)
        response.raise_for_status()
        print("✅ Webhook enviado con éxito.")
        return True
    except Exception as e:
        print(f"Error al enviar webhook: {e}")
        return False

def compartir_anime(nombre_anime, cap_num, link):
    resultados = buscar_anime_en_api(nombre_anime)

    if len(resultados) == 1:
        anime = resultados[0]
        print(anime)
        payload = formatear_payload(anime, cap_num, link)
        exito = enviar_webhook(payload)
        return exito
    else:
        print(f"⚠️ {len(resultados)} resultados encontrados para '{nombre_anime}'. Buscando el más parecido...")
        mejores = []
        for anime in resultados:
            titulo = anime.get("title", "")
            porcentaje = calcular_match(nombre_anime, titulo)
            mejores.append((porcentaje, anime))
            print(f"Comparando con '{titulo}': {porcentaje:.2f}% match")
        mejores.sort(reverse=True, key=lambda x: x[0])
        if mejores and mejores[0][0] > 80:  # Puedes ajustar el umbral
            mejor_anime = mejores[0][1]
            print(f"Mejor coincidencia: {mejor_anime['title']} ({mejores[0][0]:.2f}%)")
            payload = formatear_payload(mejor_anime, cap_num, link)
            exito = enviar_webhook(payload)
            return exito
        else:
            print("❌ No se encontró una coincidencia suficientemente buena.")
            return False

def calcular_match(nombre_a, nombre_b):
    nombre_a = nombre_a.lower()
    nombre_b = nombre_b.lower()
    if nombre_a in nombre_b or nombre_b in nombre_a:
        return 100.0
    return SequenceMatcher(None, nombre_a, nombre_b).ratio() * 100