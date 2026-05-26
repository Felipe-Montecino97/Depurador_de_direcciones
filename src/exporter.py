import pandas as pd


def export_results(results: list[dict], output_path: str) -> None:
    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False)
