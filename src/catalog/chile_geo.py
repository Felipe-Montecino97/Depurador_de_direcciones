from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd


def normalize_text(value: str) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.upper().split())


def find_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized_columns = {normalize_text(column): column for column in columns}
    for candidate in candidates:
        found = normalized_columns.get(normalize_text(candidate))
        if found:
            return found
    return None


class ChileGeoResolver:
    def __init__(self, master_df: pd.DataFrame, alias_df: pd.DataFrame | None = None) -> None:
        self.master_df = master_df.copy()
        self.alias_df = alias_df.copy() if alias_df is not None else pd.DataFrame(columns=["tipo", "alias", "valor_oficial"])

        self.comuna_to_region: dict[str, str] = {}
        self.comuna_norm_to_official: dict[str, str] = {}
        self.region_norm_to_official: dict[str, str] = {}
        self.alias_comuna: dict[str, str] = {}
        self.alias_region: dict[str, str] = {}

        self._build_indexes()

    @classmethod
    def from_paths(cls, master_path: Path, alias_path: Path | None = None) -> "ChileGeoResolver":
        master_df = pd.read_csv(master_path)
        alias_df = pd.read_csv(alias_path) if alias_path and alias_path.exists() else None
        return cls(master_df=master_df, alias_df=alias_df)

    def _build_indexes(self) -> None:
        if "comuna_normalizada" not in self.master_df.columns:
            self.master_df["comuna_normalizada"] = self.master_df["nombre_comuna"].map(normalize_text)
        if "region_normalizada" not in self.master_df.columns:
            self.master_df["region_normalizada"] = self.master_df["nombre_region"].map(normalize_text)

        for _, row in self.master_df.iterrows():
            comuna_norm = normalize_text(row.get("comuna_normalizada", ""))
            comuna_official = str(row.get("nombre_comuna", "")).strip()
            region_official = str(row.get("nombre_region", "")).strip()

            if comuna_norm and comuna_official:
                self.comuna_norm_to_official[comuna_norm] = comuna_official
                if region_official:
                    self.comuna_to_region[comuna_norm] = region_official

            region_norm = normalize_text(row.get("region_normalizada", ""))
            if region_norm and region_official:
                self.region_norm_to_official[region_norm] = region_official

        if self.alias_df.empty:
            return

        for _, row in self.alias_df.iterrows():
            alias_type = normalize_text(row.get("tipo", "")).lower()
            alias = normalize_text(row.get("alias", ""))
            official_raw = str(row.get("valor_oficial", "")).strip()
            if not alias or not official_raw:
                continue

            official_norm = normalize_text(official_raw)
            if alias_type == "comuna":
                official = self.comuna_norm_to_official.get(official_norm, official_raw)
                self.alias_comuna[alias] = official
            elif alias_type == "region":
                official = self.region_norm_to_official.get(official_norm, official_raw)
                self.alias_region[alias] = official

    def _resolve_comuna_candidate(self, raw_value: str) -> str:
        normalized = normalize_text(raw_value)
        if not normalized:
            return ""

        alias_hit = self.alias_comuna.get(normalized)
        if alias_hit:
            return alias_hit

        official = self.comuna_norm_to_official.get(normalized)
        return official or ""

    def _resolve_region_candidate(self, raw_value: str) -> str:
        normalized = normalize_text(raw_value)
        if not normalized:
            return ""

        alias_hit = self.alias_region.get(normalized)
        if alias_hit:
            return alias_hit

        official = self.region_norm_to_official.get(normalized)
        return official or ""

    def _resolve_comuna_from_text(self, raw_text: str) -> str:
        normalized_text = f" {normalize_text(raw_text)} "
        if normalized_text.strip() == "":
            return ""

        matches: list[tuple[int, str]] = []
        for comuna_norm, comuna_official in self.comuna_norm_to_official.items():
            token = f" {comuna_norm} "
            if token in normalized_text:
                matches.append((len(comuna_norm), comuna_official))

        if not matches:
            return ""

        matches.sort(key=lambda item: item[0], reverse=True)
        return matches[0][1]

    def resolve(self, comuna_raw: str, ciudad_raw: str, region_raw: str, direccion_raw: str) -> dict[str, str]:
        comuna = self._resolve_comuna_candidate(comuna_raw)
        source = "COMUNA"

        if not comuna:
            comuna = self._resolve_comuna_candidate(ciudad_raw)
            source = "CIUDAD"

        if not comuna:
            comuna = self._resolve_comuna_from_text(direccion_raw)
            source = "DIRECCION"

        if not comuna:
            return {
                "comuna": "",
                "region": "",
                "estado_territorial": "COMUNA_NO_ENCONTRADA",
                "origen_comuna": "",
                "fuente_territorial": "BCN-SIIT",
            }

        comuna_norm = normalize_text(comuna)
        region_derived = self.comuna_to_region.get(comuna_norm, "")
        region_informed = self._resolve_region_candidate(region_raw)

        if region_informed and region_derived and normalize_text(region_informed) != normalize_text(region_derived):
            status = "COMUNA_REGION_INCONSISTENTE"
            final_region = region_derived
        elif region_derived:
            status = "OK"
            final_region = region_derived
        else:
            status = "SIN_REGION"
            final_region = ""

        return {
            "comuna": comuna,
            "region": final_region,
            "estado_territorial": status,
            "origen_comuna": source,
            "fuente_territorial": "BCN-SIIT",
        }
