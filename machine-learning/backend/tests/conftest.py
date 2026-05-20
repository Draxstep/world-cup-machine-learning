"""
conftest.py - Fixtures compartidos para todos los tests.
Usa TestClient de Starlette (sincrono, no necesita asyncio).
El lifespan (carga de modelos) se ejecuta automaticamente.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """Cliente de prueba que activa el lifespan completo una vez por sesion."""
    with TestClient(app) as c:
        yield c
