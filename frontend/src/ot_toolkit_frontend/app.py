from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ot_toolkit_backend.services import MockToolkitService
from .ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Industrial Communications & OT Toolkit")
    app.setOrganizationName("OT Toolkit")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow(MockToolkitService())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
