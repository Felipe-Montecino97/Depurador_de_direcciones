from __future__ import annotations

import argparse
import unicodedata
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


DEFAULT_BASE_DIR = Path("Maestro")


def _normalize_text(value: str) -> str:
    text = str(value).strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.upper().split())


def _pick_column(columns: list[str], candidates: list[str]) -> str | None:
    lookup = {col.lower(): col for col in columns}
    for candidate in candidates:
        selected = lookup.get(candidate.lower())
        if selected:
            return selected
    return None


def _first_shp(folder: Path) -> Path:
    shp_files = list(folder.rglob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"No se encontro archivo .shp en {folder}")
    return shp_files[0]


def _extract_if_needed(zip_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    if any(target_dir.rglob("*.shp")):
        return

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(target_dir)


def _resolve_zip_path(base_dir: Path, expected_name: str) -> Path:
    candidates = [
        base_dir / "raw" / expected_name,
        base_dir / "Catalogo" / expected_name,
        base_dir / expected_name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"No se encontro {expected_name}. Busque en: "
        + ", ".join(str(path) for path in candidates)
    )


def build_catalog(base_dir: Path) -> tuple[Path, Path, int]:
    raw_dir = base_dir / "raw"
    work_dir = base_dir / "work"
    output_dir = base_dir / "output"
    docs_dir = base_dir / "docs"

    raw_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    comunas_zip = _resolve_zip_path(base_dir, "Comunas.zip")
    regiones_zip = _resolve_zip_path(base_dir, "Regiones.zip")

    comunas_extract = work_dir / "comunas"
    regiones_extract = work_dir / "regiones"

    _extract_if_needed(comunas_zip, comunas_extract)
    _extract_if_needed(regiones_zip, regiones_extract)

    comunas = gpd.read_file(_first_shp(comunas_extract))
    regiones = gpd.read_file(_first_shp(regiones_extract))

    comuna_name_col = _pick_column(list(comunas.columns), ["COMUNA", "NOM_COMUNA", "NOM_COM", "NOMBRE"])
    comuna_code_col = _pick_column(list(comunas.columns), ["COD_COMUNA", "COD_COM", "CUT_COM", "CODIGO", "ID", "CODCOMUNA"])
    provincia_name_col = _pick_column(list(comunas.columns), ["PROVINCIA", "NOM_PROV", "NOMBRE_PROV"])
    provincia_code_col = _pick_column(list(comunas.columns), ["COD_PROV", "CUT_PROV", "COD_PROVINCIA", "CODPROV"])
    region_name_col_com = _pick_column(list(comunas.columns), ["REGION", "NOM_REGION", "NOMBRE_REG", "REGIÓN"])
    region_code_col_com = _pick_column(list(comunas.columns), ["COD_REGION", "CUT_REG", "COD_REG", "CODREGION"])

    region_name_col_reg = _pick_column(list(regiones.columns), ["REGION", "NOM_REGION", "NOMBRE", "REGIÓN"])
    region_code_col_reg = _pick_column(list(regiones.columns), ["COD_REGION", "CUT_REG", "COD_REG", "CODREGION", "ID"])

    if comuna_name_col is None:
        raise ValueError("No se detecto columna de nombre de comuna en la capa comunal")

    if region_name_col_com is None and region_name_col_reg is None:
        raise ValueError("No se detecto columna de nombre de region en las capas")

    if region_name_col_com is not None:
        catalog = pd.DataFrame(
            {
                "codigo_region": comunas[region_code_col_com] if region_code_col_com else None,
                "nombre_region": comunas[region_name_col_com],
                "codigo_provincia": comunas[provincia_code_col] if provincia_code_col else None,
                "nombre_provincia": comunas[provincia_name_col] if provincia_name_col else None,
                "codigo_comuna": comunas[comuna_code_col] if comuna_code_col else None,
                "nombre_comuna": comunas[comuna_name_col],
            }
        )
    else:
        comunas = comunas.to_crs(regiones.crs)
        comunas_points = comunas.copy()
        comunas_points["geometry"] = comunas_points.geometry.representative_point()

        left_cols = [comuna_name_col, "geometry"]
        if comuna_code_col:
            left_cols.append(comuna_code_col)

        right_cols = [region_name_col_reg, "geometry"]
        if region_code_col_reg:
            right_cols.append(region_code_col_reg)

        joined = gpd.sjoin(
            comunas_points[left_cols],
            regiones[right_cols],
            how="left",
            predicate="within",
        )

        catalog = pd.DataFrame(
            {
                "codigo_region": joined[region_code_col_reg] if region_code_col_reg else None,
                "nombre_region": joined[region_name_col_reg],
                "codigo_provincia": None,
                "nombre_provincia": None,
                "codigo_comuna": joined[comuna_code_col] if comuna_code_col else None,
                "nombre_comuna": joined[comuna_name_col],
            }
        )

    catalog["nombre_region"] = catalog["nombre_region"].astype(str).str.strip()
    catalog["nombre_comuna"] = catalog["nombre_comuna"].astype(str).str.strip()
    catalog["region_normalizada"] = catalog["nombre_region"].apply(_normalize_text)
    catalog["comuna_normalizada"] = catalog["nombre_comuna"].apply(_normalize_text)
    catalog["fuente"] = "BCN-SIIT"
    catalog["fecha_extraccion"] = pd.Timestamp.today().date().isoformat()
    catalog["vigente"] = True

    catalog = (
        catalog.drop_duplicates(subset=["region_normalizada", "comuna_normalizada"])
        .sort_values(["nombre_region", "nombre_comuna"])
        .reset_index(drop=True)
    )

    master_path = output_dir / "maestro_territorial_chile.csv"
    catalog.to_csv(master_path, index=False, encoding="utf-8-sig")

    alias_df = pd.DataFrame(
        [
            {"tipo": "region", "alias": "RM", "valor_oficial": "Region Metropolitana de Santiago"},
            {"tipo": "region", "alias": "METROPOLITANA", "valor_oficial": "Region Metropolitana de Santiago"},
            {"tipo": "comuna", "alias": "NUNOA", "valor_oficial": "Nunoa"},
            {"tipo": "comuna", "alias": "ESTACION CENTRAL", "valor_oficial": "Estacion Central"},
            {"tipo": "comuna", "alias": "AYSEN", "valor_oficial": "Aysen"},
            {"tipo": "comuna", "alias": "COIHAIQUE", "valor_oficial": "Coyhaique"},
        ]
    )
    alias_path = output_dir / "alias_territorial_chile.csv"
    alias_df.to_csv(alias_path, index=False, encoding="utf-8-sig")

    source_note = docs_dir / "fuente_bcn.md"
    source_note.write_text(
        "# Fuente del catalogo territorial\n\n"
        "- Fuente: Biblioteca del Congreso Nacional de Chile (BCN-SIIT).\n"
        "- Capas: Division comunal y Division regional.\n"
        "- Uso: referencial para validacion territorial comuna-region.\n"
        f"- Fecha de extraccion: {pd.Timestamp.today().date().isoformat()}\n",
        encoding="utf-8",
    )

    return master_path, alias_path, len(catalog)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Genera catalogos territoriales de Chile desde BCN")
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help="Directorio base para raw/work/output/docs (por defecto Maestro)",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    base_dir = Path(args.base_dir)
    master_path, alias_path, total_rows = build_catalog(base_dir)

    print("Catalogo generado correctamente")
    print(f"Maestro: {master_path}")
    print(f"Alias:   {alias_path}")
    print(f"Total comunas catalogadas: {total_rows}")


if __name__ == "__main__":
    main()
