"""
stats.py - Router /api/v1/stats
Endpoints:
  GET /metrics   -> metricas RF y clustering
  GET /clusters  -> resumen estadistico por cluster
  GET /quality   -> reporte de calidad del dataset
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.config import settings
from app.schemas.stats import TeamStatsResponse
from app.ml import predictor

router = APIRouter(prefix="/stats", tags=["Estadisticas"])


@router.get(
    "/metrics",
    summary="Metricas del modelo Random Forest y clustering",
)
def get_metrics():
    try:
        return predictor.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/clusters",
    summary="Resumen estadistico de cada cluster K-Means",
)
def get_clusters():
    try:
        return predictor.get_cluster_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/quality",
    summary="Reporte de calidad del dataset FIFA 1930-2022",
)
def get_quality():
    try:
        return predictor.get_quality_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/report",
    summary="Exporta reporte HTML o PDF",
)
def get_report(format: str = Query("pdf", pattern="^(pdf|html)$")):
    try:
        path = predictor.export_report(format)
        media_type = "application/pdf" if format == "pdf" else "text/html"
        filename = f"report.{format}"
        return FileResponse(path, media_type=media_type, filename=filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/report/team",
    summary="Exporta reporte para un equipo (PDF o CSV)",
)
def get_team_report(
    team: str = Query(..., description="Nombre del equipo"),
    format: str = Query("pdf", pattern="^(pdf|csv)$"),
    mode: str = Query("heatmap", pattern="^(heatmap|profile)$"),
    is_knockout: int = Query(0, ge=0, le=1),
    is_home: int = Query(1, ge=0, le=1),
):
    try:
        path = predictor.export_team_report(team_name=team, format_name=format, mode=mode, is_knockout=is_knockout, is_home=is_home)
        media_type = "application/pdf" if format == "pdf" else "text/csv"
        filename = f"{team.replace(' ', '_')}_report.{format}"
        return FileResponse(path, media_type=media_type, filename=filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/teams",
    response_model=TeamStatsResponse,
    summary="Estadisticas de selecciones para grilla de banderas",
)
def get_team_stats():
    try:
        teams = predictor.get_team_stats()
        return TeamStatsResponse(teams=teams, total=len(teams))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/plots/{plot_name}",
    summary="Imagenes PNG generadas por el pipeline",
)
def get_plot(plot_name: str):
    safe_name = Path(plot_name).name
    if not safe_name.lower().endswith(".png"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PNG.")

    path = Path(settings.cluster_summary_path.parent) / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")

    return FileResponse(path, media_type="image/png")
