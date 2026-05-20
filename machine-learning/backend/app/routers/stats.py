"""
stats.py - Router /api/v1/stats
Endpoints:
  GET /metrics   -> metricas RF y clustering
  GET /clusters  -> resumen estadistico por cluster
  GET /quality   -> reporte de calidad del dataset
"""
from fastapi import APIRouter, HTTPException
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
