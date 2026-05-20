"""
loader.py
Carga unica de modelos ML y artefactos pre-computados.
Se invoca en el lifespan de FastAPI; los objetos viven toda la sesion.
"""
import sys
import json
import joblib
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.config import settings


class MLRegistry:
    """Contenedor de estado global para modelos y datos ML."""
    rf_model = None          # RandomForestClassifier
    kmeans_model = None      # KMeans
    team_profiles = None     # pd.DataFrame; index: team_name (lowercase)
    cluster_summary = None   # pd.DataFrame
    metrics_report = None    # dict
    quality_report = None    # dict
    available_teams = None   # list[str]; nombres de equipos disponibles


registry = MLRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Carga todos los artefactos al iniciar. Libera al apagar (no necesario aqui,
    pero el patron es correcto para recursos con cleanup).
    """
    if str(settings.ml_src_dir) not in sys.path:
        sys.path.insert(0, str(settings.ml_src_dir))

    print("[startup] Cargando rf_model.pkl ...")
    registry.rf_model = joblib.load(settings.rf_model_path)

    print("[startup] Cargando kmeans_model.pkl ...")
    registry.kmeans_model = joblib.load(settings.kmeans_model_path)

    print("[startup] Cargando team_profiles_with_cluster.csv ...")
    registry.team_profiles = pd.read_csv(
        settings.team_profiles_path, index_col="team_name"
    )

    print("[startup] Cargando cluster_summary.csv ...")
    registry.cluster_summary = pd.read_csv(
        settings.cluster_summary_path, index_col="cluster"
    )

    with open(settings.metrics_report_path, encoding="utf-8") as f:
        registry.metrics_report = json.load(f)

    with open(settings.quality_report_path, encoding="utf-8") as f:
        registry.quality_report = json.load(f)

    registry.available_teams = sorted(registry.team_profiles.index.tolist())

    print(f"[startup] Modelos listos. {len(registry.available_teams)} equipos disponibles.")
    yield
