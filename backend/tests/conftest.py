from pathlib import Path

import pytest

from ot_toolkit_backend.services import MockToolkitService


@pytest.fixture
def service(tmp_path: Path) -> MockToolkitService:
    return MockToolkitService(tmp_path / "favorites.json")
