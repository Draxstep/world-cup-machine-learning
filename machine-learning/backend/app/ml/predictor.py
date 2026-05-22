"""
predictor.py
Capa de abstraccion entre los routers HTTP y las funciones ML de risk_map.py.
Los routers solo llaman a estas funciones; nunca acceden al registry directamente.
"""
import importlib
import sys
from functools import lru_cache

import pandas as pd

from app.config import settings
from app.ml.loader import registry


@lru_cache(maxsize=1)
def _risk_map_module():
    ml_src = str(settings.ml_src_dir)
    if ml_src not in sys.path:
        sys.path.insert(0, ml_src)
    return importlib.import_module("risk_map")


@lru_cache(maxsize=1)
def _report_exporter_module():
    ml_src = str(settings.ml_src_dir)
    if ml_src not in sys.path:
        sys.path.insert(0, ml_src)
    return importlib.import_module("report_exporter")


@lru_cache(maxsize=1)
def _goals_dataset() -> pd.DataFrame:
    df = pd.read_csv(settings.goals_csv_path, encoding="latin1")
    df["team_name"] = df["team_name"].astype(str).str.strip().str.lower()
    df["stage_name"] = df["stage_name"].astype(str).str.strip().str.lower()
    df["match_year"] = pd.to_datetime(df["match_date"], errors="coerce").dt.year
    return df


STAGE_RANK = {
    "group stage": 1,
    "round of 16": 2,
    "round of 16s": 2,
    "round of sixteen": 2,
    "quarter-finals": 3,
    "quarterfinals": 3,
    "semi-finals": 4,
    "semi finals": 4,
    "third-place match": 4,
    "final": 5,
    "final round": 5,
}

STAGE_LABELS = {
    1: "Fase de grupos",
    2: "Octavos",
    3: "Cuartos",
    4: "Semifinal",
    5: "Finalista",
}

TITLE_COUNTS = {
    "brazil": 5,
    "germany": 4,
    "italy": 4,
    "argentina": 3,
    "france": 2,
    "uruguay": 2,
    "england": 1,
    "spain": 1,
}


def predict_risk_map(team_name: str, is_knockout: int, is_home: int) -> dict:
    """
    Devuelve la probabilidad de gol por intervalo para un equipo.

    Parametros
    ----------
    team_name   : nombre del equipo (case-insensitive)
    is_knockout : 1=eliminatoria, 0=grupos
    is_home     : 1=local, 0=visitante

    Retorna
    -------
    dict con keys: team, intervals (list), probabilities (list), cluster, is_knockout, is_home
    """
    risk_map = _risk_map_module()
    result = risk_map.get_team_risk_map(
        team_name=team_name,
        model=registry.rf_model,
        team_profiles=registry.team_profiles,
        is_knockout=is_knockout,
        is_home=is_home,
    )
    baseline = risk_map.get_baseline_risk_map(
        team_profiles=registry.team_profiles,
        model=registry.rf_model,
        is_knockout=is_knockout,
        is_home=is_home,
        cluster=result.get("cluster"),
    )
    result["baseline"] = baseline
    return result


def get_profile(team_name: str) -> dict:
    """
    Retorna el perfil tactico del equipo: cluster, equipos similares y stats.

    Retorna
    -------
    dict con keys: team, cluster, similar_teams, avg_goals_match,
                   penalty_rate, own_goal_rate, mean_minute, knockout_ratio
    """
    risk_map = _risk_map_module()
    return risk_map.get_team_profile_summary(
        team_name=team_name,
        team_profiles=registry.team_profiles,
    )


def get_available_teams() -> list[str]:
    """Lista de equipos disponibles (cargada al arrancar)."""
    return registry.available_teams


@lru_cache(maxsize=1)
def get_metrics() -> dict:
    return registry.metrics_report


@lru_cache(maxsize=1)
def get_cluster_summary() -> dict:
    """Resumen por cluster como dict serializable."""
    return registry.cluster_summary.reset_index().to_dict(orient="records")


@lru_cache(maxsize=1)
def get_quality_report() -> dict:
    return registry.quality_report


def export_report(format_name: str = "pdf") -> str:
    """Genera un reporte en HTML o PDF y retorna la ruta absoluta."""
    exporter = _report_exporter_module()
    output_dir = str(settings.cluster_summary_path.parent)
    images = exporter.collect_report_images(output_dir)

    if format_name == "html":
        return exporter.export_html_report(
            output_dir,
            registry.quality_report,
            registry.metrics_report,
            registry.cluster_summary,
            images,
        )

    if format_name == "pdf":
        return exporter.export_pdf_report(
            output_dir,
            registry.quality_report,
            registry.metrics_report,
            registry.cluster_summary,
            images,
        )

    raise ValueError("Formato de reporte no soportado. Use 'pdf' o 'html'.")


def export_team_report(team_name: str, format_name: str = "pdf", mode: str = "heatmap", is_knockout: int = 0, is_home: int = 1) -> str:
    """Genera un reporte para un equipo específico en formato pdf|csv.

    mode: 'heatmap' incluirá la imagen del mapa de riesgo si es posible.
    """
    exporter = _report_exporter_module()
    risk_map = _risk_map_module()
    output_dir = str(settings.cluster_summary_path.parent)

    # compute risk map and optional heatmap image
    team_risk = risk_map.get_team_risk_map(
        team_name=team_name,
        model=registry.rf_model,
        team_profiles=registry.team_profiles,
        is_knockout=is_knockout,
        is_home=is_home,
    )

    heatmap_path = None
    if mode == 'heatmap':
        try:
            heatmap_path = risk_map.plot_risk_heatmap(team_risk, output_dir)
        except Exception:
            heatmap_path = None

    profile = risk_map.get_team_profile_summary(
        team_name=team_name,
        team_profiles=registry.team_profiles,
    )

    stats = next(
        (item for item in get_team_stats() if item.get('team') == team_risk.get('team')),
        {},
    )

    cluster_row = {}
    if registry.cluster_summary is not None and team_risk.get('cluster') is not None:
        try:
            matched = registry.cluster_summary.reset_index().loc[
                registry.cluster_summary.reset_index()['cluster'] == team_risk.get('cluster')
            ]
            if not matched.empty:
                cluster_row = matched.iloc[0].to_dict()
        except Exception:
            cluster_row = {}

    team_payload = {
        **team_risk,
        'risk_map': team_risk,
        'profile': profile,
        'stats': stats,
        'cluster_row': cluster_row,
        'similar_teams': profile.get('similar_teams', []),
    }

    if format_name == 'csv':
        return exporter.export_team_csv(output_dir, team_risk)

    if format_name == 'pdf':
        return exporter.export_team_pdf(output_dir, team_payload, heatmap_path)

    raise ValueError("Formato de reporte no soportado para equipo. Use 'pdf' o 'csv'.")


@lru_cache(maxsize=1)
def get_team_stats() -> list[dict]:
    """Retorna estadisticas de selecciones para la grilla de banderas."""
    df = _goals_dataset()

    participations = df.groupby("team_name")["tournament_id"].nunique()
    last_year = df.groupby("team_name")["match_year"].max()
    team_code = df.groupby("team_name")["team_code"].agg(
        lambda x: x.dropna().mode().iloc[0] if not x.dropna().empty else None
    )

    def _best_rank(series: pd.Series) -> int:
        ranks = [STAGE_RANK.get(s, 1) for s in series.tolist()]
        return int(max(ranks)) if ranks else 1

    best_stage_rank = df.groupby("team_name")["stage_name"].apply(_best_rank)

    stats = []
    for team in registry.available_teams:
        titles = int(TITLE_COUNTS.get(team, 0))
        rank = int(best_stage_rank.get(team, 1))
        best_finish = "Campeon" if titles > 0 else STAGE_LABELS.get(rank, "Fase de grupos")

        matches_sample = 0
        if registry.team_profiles is not None and team in registry.team_profiles.index:
            matches_sample = int(registry.team_profiles.loc[team].get("matches_played", 0))

        last_participation = last_year.get(team)
        last_participation = int(last_participation) if pd.notna(last_participation) else None

        stats.append({
            "team": team,
            "team_code": team_code.get(team),
            "participations": int(participations.get(team, 0)),
            "last_participation": last_participation,
            "titles": titles,
            "best_finish": best_finish,
            "matches_sample": matches_sample,
        })

    return stats
