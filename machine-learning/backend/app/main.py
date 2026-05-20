"""
main.py - Punto de entrada de la API FastAPI.
Responsabilidades:
  1. Crear la instancia FastAPI con lifespan (carga de modelos).
  2. Configurar CORS para el frontend en localhost:5173.
  3. Registrar routers bajo el prefijo /api/v1.
  4. Exponer endpoint de salud GET /health.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ml.loader import lifespan
from app.routers import predictions, stats


app = FastAPI(
    title="Sistema de Inteligencia Tactica FIFA",
    description=(
        "API REST para prediccion de riesgo goleador y analisis de perfiles tacticos "
        "usando el historico de goles del Mundial FIFA 1930-2022."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = f"/api/{settings.API_VERSION}"
app.include_router(predictions.router, prefix=PREFIX)
app.include_router(stats.router, prefix=PREFIX)


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "version": "1.0.0"}
