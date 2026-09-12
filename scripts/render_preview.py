"""Render deterministic screenshots for local visual QA."""

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ot_toolkit.services import MockToolkitService
from ot_toolkit.ui.main_window import MainWindow


def render() -> None:
    app = QApplication.instance() or QApplication([])
    service = MockToolkitService(Path(".preview-favorites.json"))
    window = MainWindow(service)
    window.resize(1440, 900)
    window.show()
    app.processEvents()
    Path("artifacts").mkdir(exist_ok=True)
    window.grab().save("artifacts/dashboard.png")
    window.navigate("Modbus Toolkit")
    app.processEvents()
    window.grab().save("artifacts/modbus-toolkit.png")
    window.close()


if __name__ == "__main__":
    render()
