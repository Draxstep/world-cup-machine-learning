"""
predictions.py - Router /api/v1/predict
Endpoints:
  POST /risk-map          -> mapa de riesgo para un equipo
  GET  /profile/{team}    -> perfil tactico + equipos similares
  GET  /teams             -> lista de equipos disponibles
"""
from fastapi import APIRouter, HTTPException
from app.schemas.prediction import RiskMapRequest, RiskMapResponse, TeamProfileResponse
from app.schemas.stats import TeamsListResponse
from app.ml import predictor

router = APIRouter(prefix="/predict", tags=["Predicciones"])


@router.post(
    "/risk-map",
    response_model=RiskMapResponse,
    summary="Mapa de riesgo goleador por intervalos",
    description=(
        "Dado un equipo y el contexto del partido, retorna la probabilidad estimada "
        "de que el equipo anote en cada uno de los 7 intervalos de 15 minutos. "
        "Usa el modelo Random Forest entrenado con el historico 1930-2022."
    ),
)
def predict_risk_map(body: RiskMapRequest):
    try:
        result = predictor.predict_risk_map(
            team_name=body.team_name,
            is_knockout=body.is_knockout,
            is_home=body.is_home,
        )
        return RiskMapResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del modelo: {e}")


@router.get(
    "/profile/{team_name}",
    response_model=TeamProfileResponse,
    summary="Perfil tactico de un equipo",
    description=(
        "Retorna el cluster K-Means asignado al equipo y los equipos historicos mas similares, "
        "junto con estadisticas ofensivas agregadas."
    ),
)
def get_team_profile(team_name: str):
    try:
        result = predictor.get_profile(team_name.strip().lower())
        return TeamProfileResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


@router.get(
    "/teams",
    response_model=TeamsListResponse,
    summary="Lista de equipos disponibles",
)
def list_teams():
    teams = predictor.get_available_teams()
    return TeamsListResponse(teams=teams, total=len(teams))
