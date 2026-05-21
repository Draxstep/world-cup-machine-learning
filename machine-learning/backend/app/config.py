"""
config.py
Carga variables de entorno y construye rutas absolutas a los artefactos ML.
No contiene logica de negocio.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ML_MODELS_DIR: str = "../proyecto_ml/models"
    ML_OUTPUTS_DIR: str = "../proyecto_ml/outputs"
    ML_SRC_DIR: str = "../proyecto_ml/src"
    ML_DATA_DIR: str = "../proyecto_ml/data"
    CORS_ORIGINS: str = "http://localhost:5173"
    API_VERSION: str = "v1"

    @property
    def rf_model_path(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_MODELS_DIR / "rf_model.pkl").resolve()

    @property
    def kmeans_model_path(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_MODELS_DIR / "kmeans_model.pkl").resolve()

    @property
    def team_profiles_path(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_OUTPUTS_DIR / "team_profiles_with_cluster.csv").resolve()

    @property
    def cluster_summary_path(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_OUTPUTS_DIR / "cluster_summary.csv").resolve()

    @property
    def metrics_report_path(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_OUTPUTS_DIR / "metrics_report.json").resolve()

    @property
    def quality_report_path(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_OUTPUTS_DIR / "quality_report.json").resolve()

    @property
    def ml_src_dir(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_SRC_DIR).resolve()

    @property
    def goals_csv_path(self) -> Path:
        return (Path(__file__).parent.parent / self.ML_DATA_DIR / "goals.csv").resolve()

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
