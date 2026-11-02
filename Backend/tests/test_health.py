from fastapi import status
from sqlalchemy.exc import OperationalError
from unittest.mock import MagicMock
from app.db.dependencies import get_db
from app.main import create_application


def test_app_startup(client):
    """Test that the FastAPI application initializes properly."""
    assert client.app.title == "GearShare API"


def test_health_endpoint_healthy(client):
    """Test health endpoint when database connectivity is healthy."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_endpoint_db_failure():
    """Test health endpoint returns 503 when database is unreachable."""
    app = create_application()

    # Mock database session that raises an error on query execution
    mock_db = MagicMock()
    mock_db.execute.side_effect = OperationalError("Connection refused", params=None, orig=Exception("DB down"))

    app.dependency_overrides[get_db] = lambda: mock_db

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
