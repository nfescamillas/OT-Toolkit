import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ot_toolkit.ui.main_window import MainWindow


def test_main_window_builds_with_mock_service(service):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(service)
    assert window.windowTitle() == "Industrial Communications & OT Toolkit"
    assert window.nav.count() == 11
    window.navigate("Modbus Toolkit")
    assert window.stack.currentWidget() is window.pages["Modbus Toolkit"]
    window.close()
