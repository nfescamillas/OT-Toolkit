from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from ot_toolkit_backend.services import HttpToolkitService, ToolkitApiError
from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Industrial Communications & OT Toolkit")
    app.setOrganizationName("OT Toolkit")
    app.setFont(QFont("Segoe UI", 10))
    service = HttpToolkitService.from_environment()
    try:
        window = MainWindow(service)
    except ToolkitApiError as exc:
        service.close()
        QMessageBox.critical(None, "Backend unavailable", str(exc))
        return 1
    app.aboutToQuit.connect(service.close)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
