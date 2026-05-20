"""
stats.py - Pydantic schemas para los endpoints de estadisticas.
"""
from pydantic import BaseModel


class ClusterSummaryItem(BaseModel):
    cluster: int
    total_goals: float
    matches_played: float
    avg_goals_per_match: float
    penalty_rate: float
    mean_minute: float


class MetricsReport(BaseModel):
    clustering: dict
    random_forest: dict


class TeamsListResponse(BaseModel):
    teams: list[str]
    total: int
