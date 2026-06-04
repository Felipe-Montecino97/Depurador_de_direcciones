import argparse
from pathlib import Path

from ai.adjudicator import apply_ai_refinement_limited
from ai.ollama_client import OllamaClient
from catalog.chile_geo import ChileGeoResolver, find_column
from config.settings import AISettings
from normalization.cleaner import clean_address
from dataio.exporter import export_results
from dataio.loader import load_addresses
from scoring.scorer import score_address
from dedup.deduplicator import find_duplicates
from parsing.address_parser import parse_address_components
from consolidation.consolidator import build_summary_rows
from quality.audit import build_quality_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Depurador de direcciones offline")
    parser.add_argument("--input", required=True, help="Ruta del archivo CSV o Excel")
    parser.add_argument("--output", default="data/output/resultado_depurado.xlsx", help="Ruta de salida Excel")
    parser.add_argument("--column", default=None, help="Nombre de la columna de direcciones")
    parser.add_argument("--threshold", type=int, default=88, help="Umbral para duplicados similares")
    parser.add_argument("--disable-ai", action="store_true", help="Desactiva refinamiento con IA")
    parser.add_argument("--ai-url", default="http://192.168.1.7:11434/api/chat", help="Endpoint /api/chat de Ollama")
    parser.add_argument("--ai-model", default="gemma4:e2b", help="Modelo de Ollama")
    parser.add_argument("--ai-timeout", type=int, default=60, help="Timeout en segundos para IA")
    parser.add_argument("--ai-retries", type=int, default=2, help="Reintentos de llamada IA")
    parser.add_argument("--ai-max-cases", type=int, default=0, help="Maximo de filas a refinar con IA (0 = sin limite)")
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    ai_settings = AISettings(
        enabled=not args.disable_ai,
        url=args.ai_url,
        model=args.ai_model,
        timeout=args.ai_timeout,
        retries=args.ai_retries,
        max_cases=args.ai_max_cases,
    )

    df, address_column = load_addresses(args.input, args.column)

    master_catalog = Path("Maestro/output/maestro_territorial_chile.csv")
    alias_catalog = Path("Maestro/output/alias_territorial_chile.csv")
    geo_resolver = None
    if master_catalog.exists():
        geo_resolver = ChileGeoResolver.from_paths(master_catalog, alias_catalog)

    comuna_column = find_column(list(df.columns), ["COMUNA"])
    ciudad_column = find_column(list(df.columns), ["CIUDAD"])
    region_column = find_column(list(df.columns), ["REGION", "REGIÓN"])
    numero_column = find_column(list(df.columns), ["NUMERO", "NRO", "NÚMERO"])
    rut_column = find_column(list(df.columns), ["RUT"])
    dv_column = find_column(list(df.columns), ["DV"])
    nombre_column = find_column(list(df.columns), ["NOMBRE", "NOMBRE COMPLETO"])

    results = []
    cleaned_addresses = []

    def _clean_location_value(value: str) -> str:
        text = str(value or "").strip()
        if not text or text.lower() == "nan" or text == "0":
            return ""
        return text

    for row_index, original_value in enumerate(df[address_column].fillna(""), start=1):
        original = str(original_value)
        cleaned = clean_address(original)
        scored = score_address(cleaned)

        comuna_raw = _clean_location_value(df.iloc[row_index - 1][comuna_column]) if comuna_column else ""
        ciudad_raw = _clean_location_value(df.iloc[row_index - 1][ciudad_column]) if ciudad_column else ""
        region_raw = _clean_location_value(df.iloc[row_index - 1][region_column]) if region_column else ""
        numero_raw = str(df.iloc[row_index - 1][numero_column]) if numero_column else ""
        rut_raw = str(df.iloc[row_index - 1][rut_column]) if rut_column else ""
        dv_raw = str(df.iloc[row_index - 1][dv_column]) if dv_column else ""
        nombre_raw = str(df.iloc[row_index - 1][nombre_column]) if nombre_column else ""
        parsed_address = parse_address_components(cleaned, numero_raw)

        if geo_resolver is None:
            territorial = {
                "comuna": "",
                "region": "",
                "estado_territorial": "SIN_CATALOGO_TERRITORIAL",
                "origen_comuna": "",
                "fuente_territorial": "",
            }
        else:
            territorial = geo_resolver.resolve(
                comuna_raw=comuna_raw,
                ciudad_raw=ciudad_raw,
                region_raw=region_raw,
                direccion_raw=cleaned,
            )

        cleaned_addresses.append(cleaned)
        results.append(
            {
                "row": row_index,
                "direccion_original": original,
                "direccion_limpia": cleaned,
                "rut": rut_raw,
                "dv": dv_raw,
                "nombre": nombre_raw,
                "ciudad_original": ciudad_raw,
                "ciudad_resuelta": ciudad_raw,
                "comuna_original": comuna_raw,
                "direccion_base": parsed_address["direccion_base"],
                "numero_final": parsed_address["numero_final"],
                "detalle_direccion": parsed_address["detalle_direccion"],
                "score": scored["score"],
                "estado": scored["status"],
                "razones": " | ".join(scored["reasons"]),
                "analisis_tokens": " | ".join(
                    f"{item['token']}:{item['points']}({item['category']})"
                    for item in scored["token_analysis"]
                ),
                "comuna_resuelta": territorial["comuna"],
                "region_resuelta": territorial["region"],
                "estado_territorial": territorial["estado_territorial"],
                "origen_comuna": territorial["origen_comuna"],
                "fuente_territorial": territorial["fuente_territorial"],
                "ia_aplicada": False,
                "ia_confianza": "",
                "ia_motivo": "",
                "direccion_pre_ia": parsed_address["direccion_base"],
                "direccion_post_ia": parsed_address["direccion_base"],
            }
        )

    if ai_settings.enabled and geo_resolver is not None:
        ollama_client = OllamaClient(
            url=ai_settings.url,
            model=ai_settings.model,
            timeout=ai_settings.timeout,
            retries=ai_settings.retries,
        )
        results = apply_ai_refinement_limited(
            results=results,
            geo_resolver=geo_resolver,
            client=ollama_client,
            max_cases=ai_settings.max_cases,
        )

    duplicates = find_duplicates(cleaned_addresses, threshold=args.threshold)
    summary = build_summary_rows(results, similarity_threshold=args.threshold)
    quality_rows, quality_metrics = build_quality_report(summary)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_results(summary, results, duplicates, str(output_path), quality_rows=quality_rows, quality_metrics=quality_metrics)

    print("Proceso completado")
    print(f"Archivo procesado: {args.input}")
    print(f"Columna usada: {address_column}")
    print(f"Filas analizadas: {len(results)}")
    print(f"Filas resumen: {len(summary)}")
    print(f"Alertas calidad: {len(quality_rows)}")
    print(f"IA activa: {'si' if ai_settings.enabled else 'no'}")
    if ai_settings.enabled:
        print(f"IA max casos: {ai_settings.max_cases}")
    print(f"Duplicados exactos: {len(duplicates['exact'])}")
    print(f"Duplicados similares: {len(duplicates['similar'])}")
    print(f"Exportado en: {output_path}")


if __name__ == "__main__":
    main()
