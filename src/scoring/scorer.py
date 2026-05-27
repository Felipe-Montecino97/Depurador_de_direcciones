VALID_ADDRESS_WORDS = {
    "avenida",
    "calle",
    "pasaje",
    "camino",
    "ruta",
    "sector",
    "villa",
    "poblacion",
    "condominio",
    "edificio",
    "departamento",
    "oficina",
    "local",
    "numero",
    "santiago",
    "providencia",
    "las",
    "condes",
    "maipu",
    "nunoa",
    "florida",
    "puente",
    "alto",
    "recoleta",
    "independencia",
}


NOISE_WORDS = {
    "asdf",
    "qwer",
    "zxcv",
    "test",
    "prueba",
    "nose",
    "nada",
    "xxx",
    "aaaa",
    "null",
    "none",
}

CONNECTOR_WORDS = {
    "de",
    "del",
    "la",
    "el",
    "los",
    "las",
    "y",
}

ADDRESS_HINTS = {
    "interior",
    "torre",
    "bloque",
    "piso",
    "villa",
    "sector",
    "parcela",
    "sitio",
    "manzana",
    "lote",
}


def _token_score(token: str) -> tuple[int, str]:
    if token in NOISE_WORDS:
        return -18, "ruido"
    if token.isdigit():
        if len(token) >= 3:
            return 12, "numero_calle"
        return 8, "numero"
    if token in VALID_ADDRESS_WORDS:
        return 10, "palabra_direccion"
    if token in ADDRESS_HINTS:
        return 7, "detalle_direccion"
    if token in CONNECTOR_WORDS:
        return 1, "conector"
    if token.isalpha() and len(token) >= 3:
        return 4, "texto_compatible"
    return -4, "token_debil"


def score_address(address: str) -> dict:
    if not address:
        return {
            "score": 0,
            "status": "VACIA",
            "reasons": ["La dirección está vacía."],
        }

    words = address.split()
    total_words = len(words)

    has_number = any(word.isdigit() for word in words)
    valid_words = [word for word in words if word in VALID_ADDRESS_WORDS]
    noise_words = [word for word in words if word in NOISE_WORDS]

    score = 10
    reasons = []
    token_analysis = []

    token_points = 0
    for token in words:
        points, category = _token_score(token)
        token_points += points
        token_analysis.append({"token": token, "points": points, "category": category})

    score += token_points
    reasons.append(f"Scoring palabra a palabra aplicado sobre {total_words} tokens.")

    if total_words >= 3:
        score += 15
        reasons.append("Tiene una cantidad mínima de palabras.")
    else:
        score -= 10
        reasons.append("Tiene muy pocas palabras.")

    if has_number:
        score += 15
        reasons.append("Contiene número.")
    else:
        score -= 8
        reasons.append("No contiene número.")

    if valid_words:
        points = min(len(valid_words) * 4, 20)
        score += points
        reasons.append(f"Contiene palabras propias de dirección: {valid_words}.")
    else:
        score -= 8
        reasons.append("No contiene palabras típicas de dirección.")

    if total_words >= 6:
        score += 12
        reasons.append("Es una dirección larga y se conserva para análisis.")

    if noise_words:
        penalty = min(len(noise_words) * 12, 36)
        score -= penalty
        reasons.append(f"Contiene palabras sospechosas: {noise_words}.")

    score = max(0, min(score, 100))

    if score >= 70:
        status = "BUENA"
    elif score >= 40:
        status = "REVISAR"
    else:
        status = "SOSPECHOSA"

    return {
        "score": score,
        "status": status,
        "reasons": reasons,
        "token_analysis": token_analysis,
    }
