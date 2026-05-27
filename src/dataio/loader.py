from pathlib import Path

import pandas as pd


def load_addresses(file_path: str, address_column: str | None = None) -> tuple[pd.DataFrame, str]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {file_path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError("Formato no soportado. Usa CSV o Excel.")

    if df.empty:
        raise ValueError("El archivo no contiene filas.")

    selected_column = address_column
    if selected_column is None:
        candidates = ["direccion", "dirección", "address", "dir"]
        normalized = {col.lower().strip(): col for col in df.columns}
        for candidate in candidates:
            if candidate in normalized:
                selected_column = normalized[candidate]
                break

    if selected_column is None:
        selected_column = str(df.columns[0])

    if selected_column not in df.columns:
        raise ValueError(f"La columna '{selected_column}' no existe en el archivo.")

    return df, selected_column
