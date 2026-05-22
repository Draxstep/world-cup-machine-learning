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


class TeamStatsItem(BaseModel):
    team: str
    team_code: str | None = None
    cluster: int | None = None
    participations: int
    last_participation: int | None = None
    titles: int
    best_finish: str
    matches_sample: int


class TeamStatsResponse(BaseModel):
    teams: list[TeamStatsItem]
    total: int
