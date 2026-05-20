"""
data_loader.py
==============
RF-01 | Carga y validación del dataset CSV con reporte automático de calidad de datos.

Responsabilidad: cargar el CSV del dataset FIFA World Cup All Goals 1930-2022,
validar su estructura y producir un reporte de calidad (nulos, duplicados, tipos).
"""

import os
import pandas as pd


REQUIRED_COLUMNS = [
    "key_id", "match_id", "team_name", "team_code",
    "minute_regulation", "minute_stoppage", "match_period",
    "stage_name", "own_goal", "penalty", "home_team", "away_team",
]

CSV_ENCODING = "latin1"


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Carga el CSV desde la ruta indicada y retorna un DataFrame crudo.

    Parameters
    ----------
    filepath : str
        Ruta al archivo CSV del dataset.

    Returns
    -------
    pd.DataFrame
        Dataset cargado sin ningún preprocesamiento.

    Raises
    ------
    FileNotFoundError
        Si el archivo no existe en la ruta indicada.
    ValueError
        Si alguna columna requerida está ausente.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo: {filepath}")

    df = pd.read_csv(filepath, encoding=CSV_ENCODING)

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"El dataset no contiene las columnas requeridas: {missing_cols}"
        )

    return df


def generate_quality_report(df: pd.DataFrame) -> dict:
    """
    Genera un reporte de calidad de datos con métricas básicas.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset cargado (sin preprocesar).

    Returns
    -------
    dict
        Diccionario con métricas de calidad del dataset.
    """
    report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "null_percent": (df.isnull().mean() * 100).round(2).to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_key_id": int(df.duplicated(subset=["key_id"]).sum()),
        "teams": int(df["team_name"].nunique()),
        "matches": int(df["match_id"].nunique()),
        "tournaments": df["tournament_name"].unique().tolist() if "tournament_name" in df.columns else [],
        "year_range": (
            pd.to_datetime(df["match_date"], format="%m/%d/%Y", errors="coerce").dt.year.agg(["min", "max"]).to_dict()
            if "match_date" in df.columns else {}
        ),
        "own_goals": int(df["own_goal"].sum()),
        "penalties": int(df["penalty"].sum()),
        "minute_regulation_stats": {
            "min": int(df["minute_regulation"].min()),
            "max": int(df["minute_regulation"].max()),
            "mean": round(float(df["minute_regulation"].mean()), 2),
        },
    }
    return report


def print_quality_report(report: dict) -> None:
    """Imprime el reporte de calidad en consola de forma legible."""
    print("=" * 60)
    print("  REPORTE DE CALIDAD DEL DATASET")
    print("=" * 60)
    print(f"  Filas totales        : {report['total_rows']}")
    print(f"  Columnas totales     : {report['total_columns']}")
    print(f"  Filas duplicadas     : {report['duplicate_rows']}")
    print(f"  key_id duplicados    : {report['duplicate_key_id']}")
    print(f"  Equipos únicos       : {report['teams']}")
    print(f"  Partidos únicos      : {report['matches']}")
    print(f"  Torneos              : {len(report['tournaments'])}")
    print(f"  Rango de años        : {report.get('year_range')}")
    print(f"  Goles de penalti     : {report['penalties']}")
    print(f"  Autogoles            : {report['own_goals']}")
    print(f"  Minuto reg. (min/max/mean): {report['minute_regulation_stats']}")

    total_nulls = sum(report["null_counts"].values())
    print(f"\n  Valores nulos totales: {total_nulls}")
    if total_nulls > 0:
        for col, n in report["null_counts"].items():
            if n > 0:
                print(f"    → {col}: {n} ({report['null_percent'][col]}%)")
    print("=" * 60)
