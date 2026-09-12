from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ot_toolkit_backend.api.main import create_app
from ot_toolkit_backend.services import MockToolkitService


@pytest.fixture
def service(tmp_path: Path) -> MockToolkitService:
    return MockToolkitService(tmp_path / "favorites.json")


@pytest.fixture
def api_client() -> TestClient:
    with TestClient(create_app()) as client:
        yield client


@pytest.fixture
def demo_token(api_client: TestClient) -> str:
    response = api_client.post(
        "/api/v1/auth/token",
        json={"username": "demo", "password": "demo-password"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
