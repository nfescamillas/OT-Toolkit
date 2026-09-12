from pathlib import Path

import pytest

from ot_toolkit_backend.services import MockToolkitService


@pytest.fixture
def service(tmp_path: Path) -> MockToolkitService:
    """Inject the offline backend into frontend integration tests."""
    return MockToolkitService(tmp_path / "favorites.json")
