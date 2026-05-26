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

    score = 0
    reasons = []

    if total_words >= 3:
        score += 20
        reasons.append("Tiene una cantidad mínima de palabras.")
    else:
        reasons.append("Tiene muy pocas palabras.")

    if has_number:
        score += 25
        reasons.append("Contiene número.")
    else:
        reasons.append("No contiene número.")

    if valid_words:
        points = min(len(valid_words) * 10, 30)
        score += points
        reasons.append(f"Contiene palabras propias de dirección: {valid_words}.")
    else:
        reasons.append("No contiene palabras típicas de dirección.")

    if total_words >= 6:
        score += 15
        reasons.append("Es una dirección larga, se conserva para análisis.")

    if noise_words:
        penalty = min(len(noise_words) * 20, 40)
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
    }
