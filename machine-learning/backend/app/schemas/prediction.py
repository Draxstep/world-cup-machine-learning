"""
prediction.py - Pydantic schemas para los endpoints de prediccion.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class RiskMapRequest(BaseModel):
    team_name: str = Field(
        ...,
        description="Nombre del equipo (case-insensitive, ej: 'Brazil')",
        examples=["brazil"],
    )
    is_knockout: Literal[0, 1] = Field(
        default=0,
        description="1 si el partido es fase eliminatoria, 0 si es fase de grupos",
    )
    is_home: Literal[0, 1] = Field(
        default=1,
        description="1 si el equipo juega como local, 0 como visitante",
    )

    @field_validator("team_name")
    @classmethod
    def normalize_team_name(cls, v: str) -> str:
        return v.strip().lower()


class RiskMapResponse(BaseModel):
    team: str
    intervals: list[str]
    probabilities: list[float]
    cluster: int | None
    is_knockout: int
    is_home: int


class TeamProfileResponse(BaseModel):
    team: str
    cluster: int | None
    similar_teams: list[str]
    avg_goals_match: float
    penalty_rate: float
    own_goal_rate: float
    mean_minute: float
    knockout_ratio: float
