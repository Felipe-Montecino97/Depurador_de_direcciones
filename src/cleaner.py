import re
import unicodedata


ABBREVIATIONS = {
    "av": "avenida",
    "av.": "avenida",
    "aven": "avenida",
    "cal": "calle",
    "pje": "pasaje",
    "psje": "pasaje",
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


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


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
    text = text.replace("#", " # ")

    text = re.sub(r"[^a-z0-9#\s]", " ", text)

    words = text.split()

    normalized_words = []
    for word in words:
        normalized_words.append(ABBREVIATIONS.get(word, word))

    text = " ".join(normalized_words)
    text = re.sub(r"\s+", " ", text).strip()

    return text
