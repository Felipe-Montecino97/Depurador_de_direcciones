from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter
from pathlib import Path


GLUED_TOKEN_PATTERN = re.compile(r"[a-zA-Z]+\d{2,}|\d{2,}[a-zA-Z]+")
SUSPICIOUS_TOKEN_PATTERN = re.compile(r"\b(?:v|sn|s/n|numero|0)\b", re.IGNORECASE)
TRAILING_V_PATTERN = re.compile(r"(?:^|\s)\d+\s+v$|(?:^|\s)v$", re.IGNORECASE)
TRAILING_DIRECTIONAL_PATTERN = re.compile(r"(?:^|\s)(?:sur|norte|oriente|poniente)\s+\d+$", re.IGNORECASE)
DIRECTIONAL_WORDS = {"sur", "norte", "oriente", "poniente"}
VALID_DIRECTIONAL_PREFIXES = {
    "avenida",
    "av",
    "calle",
    "pasaje",
    "psje",
    "pje",
    "diagonal",
    "camino",
    "ruta",
    "sector",
    "villa",
    "poblacion",
}
NUMBER_WORD_PREFIXES = {
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
    "diez",
    "veintinueve",
}
VALID_DIRECTIONAL_PHRASES = {
    "diagonal oriente",
    "americo vespucio sur",
    "cruz del sur",
    "carretera norte",
    "uno oriente",
    "dos poniente",
    "veintinueve sur",
    "quinta sur",
    "errazuriz sur",
}
MASTER_CATALOG_PATH = Path("Maestro/output/maestro_territorial_chile.csv")
KNOWN_COMPLEX_GLUE_PATTERNS = {
    "torreconcepcion",
    "animaslas",
    "mistrallas",
    "manantialesvaldivia",
    "andeslos",
    "sabellaantofagasta",
    "estrellapudahuel",
    "condoromalos",
    "nalcahuesan",
    "penonsotero",
}


def _normalize_text(value: str) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.upper().split())


def _clean_text(value: str) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    return text


def _number_text(value: str) -> str:
    text = _clean_text(value)
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _load_catalog_places() -> set[str]:
    places: set[str] = set()
    if not MASTER_CATALOG_PATH.exists():
        return places

    with MASTER_CATALOG_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            comuna = _normalize_text(row.get("nombre_comuna", ""))
            if comuna:
                places.add(comuna)
    return places


CATALOG_PLACES = _load_catalog_places()


def _build_issue(
    row: dict,
    problema: str,
    severidad: str,
    sugerencia: str,
) -> dict:
    return {
        "RUT+DV": row.get("RUT+DV", ""),
        "direccion": row.get("direccion", ""),
        "numero": row.get("numero", ""),
        "comuna": row.get("comuna", ""),
        "ciudad": row.get("ciudad", ""),
        "region": row.get("region", ""),
        "problema_detectado": problema,
        "severidad": severidad,
        "sugerencia": sugerencia,
    }


def _is_short_address_valid(direccion: str, numero: str, comuna: str, ciudad: str) -> bool:
    words = _clean_text(direccion).split()
    if len(words) != 1:
        return False
    if numero:
        return True
    if comuna or ciudad:
        return True
    return False


def _has_complex_glued_word(direccion: str) -> bool:
    lowered = _clean_text(direccion).lower()
    if not lowered:
        return False

    compact = lowered.replace(" ", "")
    if any(pattern in compact for pattern in KNOWN_COMPLEX_GLUE_PATTERNS):
        return True

    # Alta confianza: palabras unidas que terminan o contienen claramente una comuna catalogada.
    for token in lowered.split():
        token_norm = _normalize_text(token)
        if len(token_norm) < 12:
            continue
        for place in CATALOG_PLACES:
            if len(place) < 6:
                continue
            if token_norm.endswith(place) and token_norm != place:
                return True
            if place in token_norm and token_norm != place and not token_norm.startswith(place):
                return True

    return False


def _has_repeated_fragment(direccion: str) -> bool:
    lowered = _clean_text(direccion).lower()
    if not lowered:
        return False
    compact = lowered.replace(" ", "")
    return bool(re.search(r"([a-z]{3,})\1", compact)) or bool(re.search(r"([a-z]{3,})\s+\1", lowered))


def _classify_directional_suffix(direccion: str, comuna: str, ciudad: str) -> str:
    text = _clean_text(direccion)
    if not text:
        return ""

    normalized = _normalize_text(text)
    words = normalized.split()
    lower_words = [word.lower() for word in words]
    lower_text = " ".join(lower_words)
    if len(words) < 2:
        return ""

    if not re.search(r"(?:^|\s)(SUR|NORTE|ORIENTE|PONIENTE)(?:\s+\d+)?$", normalized):
        return ""

    trusted_places = [_normalize_text(comuna), _normalize_text(ciudad)]
    trusted_places = [place for place in trusted_places if place]
    for place in trusted_places:
        if re.search(rf"(?:^|\s){re.escape(place)}\s+(SUR|NORTE|ORIENTE|PONIENTE)(?:\s+\d+)?$", normalized):
            return "RESIDUO_TERRITORIAL_DIRECCIONAL"

    for place in CATALOG_PLACES:
        if re.search(rf"(?:^|\s){re.escape(place)}\s+(SUR|NORTE|ORIENTE|PONIENTE)\s+\d+$", normalized):
            return "RESIDUO_TERRITORIAL_DIRECCIONAL"

    if any(phrase in lower_text for phrase in VALID_DIRECTIONAL_PHRASES):
        return "DIRECCIONAL_VALIDO"

    if lower_words[0] in VALID_DIRECTIONAL_PREFIXES:
        return "DIRECCIONAL_VALIDO"
    if lower_words[0].isdigit() or lower_words[0] in NUMBER_WORD_PREFIXES:
        return "DIRECCIONAL_VALIDO"
    if len(lower_words) >= 2 and lower_words[-2] in DIRECTIONAL_WORDS and lower_words[-1].isdigit():
        return "DIRECCIONAL_VALIDO"
    if lower_words[-1] in DIRECTIONAL_WORDS:
        return "DIRECCIONAL_VALIDO"
    return "DIRECCIONAL_REVISAR"


def build_quality_report(summary_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    issues: list[dict] = []
    token_counter: Counter[str] = Counter()

    for row in summary_rows:
        direccion = _clean_text(row.get("direccion", ""))
        numero = _number_text(row.get("numero", ""))
        comuna = _clean_text(row.get("comuna", ""))
        ciudad = _clean_text(row.get("ciudad", ""))
        region = _clean_text(row.get("region", ""))

        normalized_direccion = _normalize_text(direccion)
        normalized_comuna = _normalize_text(comuna)
        normalized_ciudad = _normalize_text(ciudad)

        for token in direccion.split():
            token_counter[token.lower()] += 1

        if not direccion and (numero or comuna or ciudad):
            issues.append(
                _build_issue(
                    row,
                    "DIRECCION_VACIA_CON_DATOS",
                    "alta",
                    "Revisar fuente original y priorizar otra variante del mismo RUT+DV.",
                )
            )

        if GLUED_TOKEN_PATTERN.search(direccion):
            issues.append(
                _build_issue(
                    row,
                    "TOKENS_PEGADOS",
                    "alta",
                    "Separar palabras y numeros pegados con reglas o IA textual.",
                )
            )

        if _has_complex_glued_word(direccion):
            issues.append(
                _build_issue(
                    row,
                    "PALABRA_PEGADA_REVISAR",
                    "alta",
                    "Revisar y separar palabras pegadas complejas con reglas o IA textual.",
                )
            )

        if _has_repeated_fragment(direccion):
            issues.append(
                _build_issue(
                    row,
                    "REPETICION_PEGADA",
                    "alta",
                    "Detectar y limpiar repeticiones pegadas o duplicadas dentro de la direccion.",
                )
            )

        if numero and re.search(rf"(^|\s){re.escape(numero)}($|\s)", direccion, flags=re.IGNORECASE):
            issues.append(
                _build_issue(
                    row,
                    "NUMERO_DUPLICADO_EN_DIRECCION",
                    "media",
                    "Quitar el numero del texto de direccion cuando ya existe en columna numero.",
                )
            )

        if re.search(r"\bnumero\b", direccion, flags=re.IGNORECASE):
            issues.append(
                _build_issue(
                    row,
                    "TOKEN_NUMERO_LITERAL",
                    "media",
                    "Quitar la palabra numero cuando funcione como ruido textual.",
                )
            )

        if TRAILING_V_PATTERN.search(direccion):
            issues.append(
                _build_issue(
                    row,
                    "TOKEN_V_FINAL",
                    "media",
                    "Eliminar V final aislada o asociada a un numero cuando no aporta direccion.",
                )
            )

        if re.search(r"(?:^|\s)0(?:$|\s)", direccion):
            issues.append(
                _build_issue(
                    row,
                    "TOKEN_CERO_AISLADO",
                    "media",
                    "Revisar cero aislado dentro de la direccion y limpiar si corresponde a ruido.",
                )
            )

        directional_class = _classify_directional_suffix(direccion, comuna, ciudad)
        if directional_class == "RESIDUO_TERRITORIAL_DIRECCIONAL":
            issues.append(
                _build_issue(
                    row,
                    "RESIDUO_TERRITORIAL_DIRECCIONAL",
                    "media",
                    "Quitar bloque territorial final solo si coincide con comuna o ciudad ya confiable.",
                )
            )
        elif directional_class == "DIRECCIONAL_REVISAR":
            issues.append(
                _build_issue(
                    row,
                    "DIRECCIONAL_REVISAR",
                    "media",
                    "Revisar sufijo direccional final para confirmar si es parte real de la direccion.",
                )
            )

        if SUSPICIOUS_TOKEN_PATTERN.search(direccion):
            issues.append(
                _build_issue(
                    row,
                    "TOKEN_SOSPECHOSO",
                    "media",
                    "Aplicar limpieza adicional de ruido textual.",
                )
            )

        if direccion and len(direccion.split()) <= 1:
            if _is_short_address_valid(direccion, numero, comuna, ciudad):
                issues.append(
                    _build_issue(
                        row,
                        "DIRECCION_CORTA_VALIDA",
                        "baja",
                        "Direccion breve pero consistente con numero o territorio confiable.",
                    )
                )
            else:
                issues.append(
                    _build_issue(
                        row,
                        "DIRECCION_CORTA_REVISAR",
                        "media",
                        "Validar si la direccion necesita complemento o corresponde a una calle incompleta.",
                    )
                )

        if comuna and normalized_comuna and f" {normalized_comuna} " in f" {normalized_direccion} ":
            issues.append(
                _build_issue(
                    row,
                    "COMUNA_DENTRO_DIRECCION",
                    "media",
                    "Eliminar comuna incrustada del texto si corresponde al dato territorial.",
                )
            )

        if ciudad and normalized_ciudad and f" {normalized_ciudad} " in f" {normalized_direccion} ":
            issues.append(
                _build_issue(
                    row,
                    "CIUDAD_DENTRO_DIRECCION",
                    "media",
                    "Eliminar ciudad incrustada del texto si corresponde al dato territorial.",
                )
            )

        if not comuna:
            issues.append(
                _build_issue(
                    row,
                    "COMUNA_FALTANTE",
                    "baja",
                    "Mantener vacio o revisar manualmente otra variante del mismo RUT+DV.",
                )
            )

        if not ciudad:
            issues.append(
                _build_issue(
                    row,
                    "CIUDAD_FALTANTE",
                    "baja",
                    "Mantener vacio o revisar manualmente otra variante del mismo RUT+DV.",
                )
            )

        if comuna and not region:
            issues.append(
                _build_issue(
                    row,
                    "REGION_FALTANTE_CON_COMUNA",
                    "media",
                    "Verificar derivacion territorial desde comuna valida.",
                )
            )

    metrics_counter = Counter(issue["problema_detectado"] for issue in issues)
    metrics = [
        {"metrica": "FILAS_RESUMEN", "valor": len(summary_rows)},
        {"metrica": "FILAS_CON_ALERTA", "valor": len({issue['RUT+DV'] + '|' + str(issue['direccion']) for issue in issues})},
        {"metrica": "TOP_TOKEN_1", "valor": f"{token_counter.most_common(1)[0][0]} ({token_counter.most_common(1)[0][1]})" if token_counter else ""},
    ]

    for problema, count in sorted(metrics_counter.items()):
        metrics.append({"metrica": problema, "valor": count})

    for token, count in token_counter.most_common(10):
        metrics.append({"metrica": f"TOKEN_{token}", "valor": count})

    return issues, metrics
