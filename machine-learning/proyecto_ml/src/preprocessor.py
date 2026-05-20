"""
preprocessor.py
===============
RF-02 | Limpieza y preprocesamiento del dataset.
RF-03 | Ingeniería de características (feature engineering).

Responsabilidad:
  - Limpiar el dataset crudo: nulos, duplicados, outliers, inconsistencias.
  - Construir las features necesarias para el modelo supervisado y no supervisado.
  - Separar correctamente en conjuntos de entrenamiento, validación y prueba.

El dataset original tiene un registro por GOL. Este módulo produce:
  1. df_clean        → dataset limpio a nivel de gol.
  2. team_profiles   → una fila por selección (para clustering).
  3. match_intervals → una fila por (partido × intervalo) con etiqueta binaria (para clasificación).
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ── Intervalos de 15 minutos definidos en la propuesta ─────────────────────────
INTERVALS = [
    ("0-15",  0,  15),
    ("16-30", 16, 30),
    ("31-45", 31, 45),
    ("46-60", 46, 60),
    ("61-75", 61, 75),
    ("76-90", 76, 90),
    ("90+",   91, 999),
]

# Fases que corresponden a rondas eliminatorias
KNOCKOUT_STAGES = {
    "round of 16", "quarter-finals", "semi-finals",
    "third-place match", "final", "final round",
}


# ── 1. LIMPIEZA ─────────────────────────────────────────────────────────────────

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica limpieza completa al dataset crudo.

    Pasos:
      1. Elimina duplicados por key_id.
      2. Imputa minute_stoppage nulo → 0 (ausencia de tiempo adicional).
      3. Filtra registros con minute_regulation fuera del rango válido (0–120).
      4. Estandariza strings en columnas categóricas clave.
      5. Deriva columna 'year' desde match_date.
      6. Deriva columna 'is_knockout' según stage_name.
      7. Deriva columna 'minute_total' = minute_regulation + minute_stoppage.
      8. Deriva columna 'interval' con la etiqueta del intervalo de 15 min.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset crudo cargado por data_loader.load_dataset().

    Returns
    -------
    pd.DataFrame
        Dataset limpio con columnas adicionales derivadas.
    """
    df = df.copy()

    # 1. Eliminar duplicados exactos por key_id
    before = len(df)
    df = df.drop_duplicates(subset=["key_id"])
    dropped_dup = before - len(df)
    if dropped_dup > 0:
        print(f"  [limpieza] Duplicados eliminados (key_id): {dropped_dup}")

    # 2. Imputar minute_stoppage: si es nulo → 0
    null_stop = df["minute_stoppage"].isnull().sum()
    if null_stop > 0:
        df["minute_stoppage"] = df["minute_stoppage"].fillna(0)
        print(f"  [limpieza] minute_stoppage nulos imputados con 0: {null_stop}")

    # 3. Outliers en minute_regulation: descartar valores fuera de [0, 120]
    #    (120 cubre tiempo extra; valores mayores son errores de entrada)
    outliers_mask = (df["minute_regulation"] < 0) | (df["minute_regulation"] > 120)
    n_outliers = outliers_mask.sum()
    if n_outliers > 0:
        df = df[~outliers_mask]
        print(f"  [limpieza] Registros con minute_regulation fuera de [0,120] eliminados: {n_outliers}")

    # 4. Estandarizar strings en columnas categóricas
    for col in ["stage_name", "match_period", "team_name", "team_code"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.lower()

    # 5. Derivar año del torneo
    if "match_date" in df.columns:
        df["year"] = pd.to_datetime(df["match_date"], errors="coerce").dt.year

    # 6. Indicador de fase eliminatoria
    df["is_knockout"] = df["stage_name"].isin(KNOCKOUT_STAGES).astype(int)

    # 7. Minuto total del partido
    df["minute_total"] = df["minute_regulation"] + df["minute_stoppage"].fillna(0)

    # 8. Etiqueta de intervalo de 15 minutos
    df["interval"] = df["minute_regulation"].apply(_assign_interval)

    print(f"  [limpieza] Dataset limpio: {len(df)} registros.")
    return df.reset_index(drop=True)


def _assign_interval(minute: int) -> str:
    """Devuelve la etiqueta del intervalo de 15 min al que pertenece un minuto."""
    for label, lo, hi in INTERVALS:
        if lo <= minute <= hi:
            return label
    return "90+"


def detect_outliers_report(df: pd.DataFrame) -> dict:
    """
    Genera un reporte de outliers para las variables numéricas clave.
    Usa el método IQR (rango intercuartílico).

    Returns
    -------
    dict
        Por columna: cantidad de outliers detectados y sus límites.
    """
    report = {}
    for col in ["minute_regulation", "minute_stoppage", "shirt_number"]:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        n_out = int(((df[col] < lower) | (df[col] > upper)).sum())
        report[col] = {"lower_fence": round(lower, 2), "upper_fence": round(upper, 2), "outliers": n_out}
    return report


# ── 2. FEATURE ENGINEERING ──────────────────────────────────────────────────────

def build_team_profiles(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Construye una fila por selección con su perfil ofensivo histórico.
    Esta matriz es la entrada del modelo de CLUSTERING (no supervisado).

    Features generadas:
      - pct_0_15 … pct_90plus : distribución porcentual de goles por intervalo.
      - penalty_rate           : fracción de goles que fueron penalti.
      - own_goal_rate          : fracción de goles que fueron autogol (concedidos).
      - avg_goals_per_match    : promedio de goles por partido disputado.
      - knockout_goal_ratio    : proporción de goles marcados en fases eliminatorias.
      - mean_minute            : minuto promedio de anotación.

    Parameters
    ----------
    df_clean : pd.DataFrame
        Dataset limpio producido por clean_dataset().

    Returns
    -------
    pd.DataFrame
        Una fila por equipo, indexada por team_name, lista para escalar y clusterizar.
    """
    records = []

    for team, grp in df_clean.groupby("team_name"):
        total_goals = len(grp)
        matches = grp["match_id"].nunique()

        # Distribución por intervalo
        interval_counts = grp["interval"].value_counts()
        pct = {}
        for label, _, _ in INTERVALS:
            col_name = "pct_" + label.replace("-", "_").replace("+", "plus")
            pct[col_name] = round(interval_counts.get(label, 0) / total_goals * 100, 4)

        row = {
            "team_name": team,
            "total_goals": total_goals,
            "matches_played": matches,
            **pct,
            "penalty_rate": round(grp["penalty"].sum() / total_goals, 4),
            "own_goal_rate": round(grp["own_goal"].sum() / total_goals, 4),
            "avg_goals_per_match": round(total_goals / max(matches, 1), 4),
            "knockout_goal_ratio": round(grp["is_knockout"].sum() / total_goals, 4),
            "mean_minute": round(grp["minute_regulation"].mean(), 4),
        }
        records.append(row)

    profiles = pd.DataFrame(records).set_index("team_name")
    return profiles


def build_match_intervals(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el dataset supervisado: una fila por (partido × intervalo × equipo).
    La variable objetivo (target) es 1 si el equipo anotó en ese intervalo, 0 si no.

    Features:
      - interval_encoded  : intervalo codificado numéricamente (0–6).
      - is_knockout       : ¿es fase eliminatoria? (0/1).
      - is_home           : ¿el equipo juega como local? (0/1).
      - team_goals_hist   : promedio histórico de goles por partido del equipo.
      - team_pen_rate     : tasa histórica de penaltis del equipo.
      - team_mean_minute  : minuto promedio histórico de anotación del equipo.
      - target            : 1 si anotó en este intervalo en este partido, 0 si no.

    Parameters
    ----------
    df_clean : pd.DataFrame
        Dataset limpio producido por clean_dataset().

    Returns
    -------
    pd.DataFrame
        Dataset listo para entrenar el clasificador supervisado.
    """
    interval_labels = [label for label, _, _ in INTERVALS]
    interval_index  = {label: i for i, label in enumerate(interval_labels)}

    # Estadísticas históricas por equipo (usadas como features contextuales)
    team_stats = (
        df_clean.groupby("team_name")
        .agg(
            _avg_goals=("match_id", lambda x: len(x) / x.nunique()),
            _pen_rate=("penalty", "mean"),
            _mean_min=("minute_regulation", "mean"),
        )
        .rename(columns={
            "_avg_goals": "team_goals_hist",
            "_pen_rate":  "team_pen_rate",
            "_mean_min":  "team_mean_minute",
        })
    )

    # Obtener todos los partidos y equipos que participaron
    matches = df_clean[["match_id", "team_name", "is_knockout"]].drop_duplicates()

    records = []
    for _, row in matches.iterrows():
        mid   = row["match_id"]
        team  = row["team_name"]
        ko    = row["is_knockout"]

        # Goles de este equipo en este partido, por intervalo
        scored = set(
            df_clean[
                (df_clean["match_id"] == mid) &
                (df_clean["team_name"] == team)
            ]["interval"].tolist()
        )

        # ¿Juega como local? (home_team == 1 para este equipo en este partido)
        is_home_rows = df_clean[
            (df_clean["match_id"] == mid) &
            (df_clean["team_name"] == team)
        ]["home_team"]
        is_home = int(is_home_rows.iloc[0]) if len(is_home_rows) > 0 else 0

        stats = team_stats.loc[team] if team in team_stats.index else pd.Series({
            "team_goals_hist": 0.0, "team_pen_rate": 0.0, "team_mean_minute": 45.0
        })

        for label in interval_labels:
            records.append({
                "match_id":         mid,
                "team_name":        team,
                "interval":         label,
                "interval_encoded": interval_index[label],
                "is_knockout":      ko,
                "is_home":          is_home,
                "team_goals_hist":  round(float(stats["team_goals_hist"]), 4),
                "team_pen_rate":    round(float(stats["team_pen_rate"]), 4),
                "team_mean_minute": round(float(stats["team_mean_minute"]), 4),
                "target":           int(label in scored),
            })

    return pd.DataFrame(records)


# ── 3. SPLIT ENTRENAMIENTO / VALIDACIÓN / PRUEBA ─────────────────────────────────

def split_supervised_dataset(
    df_intervals: pd.DataFrame,
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
):
    """
    Divide el dataset supervisado en train / val / test.
    La división se hace a nivel de partido (match_id) para evitar fuga de información.

    Parameters
    ----------
    df_intervals : pd.DataFrame
        Dataset producido por build_match_intervals().
    test_size : float
        Fracción de partidos para el conjunto de prueba.
    val_size : float
        Fracción de partidos para el conjunto de validación.
    random_state : int
        Semilla para reproducibilidad.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        (df_train, df_val, df_test)
    """
    all_matches = df_intervals["match_id"].unique()

    # Separar test primero
    train_val_ids, test_ids = train_test_split(
        all_matches, test_size=test_size, random_state=random_state
    )

    # Separar val del restante
    relative_val = val_size / (1 - test_size)
    train_ids, val_ids = train_test_split(
        train_val_ids, test_size=relative_val, random_state=random_state
    )

    df_train = df_intervals[df_intervals["match_id"].isin(train_ids)].copy()
    df_val   = df_intervals[df_intervals["match_id"].isin(val_ids)].copy()
    df_test  = df_intervals[df_intervals["match_id"].isin(test_ids)].copy()

    print(f"  [split] Train: {len(df_train)} | Val: {len(df_val)} | Test: {len(df_test)}")
    print(f"  [split] Partidos → Train: {len(train_ids)} | Val: {len(val_ids)} | Test: {len(test_ids)}")

    return df_train, df_val, df_test


def scale_team_profiles(profiles: pd.DataFrame):
    """
    Escala las features del perfil de equipo usando StandardScaler.
    Excluye columnas no-feature como total_goals y matches_played.

    Returns
    -------
    tuple[np.ndarray, list[str], StandardScaler]
        (X_scaled, feature_names, scaler)
    """
    exclude = ["total_goals", "matches_played"]
    feature_cols = [c for c in profiles.columns if c not in exclude]
    X = profiles[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, feature_cols, scaler


SUPERVISED_FEATURES = [
    "interval_encoded",
    "is_knockout",
    "is_home",
    "team_goals_hist",
    "team_pen_rate",
    "team_mean_minute",
]
SUPERVISED_TARGET = "target"
