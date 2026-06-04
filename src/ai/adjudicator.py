from __future__ import annotations

import json
import re

from ai.ollama_client import OllamaClient
from catalog.chile_geo import ChileGeoResolver, normalize_text


SYSTEM_PROMPT = """
Eres un asistente experto en limpieza de direcciones chilenas.
Tu tarea es mejorar solo el texto de la direccion.
Reglas:
1) No inventes datos que no esten en la entrada.
2) Si no puedes inferir algo con alta certeza, dejalo vacio.
3) No completes numero, comuna, ciudad ni region.
4) No uses palabras de la direccion para llenar campos territoriales.
5) Si numero_actual viene informado, elimina ese mismo numero desde direccion_refinada.
6) Si numero_actual viene vacio, no propongas numero.
7) Si comuna/ciudad/region vienen vacias, dejalas vacias.
8) Corrige espacios, palabras pegadas, ruido y duplicaciones.
9) No agregues explicaciones fuera del JSON.
10) Devuelve SOLO JSON valido con la estructura exacta indicada.
""".strip()


def _extract_json_object(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _has_suspicious_concatenation(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"[a-z]{4,}\d{2,}", lowered):
        return True
    return any(token in lowered for token in ["animaslas", "mistrallas", "torreconcepcion", "manantialesvaldivia", "andeslos", "dechile", "sabellaantofagasta", "estrellapudahuel"])


def _has_repeated_text(text: str) -> bool:
    lowered = str(text or "").lower()
    compact = lowered.replace(" ", "")
    return bool(re.search(r"([a-z]{3,})\1", compact)) or bool(re.search(r"([a-z]{3,})\s+\1", lowered))


def _is_weak_short_address(record: dict) -> bool:
    direccion_base = str(record.get("direccion_base", "")).strip()
    if not direccion_base:
        return False
    if len(direccion_base.split()) != 1:
        return False
    if str(record.get("numero_final", "")).strip():
        return False
    if str(record.get("comuna_resuelta", "")).strip():
        return False
    if str(record.get("ciudad_resuelta", "")).strip() or str(record.get("ciudad_original", "")).strip():
        return False
    return True


def _pre_sanitize_address_base(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""

    value = re.sub(r"([a-zA-Z])([0-9])", r"\1 \2", value)
    value = re.sub(r"([0-9])([a-zA-Z])", r"\1 \2", value)
    value = re.sub(r"\bnumero\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _quality_penalty(text: str) -> int:
    value = _pre_sanitize_address_base(text)
    if not value:
        return 10

    penalty = 0
    if _has_suspicious_concatenation(value):
        penalty += 3
    if _has_repeated_text(value):
        penalty += 3
    if re.search(r"[a-z]{2,}\d{2,}[a-z0-9]+", value.lower()):
        penalty += 2
    if re.search(r"\b\w+\d+\b", value.lower()):
        penalty += 1
    if len(value.split()) == 1 and len(value) <= 8:
        penalty += 1
    return penalty


def _is_better_address(before: str, after: str) -> bool:
    before_clean = _pre_sanitize_address_base(before)
    after_clean = _pre_sanitize_address_base(after)
    if not after_clean:
        return False

    before_penalty = _quality_penalty(before_clean)
    after_penalty = _quality_penalty(after_clean)
    if after_penalty < before_penalty:
        return True
    if after_penalty > before_penalty:
        return False

    if len(after_clean) < max(4, len(before_clean) - 8):
        return False
    if after_clean == before_clean:
        return False
    return len(after_clean.split()) >= len(before_clean.split())


def _should_refine_record(record: dict, ambiguous_keys: set[tuple[str, str]]) -> bool:
    direccion_base = str(record.get("direccion_base", ""))
    has_glued_text = _has_suspicious_concatenation(direccion_base)
    has_repeated_text = _has_repeated_text(direccion_base)
    if has_glued_text or has_repeated_text:
        return True

    return False


def _build_user_prompt(record: dict) -> str:
    return (
        "Depura esta direccion chilena y responde en JSON con esta estructura exacta:\n"
        "{\n"
        '  "direccion_refinada": "...",\n'
        '  "confianza": "alta|media|baja",\n'
        '  "motivo": "..."\n'
        "}\n\n"
        f"rut: {record.get('rut', '')}\n"
        f"dv: {record.get('dv', '')}\n"
        f"nombre: {record.get('nombre', '')}\n"
        f"direccion_original: {record.get('direccion_original', '')}\n"
        f"direccion_limpia: {record.get('direccion_limpia', '')}\n"
        f"direccion_base_actual: {record.get('direccion_base', '')}\n"
        f"numero_actual: {record.get('numero_final', '')}\n"
        f"comuna_actual: {record.get('comuna_resuelta', '')}\n"
        f"ciudad_actual: {record.get('ciudad_resuelta', '')}\n"
        f"region_actual: {record.get('region_resuelta', '')}\n"
        f"comuna_original_columna: {record.get('comuna_original', '')}\n"
        f"ciudad_original_columna: {record.get('ciudad_original', '')}\n"
    )


def _compute_ambiguous_keys(results: list[dict], score_gap: int = 5) -> set[tuple[str, str]]:
    grouped: dict[tuple[str, str], list[int]] = {}
    for row in results:
        key = (str(row.get("rut", "")).strip(), str(row.get("dv", "")).strip().upper())
        if not key[0] or not key[1]:
            continue
        grouped.setdefault(key, []).append(int(row.get("score", 0)))

    ambiguous: set[tuple[str, str]] = set()
    for key, scores in grouped.items():
        if len(scores) < 2:
            continue
        ordered = sorted(scores, reverse=True)
        if ordered[0] - ordered[1] <= score_gap:
            ambiguous.add(key)
    return ambiguous


def apply_ai_refinement(results: list[dict], geo_resolver: ChileGeoResolver, client: OllamaClient) -> list[dict]:
    ambiguous_keys = _compute_ambiguous_keys(results)
    refined_results: list[dict] = []

    for record in results:
        enriched = dict(record)
        enriched["direccion_base"] = _pre_sanitize_address_base(enriched.get("direccion_base", ""))
        enriched.setdefault("ia_aplicada", False)
        enriched.setdefault("ia_confianza", "")
        enriched.setdefault("ia_motivo", "")
        enriched.setdefault("direccion_pre_ia", enriched.get("direccion_base", ""))
        enriched.setdefault("direccion_post_ia", enriched.get("direccion_base", ""))

        if not _should_refine_record(enriched, ambiguous_keys):
            refined_results.append(enriched)
            continue

        try:
            raw_reply = client.chat(SYSTEM_PROMPT, _build_user_prompt(enriched))
            payload = _extract_json_object(raw_reply)
            if not payload:
                enriched["ia_motivo"] = "JSON invalido"
                refined_results.append(enriched)
                continue

            confidence = str(payload.get("confianza", "")).strip().lower()
            direccion_refinada = str(payload.get("direccion_refinada", "")).strip()
            motivo = str(payload.get("motivo", "")).strip()

            if confidence != "alta":
                enriched["ia_confianza"] = confidence
                enriched["ia_motivo"] = motivo or "Confianza no alta"
                refined_results.append(enriched)
                continue

            if direccion_refinada and _is_better_address(enriched.get("direccion_base", ""), direccion_refinada):
                enriched["direccion_base"] = direccion_refinada
                enriched["direccion_post_ia"] = direccion_refinada
                enriched["ia_aplicada"] = True
                enriched["ia_confianza"] = confidence
                enriched["ia_motivo"] = motivo or "Mejora textual validada"
            else:
                enriched["ia_confianza"] = confidence
                enriched["ia_motivo"] = "Cambio IA rechazado por no mejorar la calidad del texto"

        except Exception as exc:  # noqa: BLE001
            enriched["ia_motivo"] = f"Error IA: {exc}"

        refined_results.append(enriched)

    return refined_results


def apply_ai_refinement_limited(
    results: list[dict],
    geo_resolver: ChileGeoResolver,
    client: OllamaClient,
    max_cases: int,
) -> list[dict]:
    if max_cases <= 0:
        return apply_ai_refinement(results, geo_resolver, client)

    ambiguous_keys = _compute_ambiguous_keys(results)
    prepared = []
    for record in results:
        score = 1 if _should_refine_record(record, ambiguous_keys) else 0
        prepared.append((score, record))

    prepared.sort(key=lambda item: item[0], reverse=True)
    selected_ids = {id(item[1]) for item in prepared[:max_cases] if item[0] == 1}

    subset = [row for row in results if id(row) in selected_ids]
    refined_subset = apply_ai_refinement(subset, geo_resolver, client)
    refined_map = {id(orig): refined for orig, refined in zip(subset, refined_subset)}

    output: list[dict] = []
    for row in results:
        output.append(refined_map.get(id(row), dict(row)))
    return output
