import pandas as pd


def export_results(
    summary_rows: list[dict],
    detail_rows: list[dict],
    duplicates: dict,
    output_path: str,
    quality_rows: list[dict] | None = None,
    quality_metrics: list[dict] | None = None,
) -> None:
    summary_df = pd.DataFrame(summary_rows)
    detail_df = pd.DataFrame(detail_rows)
    exact_df = pd.DataFrame(duplicates.get("exact", []))
    similar_df = pd.DataFrame(duplicates.get("similar", []))
    quality_df = pd.DataFrame(quality_rows or [])
    metrics_df = pd.DataFrame(quality_metrics or [])

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="resumen", index=False)
        detail_df.to_excel(writer, sheet_name="detalle_tecnico", index=False)
        exact_df.to_excel(writer, sheet_name="duplicados_exactos", index=False)
        similar_df.to_excel(writer, sheet_name="duplicados_similares", index=False)
        quality_df.to_excel(writer, sheet_name="calidad_direcciones", index=False)
        metrics_df.to_excel(writer, sheet_name="metricas_calidad", index=False)

        writer.book["detalle_tecnico"].sheet_state = "hidden"
