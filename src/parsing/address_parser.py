from __future__ import annotations

import re


DETAIL_KEYWORDS = {
    "departamento",
    "depto",
    "dpto",
    "dp",
    "oficina",
    "of",
    "interior",
    "torre",
    "block",
    "bloque",
    "piso",
    "villa",
    "condominio",
    "casa",
}


NUMBER_PATTERN = re.compile(r"\b\d{1,6}[a-z]?\b", re.IGNORECASE)


def _normalize_numero_raw(numero_raw: str) -> str:
    raw = str(numero_raw or "").strip()
    if not raw or raw.lower() == "nan":
        return ""

    raw = raw.replace(",", ".")
    if raw.endswith(".0"):
        raw = raw[:-2]

    token = raw.split()[0]
    if token.isdigit() and int(token) > 0:
        return token

    return ""


def _extract_number_candidates(address: str) -> list[str]:
    candidates = []
    for match in NUMBER_PATTERN.finditer(address):
        value = match.group(0).lower()
        if value.isdigit() and int(value) == 0:
            continue
        candidates.append(value)
    return candidates


def _extract_detail_tokens(tokens: list[str]) -> list[str]:
    details: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in DETAIL_KEYWORDS:
            details.append(token)
            if i + 1 < len(tokens):
                nxt = tokens[i + 1]
                if re.fullmatch(r"[a-z0-9-]+", nxt):
                    details.append(nxt)
                    i += 1
        i += 1
    return details


def parse_address_components(cleaned_address: str, numero_raw: str) -> dict[str, str]:
    tokens = cleaned_address.split()

    numero_from_column = _normalize_numero_raw(numero_raw)
    number_candidates = _extract_number_candidates(cleaned_address)

    if numero_from_column:
        numero_final = numero_from_column
    elif number_candidates:
        long_candidates = [candidate for candidate in number_candidates if any(ch.isdigit() for ch in candidate) and len(candidate) >= 3]
        numero_final = long_candidates[0] if long_candidates else number_candidates[0]
    else:
        numero_final = ""

    detail_tokens = _extract_detail_tokens(tokens)
    detail_set = set(detail_tokens)

    base_tokens: list[str] = []
    removed_number = False
    for token in tokens:
        if not removed_number and numero_final and token.lower() == numero_final.lower():
            removed_number = True
            continue
        if token in detail_set:
            continue
        base_tokens.append(token)

    direccion_base = " ".join(base_tokens).strip()
    detalle_direccion = " ".join(detail_tokens).strip()

    return {
        "direccion_base": direccion_base,
        "numero_final": numero_final,
        "detalle_direccion": detalle_direccion,
    }
