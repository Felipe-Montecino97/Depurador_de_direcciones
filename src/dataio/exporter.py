import pandas as pd


def export_results(results: list[dict], duplicates: dict, output_path: str) -> None:
    addresses_df = pd.DataFrame(results)
    exact_df = pd.DataFrame(duplicates.get("exact", []))
    similar_df = pd.DataFrame(duplicates.get("similar", []))

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        addresses_df.to_excel(writer, sheet_name="direcciones", index=False)
        exact_df.to_excel(writer, sheet_name="duplicados_exactos", index=False)
        similar_df.to_excel(writer, sheet_name="duplicados_similares", index=False)
