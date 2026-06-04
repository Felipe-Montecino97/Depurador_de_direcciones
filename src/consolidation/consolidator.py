from __future__ import annotations

import csv
import unicodedata
import re
from typing import Any
from pathlib import Path

from rapidfuzz import fuzz


MASTER_CATALOG_PATH = Path("Maestro/output/maestro_territorial_chile.csv")


def _to_title_case(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    return " ".join(word.capitalize() for word in value.split())


def _normalize_text(text: str) -> str:
    value = str(text or "").strip()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    return " ".join(value.upper().split())


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


def _clean_number(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _completeness_score(row: dict) -> int:
    points = 0
    if row.get("direccion_base"):
        points += 2
    if row.get("numero_final"):
        points += 2
    if row.get("comuna_resuelta"):
        points += 1
    if row.get("region_resuelta"):
        points += 1
    if row.get("detalle_direccion"):
        points += 1
    base = str(row.get("direccion_base", "")).strip()
    if base:
        token_count = len(base.split())
        if token_count >= 2:
            points += 1
        if token_count == 1 and not row.get("numero_final") and not row.get("comuna_resuelta") and not row.get("ciudad_resuelta"):
            points -= 2
    return points


def _has_valid_base(row: dict) -> bool:
    base = str(row.get("direccion_base", "")).strip()
    return bool(base and base.lower() != "nan")


def _trusted_territorial_origin(row: dict) -> int:
    source = str(row.get("origen_comuna", "")).strip().upper()
    if source == "COMUNA":
        return 2
    if source == "CIUDAD":
        return 1
    return 0


def _build_group_key(row: dict) -> tuple[str, str]:
    rut = str(row.get("rut", "")).strip()
    dv = str(row.get("dv", "")).strip().upper()
    return rut, dv


def _sanitize_summary_direction(row: dict) -> str:
    direccion = str(row.get("direccion_base", "")).strip()
    if not direccion:
        return ""

    normalized_tokens = direccion.split()
    numero = _clean_number(row.get("numero_final", ""))
    comuna = str(row.get("comuna_resuelta", "")).strip()
    ciudad = str(row.get("ciudad_resuelta", "")).strip() or str(row.get("ciudad_original", "")).strip()

    filtered_tokens: list[str] = []
    for token in normalized_tokens:
        if numero and token.lower() == numero.lower():
            continue
        if token.lower() == "numero":
            continue
        if token.lower() in {"sn", "s/n"}:
            continue
        filtered_tokens.append(token)

    result = " ".join(filtered_tokens).strip()
    if not result:
        return ""

    result = result.strip()
    result = result.removesuffix(" v").strip()
    result = " ".join(result.split())
    result = re.sub(r"(?:^|\s)0(?:$|\s)", " ", result)
    result = " ".join(result.split())

    def strip_phrase(text: str, phrase: str) -> str:
        if not phrase:
            return text
        phrase_norm = _normalize_text(phrase)
        text_norm = _normalize_text(text)
        if not phrase_norm:
            return text
        pattern = f" {phrase_norm} "
        if pattern in f" {text_norm} ":
            original_words = text.split()
            phrase_words = phrase.split()
            lowered_phrase = [word.lower() for word in phrase_words]
            lowered_original = [word.lower() for word in original_words]
            kept: list[str] = []
            i = 0
            while i < len(original_words):
                window = lowered_original[i : i + len(lowered_phrase)]
                if lowered_phrase and window == lowered_phrase:
                    i += len(lowered_phrase)
                    continue
                kept.append(original_words[i])
                i += 1
            return " ".join(kept).strip()
        return text

    result = strip_phrase(result, comuna)
    result = strip_phrase(result, ciudad)

    trusted_places = [comuna, ciudad]
    for place in trusted_places:
        if not place:
            continue
        place_norm = _normalize_text(place)
        if not place_norm:
            continue
        match = re.search(
            rf"\b{re.escape(place_norm)}\s+(SUR|NORTE|ORIENTE|PONIENTE)\s+\d+$",
            _normalize_text(result),
        )
        if match:
            words = result.split()
            place_words = place.split()
            if len(words) >= len(place_words) + 2:
                result = " ".join(words[: -(len(place_words) + 2)]).strip()
                break

    normalized_result = _normalize_text(result)
    for place in CATALOG_PLACES:
        match = re.search(
            rf"\b{re.escape(place)}\s+(SUR|NORTE|ORIENTE|PONIENTE)\s+\d+$",
            normalized_result,
        )
        if not match:
            continue

        original_words = result.split()
        place_words = place.split()
        if len(original_words) < len(place_words) + 2:
            continue

        tail_words = _normalize_text(" ".join(original_words[-(len(place_words) + 2) :])).split()
        expected_tail = place.split() + [match.group(1), _normalize_text(original_words[-1])]
        if tail_words != expected_tail:
            continue

        kept_words = original_words[: -(len(place_words) + 2)]
        if len(kept_words) < 2:
            continue

        result = " ".join(kept_words).strip()
        break

    result = " ".join(result.split()).strip()
    return result


def _address_signature(row: dict) -> str:
    base = str(row.get("direccion_base", "")).strip().lower()
    number = _clean_number(row.get("numero_final", "")).lower()
    if number:
        return f"{base} {number}".strip()
    return base


def _is_similar_address(row_a: dict, row_b: dict, threshold: int = 90) -> bool:
    sig_a = _address_signature(row_a)
    sig_b = _address_signature(row_b)
    if not sig_a or not sig_b:
        return False

    number_a = _clean_number(row_a.get("numero_final", "")).lower()
    number_b = _clean_number(row_b.get("numero_final", "")).lower()
    if number_a and number_b and number_a == number_b:
        if sig_a in sig_b or sig_b in sig_a:
            return True

    score = max(
        fuzz.token_sort_ratio(sig_a, sig_b),
        fuzz.token_set_ratio(sig_a, sig_b),
        fuzz.partial_ratio(sig_a, sig_b),
    )
    return score >= threshold


def _choose_winner(rows: list[dict]) -> dict:
    ordered = sorted(
        rows,
        key=lambda item: (
            _trusted_territorial_origin(item),
            int(item.get("score", 0)),
            _completeness_score(item),
        ),
        reverse=True,
    )
    return ordered[0]


def _cluster_rows(rows: list[dict], threshold: int = 90) -> list[list[dict]]:
    clusters: list[list[dict]] = []
    candidates = [row for row in rows if _has_valid_base(row)]
    if not candidates:
        candidates = rows

    for row in candidates:
        assigned = False
        for cluster in clusters:
            representative = _choose_winner(cluster)
            if _is_similar_address(row, representative, threshold=threshold):
                cluster.append(row)
                assigned = True
                break
        if not assigned:
            clusters.append([row])
    return clusters


def build_summary_rows(results: list[dict], similarity_threshold: int = 90) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in results:
        key = _build_group_key(row)
        if not key[0] or not key[1]:
            continue
        grouped.setdefault(key, []).append(row)

    summary: list[dict] = []
    for (rut, dv), rows in grouped.items():
        clusters = _cluster_rows(rows, threshold=similarity_threshold)
        winners = [_choose_winner(cluster) for cluster in clusters]
        winners = sorted(
            winners,
            key=lambda item: (
                _trusted_territorial_origin(item),
                int(item.get("score", 0)),
                _completeness_score(item),
            ),
            reverse=True,
        )

        for winner in winners:
            summary.append(
                {
                    "RUT": rut,
                    "DV": dv,
                    "RUT+DV": f"{rut}-{dv}",
                    "NOMBRE": str(winner.get("nombre", "")).strip(),
                    "direccion": _to_title_case(_sanitize_summary_direction(winner)),
                    "numero": _clean_number(winner.get("numero_final", "")),
                    "comuna": str(winner.get("comuna_resuelta", "")).strip(),
                    "ciudad": str(winner.get("ciudad_resuelta", "")).strip() or str(winner.get("ciudad_original", "")).strip(),
                    "region": str(winner.get("region_resuelta", "")).strip(),
                }
            )

    summary.sort(key=lambda item: item["RUT+DV"])
    return summary
