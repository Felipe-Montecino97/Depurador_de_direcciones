import re
import unicodedata


ABBREVIATIONS = {
    "av": "avenida",
    "av.": "avenida",
    "avda": "avenida",
    "aven": "avenida",
    "cal": "calle",
    "cll": "calle",
    "pj": "pasaje",
    "pje": "pasaje",
    "psje": "pasaje",
    "pobl": "poblacion",
    "pob": "poblacion",
    "depto": "departamento",
    "dpto": "departamento",
    "dep": "departamento",
    "of": "oficina",
    "ofi": "oficina",
    "nro": "numero",
    "num": "numero",
    "n": "numero",
    "n°": "numero",
    "#": "numero",
    "stgo": "santiago",
}

MEANINGFUL_SHORT_TOKENS = {"n", "b", "a", "km"}

KNOWN_TEXT_REPLACEMENTS = {
    "torreconcepcion": "torre concepcion",
    "manantialesvaldivia": "manantiales valdivia",
    "mistrallas": "mistral las",
    "animaslas": "animas las",
    "dechilemaipu": "de chile maipu",
    "sabellaantofagasta": "sabella antofagasta",
    "estrellapudahuel": "estrella pudahuel",
    "condoromalos": "condoroma los",
    "nalcahuesan": "nalcahue san",
    "diegoportales": "diego portales",
    "penonsotero": "penon sotero",
    "costaneratalagante": "costanera talagante",
    "centralquilicura": "central quilicura",
    "quellonquellon": "quellon quellon",
    "salinastalcahuano": "salinas talcahuano",
    "puntillapirque": "puntilla pirque",
    "cantohualpen": "canto hualpen",
    "franckepuyehue": "francke puyehue",
    "catalunacurico": "cataluna curico",
    "tierraamarilla": "tierra amarilla",
}


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _apply_known_replacements(text: str) -> str:
    updated = text
    for source, target in KNOWN_TEXT_REPLACEMENTS.items():
        updated = updated.replace(source, target)
    return updated


def _collapse_repeated_phrases(text: str) -> str:
    current = text
    # Colapsa duplicaciones consecutivas exactas de 1 a 3 palabras.
    for size in (3, 2, 1):
        words = current.split()
        if len(words) < size * 2:
            continue

        collapsed: list[str] = []
        index = 0
        while index < len(words):
            phrase_a = words[index : index + size]
            phrase_b = words[index + size : index + (size * 2)]
            if len(phrase_a) == size and phrase_a == phrase_b:
                collapsed.extend(phrase_a)
                index += size * 2
                continue
            collapsed.append(words[index])
            index += 1

        current = " ".join(collapsed)

    current = current.replace("los andeslos andes", "los andes")
    current = current.replace("las animaslas animas", "las animas")
    current = current.replace("el quisco el quisco", "el quisco")
    current = current.replace("quellon quellon", "quellon")
    current = current.replace("tierra amarilla tierra amarilla", "tierra amarilla")
    return current


def clean_address(address: str) -> str:
    if not isinstance(address, str):
        return ""

    text = address.lower().strip()
    text = remove_accents(text)

    text = text.replace(",", " ")
    text = text.replace(".", " ")
    text = text.replace(";", " ")
    text = text.replace(":", " ")
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = text.replace("#", " # ")

    text = re.sub(r"[^a-z0-9#\s]", " ", text)
    text = re.sub(r"\b(\d+)\s+v\b$", r"\1", text)
    text = re.sub(r"\bv\b$", " ", text)

    words = text.split()

    normalized_words = []
    for word in words:
        normalized = ABBREVIATIONS.get(word, word)

        # Se conservan tokens cortos que aportan contexto útil.
        if len(normalized) == 1 and not normalized.isdigit() and normalized not in MEANINGFUL_SHORT_TOKENS:
            continue

        normalized_words.append(normalized)

    text = " ".join(normalized_words)
    text = _apply_known_replacements(text)
    text = _collapse_repeated_phrases(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text
