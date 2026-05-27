import argparse
from pathlib import Path

from catalog.chile_geo import ChileGeoResolver, find_column
from normalization.cleaner import clean_address
from dataio.exporter import export_results
from dataio.loader import load_addresses
from scoring.scorer import score_address
from dedup.deduplicator import find_duplicates


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Depurador de direcciones offline")
    parser.add_argument("--input", required=True, help="Ruta del archivo CSV o Excel")
    parser.add_argument("--output", default="data/output/resultado_depurado.xlsx", help="Ruta de salida Excel")
    parser.add_argument("--column", default=None, help="Nombre de la columna de direcciones")
    parser.add_argument("--threshold", type=int, default=88, help="Umbral para duplicados similares")
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    df, address_column = load_addresses(args.input, args.column)

    master_catalog = Path("Maestro/output/maestro_territorial_chile.csv")
    alias_catalog = Path("Maestro/output/alias_territorial_chile.csv")
    geo_resolver = None
    if master_catalog.exists():
        geo_resolver = ChileGeoResolver.from_paths(master_catalog, alias_catalog)

    comuna_column = find_column(list(df.columns), ["COMUNA"])
    ciudad_column = find_column(list(df.columns), ["CIUDAD"])
    region_column = find_column(list(df.columns), ["REGION", "REGIÓN"])

    results = []
    cleaned_addresses = []

    for row_index, original_value in enumerate(df[address_column].fillna(""), start=1):
        original = str(original_value)
        cleaned = clean_address(original)
        scored = score_address(cleaned)

        comuna_raw = str(df.iloc[row_index - 1][comuna_column]) if comuna_column else ""
        ciudad_raw = str(df.iloc[row_index - 1][ciudad_column]) if ciudad_column else ""
        region_raw = str(df.iloc[row_index - 1][region_column]) if region_column else ""

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
            }
        )

    duplicates = find_duplicates(cleaned_addresses, threshold=args.threshold)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_results(results, duplicates, str(output_path))

    print("Proceso completado")
    print(f"Archivo procesado: {args.input}")
    print(f"Columna usada: {address_column}")
    print(f"Filas analizadas: {len(results)}")
    print(f"Duplicados exactos: {len(duplicates['exact'])}")
    print(f"Duplicados similares: {len(duplicates['similar'])}")
    print(f"Exportado en: {output_path}")


if __name__ == "__main__":
    main()
