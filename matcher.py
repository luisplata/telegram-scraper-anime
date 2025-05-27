from difflib import SequenceMatcher
import re

def normalizar_nombre(nombre):
    nombre = nombre.lower()
    nombre = re.sub(r'[^a-z0-9\s]', '', nombre)
    nombre = re.sub(r'\b(season|part|episode|ep|cap|sono|ni|junior|youth|hen)\b', '', nombre)
    nombre = re.sub(r'\b\d+\b', '', nombre)
    nombre = re.sub(r'\s+', ' ', nombre)
    return nombre.strip()

def match_ratio(nombre_a, nombre_b):
    """Match por ratio de SequenceMatcher."""
    return SequenceMatcher(None, nombre_a, nombre_b).ratio() * 100

def match_por_palabras(nombre_a, nombre_b):
    palabras_a = nombre_a.split()
    palabras_b = nombre_b.split()
    if not palabras_a or not palabras_b:
        return 0
    matches_a = [max(SequenceMatcher(None, pa, pb).ratio() for pb in palabras_b) for pa in palabras_a]
    matches_b = [max(SequenceMatcher(None, pb, pa).ratio() for pa in palabras_a) for pb in palabras_b]
    promedio_a = sum(matches_a) / len(matches_a) * 100
    promedio_b = sum(matches_b) / len(matches_b) * 100
    return (promedio_a + promedio_b) / 2

def match_por_set(nombre_a, nombre_b):
    tokens_a = set(nombre_a.split())
    tokens_b = set(nombre_b.split())
    interseccion = tokens_a & tokens_b
    union = tokens_a | tokens_b
    if union:
        return len(interseccion) / len(union) * 100
    return 0

def match_bonus_primera_palabra(nombre_a, nombre_b):
    """Bonus si la primera palabra coincide."""
    try:
        if nombre_a.split()[0] == nombre_b.split()[0]:
            return 100  # Bonus máximo si coincide
    except IndexError:
        pass
    return 0

def match_inclusion(nombre_a, nombre_b):
    """100% si uno está contenido en el otro."""
    if nombre_a in nombre_b or nombre_b in nombre_a:
        return 100.0
    return 0

def match_inclusion_parcial(nombre_a, nombre_b):
    if nombre_a in nombre_b or nombre_b in nombre_a:
        return 100
    # Bonus si el nombre corto está como substring en el largo
    if len(nombre_a) < len(nombre_b) and nombre_a in nombre_b:
        return 90
    if len(nombre_b) < len(nombre_a) and nombre_b in nombre_a:
        return 90
    return 0

def match_subsecuencia(nombre_a, nombre_b):
    # Devuelve 100 si todas las palabras de A están en B (en cualquier orden)
    palabras_a = set(nombre_a.split())
    palabras_b = set(nombre_b.split())
    if palabras_a and palabras_a.issubset(palabras_b):
        return 100
    if palabras_b and palabras_b.issubset(palabras_a):
        return 100
    # Bonus proporcional si la mayoría están
    interseccion = palabras_a & palabras_b
    if palabras_a:
        return len(interseccion) / len(palabras_a) * 100
    return 0

def ngramas(texto, n=2):
    palabras = texto.split()
    return set([' '.join(palabras[i:i+n]) for i in range(len(palabras)-n+1)])

def match_ngramas(nombre_a, nombre_b, n=2):
    ngramas_a = ngramas(nombre_a, n)
    ngramas_b = ngramas(nombre_b, n)
    interseccion = ngramas_a & ngramas_b
    union = ngramas_a | ngramas_b
    if union:
        return len(interseccion) / len(union) * 100
    return 0

MATCH_FUNCTIONS = [
    (match_por_palabras, 1),
    (match_por_set, 0.5),
    (match_ratio, 1),
    (match_bonus_primera_palabra, 0.5),
    (match_inclusion, 2),           # más peso
    (match_subsecuencia, 2),        # más peso
    (lambda a, b: match_ngramas(a, b, 2), 0.5),
    (match_inclusion_parcial, 1.5), # más peso
]

def calcular_match(nombre_a, nombre_b):
    nombre_a = normalizar_nombre(nombre_a)
    nombre_b = normalizar_nombre(nombre_b)
    resultados = []
    for func, peso in MATCH_FUNCTIONS:
        try:
            resultados.append(func(nombre_a, nombre_b))
        except Exception as e:
            print(f"Error en función de match {func.__name__}: {e}")
    print(f"Resultados de match para '{nombre_a}' y '{nombre_b}': {resultados}")
    if resultados:
        return (sum(resultados) / len(resultados) + max(resultados)) / 2
    return 0

if __name__ == "__main__":
    print(calcular_match("Slime Taoshite 300-nen Season 2", "Slime Taoshite 300-nen, Shiranai Uchi ni Level Max ni Nattemashita"))