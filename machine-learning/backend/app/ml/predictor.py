"""
predictor.py
Capa de abstraccion entre los routers HTTP y las funciones ML de risk_map.py.
Los routers solo llaman a estas funciones; nunca acceden al registry directamente.
"""
import importlib
import sys
from functools import lru_cache

from app.config import settings
from app.ml.loader import registry


@lru_cache(maxsize=1)
def _risk_map_module():
    ml_src = str(settings.ml_src_dir)
    if ml_src not in sys.path:
        sys.path.insert(0, ml_src)
    return importlib.import_module("risk_map")


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
    return risk_map.get_team_risk_map(
        team_name=team_name,
        model=registry.rf_model,
        team_profiles=registry.team_profiles,
        is_knockout=is_knockout,
        is_home=is_home,
    )


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


def get_metrics() -> dict:
    return registry.metrics_report


def get_cluster_summary() -> dict:
    """Resumen por cluster como dict serializable."""
    return registry.cluster_summary.reset_index().to_dict(orient="records")


def get_quality_report() -> dict:
    return registry.quality_report
