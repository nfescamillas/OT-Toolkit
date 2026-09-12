import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from fastapi.testclient import TestClient

from ot_toolkit_backend.api.main import create_app
from ot_toolkit_backend.api.store import DatabaseStore
from ot_toolkit_backend.services import HttpToolkitService
from ot_toolkit_frontend.ui.main_window import MainWindow


def test_main_window_builds_with_mock_service(service):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(service)
    assert window.windowTitle() == "Industrial Communications & OT Toolkit"
    assert window.nav.count() == 11
    window.navigate("Modbus Toolkit")
    assert window.stack.currentWidget() is window.pages["Modbus Toolkit"]
    window.close()


def test_main_window_builds_with_real_backend_client():
    app = QApplication.instance() or QApplication([])
    api = create_app(DatabaseStore("sqlite+pysqlite:///:memory:"))
    with TestClient(api, base_url="http://testserver/api/v1/") as client:
        service = HttpToolkitService(client=client)
        window = MainWindow(service)
        assert window.nav.count() == 11
        assert window.pages["Dashboard"] is not None
        window.close()
