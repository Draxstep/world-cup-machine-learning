"""
risk_map.py
===========
RF-08 | Generación del mapa de riesgo temporal.
RF-09 | Consulta del perfil táctico de un equipo.

Dado un equipo y un modelo entrenado, genera la probabilidad estimada de gol
por intervalo de 15 minutos y visualiza el mapa de calor temporal.
Este módulo produce los datos que la API de tu compañero consumirá.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


INTERVALS = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90", "90+"]
FEATURE_COLS = [
    "interval_encoded",
    "is_knockout",
    "is_home",
    "team_goals_hist",
    "team_pen_rate",
    "team_mean_minute",
]


def get_team_risk_map(
    team_name: str,
    model,
    team_profiles: pd.DataFrame,
    is_knockout: int = 0,
    is_home: int = 1,
) -> dict:
    """
    Calcula la probabilidad de gol del equipo por cada intervalo de 15 min.

    Parameters
    ----------
    team_name : str
        Nombre del equipo (debe existir en team_profiles).
    model : clasificador entrenado
        Random Forest o XGBoost persistido.
    team_profiles : pd.DataFrame
        Perfiles de equipo generados por preprocessor.build_team_profiles().
    is_knockout : int
        1 si el partido es fase eliminatoria, 0 si es fase de grupos.
    is_home : int
        1 si el equipo juega como local.

    Returns
    -------
    dict
        {'intervals': [...], 'probabilities': [...], 'team': str, 'cluster': int|None}
    """
    team_name_lower = team_name.strip().lower()

    if team_name_lower not in team_profiles.index:
        # Buscar coincidencia parcial
        matches = [t for t in team_profiles.index if team_name_lower in t]
        if not matches:
            raise ValueError(
                f"Equipo '{team_name}' no encontrado. "
                f"Equipos disponibles: {list(team_profiles.index)}"
            )
        team_name_lower = matches[0]
        print(f"  [risk_map] Usando equipo: '{team_name_lower}'")

    profile = team_profiles.loc[team_name_lower]

    rows = []
    for i, interval in enumerate(INTERVALS):
        rows.append({
            "interval_encoded": i,
            "is_knockout":      is_knockout,
            "is_home":          is_home,
            "team_goals_hist":  float(profile.get("avg_goals_per_match", 1.5)),
            "team_pen_rate":    float(profile.get("penalty_rate", 0.05)),
            "team_mean_minute": float(profile.get("mean_minute", 45.0)),
        })

    X_query = pd.DataFrame(rows)[FEATURE_COLS].values.astype(float)
    probs = model.predict_proba(X_query)[:, 1].tolist()

    cluster = int(profile["cluster"]) if "cluster" in profile.index else None

    return {
        "team":          team_name_lower,
        "intervals":     INTERVALS,
        "probabilities": [round(p, 4) for p in probs],
        "is_knockout":   is_knockout,
        "is_home":       is_home,
        "cluster":       cluster,
    }


def plot_risk_heatmap(
    risk_data: dict,
    output_dir: str,
    filename: str = None,
) -> str:
    """
    Genera el mapa de calor temporal (RF-08): una barra horizontal
    coloreada por la probabilidad de gol en cada intervalo.

    Parameters
    ----------
    risk_data : dict
        Salida de get_team_risk_map().
    output_dir : str
        Carpeta de salida.
    filename : str
        Nombre del archivo. Si None, se genera automáticamente.

    Returns
    -------
    str
        Ruta al archivo PNG generado.
    """
    os.makedirs(output_dir, exist_ok=True)

    team     = risk_data["team"].title()
    probs    = np.array(risk_data["probabilities"])
    intervals = risk_data["intervals"]

    fig, ax = plt.subplots(figsize=(10, 3))
    im = ax.imshow(probs.reshape(1, -1), cmap="RdYlGn", aspect="auto",
                   vmin=0, vmax=1)

    ax.set_xticks(range(len(intervals)))
    ax.set_xticklabels(intervals, fontsize=11)
    ax.set_yticks([])
    ax.set_xlabel("Intervalo del partido (minutos)", fontsize=11)

    context = "Eliminatoria" if risk_data["is_knockout"] else "Fase de grupos"
    local   = "Local" if risk_data["is_home"] else "Visitante"
    ax.set_title(
        f"Mapa de Riesgo Goleador — {team}  |  {context}  |  {local}",
        fontsize=13, fontweight="bold",
    )

    # Anotar probabilidades en cada celda
    for j, p in enumerate(probs):
        color = "white" if p > 0.6 else "black"
        ax.text(j, 0, f"{p:.2f}", ha="center", va="center",
                fontsize=11, fontweight="bold", color=color)

    plt.colorbar(im, ax=ax, orientation="vertical", fraction=0.03, pad=0.02,
                 label="P(gol)")
    plt.tight_layout()

    if filename is None:
        filename = f"risk_map_{team.replace(' ', '_')}.png"
    path = os.path.join(output_dir, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [risk_map] Mapa de riesgo guardado en: {path}")
    return path


def get_team_profile_summary(
    team_name: str,
    team_profiles: pd.DataFrame,
) -> dict:
    """
    RF-09 | Retorna el perfil táctico completo de un equipo:
    su clúster asignado y los equipos más similares históricamente.

    Parameters
    ----------
    team_name : str
        Nombre del equipo a consultar.
    team_profiles : pd.DataFrame
        Perfiles con columna 'cluster' ya asignada.

    Returns
    -------
    dict
        Perfil del equipo con lista de equipos similares (mismo clúster).
    """
    team_name_lower = team_name.strip().lower()

    if team_name_lower not in team_profiles.index:
        raise ValueError(f"Equipo '{team_name}' no encontrado en los perfiles.")

    row     = team_profiles.loc[team_name_lower]
    cluster = int(row["cluster"]) if "cluster" in row.index else None

    similar = []
    if cluster is not None:
        similar = [
            t for t in team_profiles[team_profiles["cluster"] == cluster].index
            if t != team_name_lower
        ]

    return {
        "team":            team_name_lower,
        "cluster":         cluster,
        "similar_teams":   similar,
        "avg_goals_match": round(float(row.get("avg_goals_per_match", 0)), 4),
        "penalty_rate":    round(float(row.get("penalty_rate", 0)), 4),
        "own_goal_rate":   round(float(row.get("own_goal_rate", 0)), 4),
        "mean_minute":     round(float(row.get("mean_minute", 0)), 4),
        "knockout_ratio":  round(float(row.get("knockout_goal_ratio", 0)), 4),
    }
