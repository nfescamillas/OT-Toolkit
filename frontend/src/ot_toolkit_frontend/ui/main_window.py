from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
    QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget,
)

from ot_toolkit_backend.models import Technology
from ot_toolkit_backend.services import ToolkitService


THEME = """
QWidget { background: #0b1119; color: #dce7f1; font-size: 14px; }
QLabel, QCheckBox { background: transparent; }
QMainWindow { background: #081018; }
QFrame#Sidebar { background: #0e1722; border-right: 1px solid #223142; }
QFrame#Topbar { background: #0b131d; border-bottom: 1px solid #223142; }
QFrame#Card { background: #111c28; border: 1px solid #26384a; border-radius: 10px; }
QLabel#Brand { color: #f4f7fb; font-size: 18px; font-weight: 700; }
QLabel#Eyebrow { color: #62c6ff; font-size: 12px; font-weight: 700; letter-spacing: 1px; }
QLabel#Title { color: #f4f7fb; font-size: 26px; font-weight: 700; }
QLabel#Section { color: #f4f7fb; font-size: 17px; font-weight: 650; }
QLabel#Muted { color: #8ea3b7; }
QLabel#Badge { color: #071019; background: #ffbd59; border-radius: 8px; padding: 3px 8px; font-weight: 700; }
QLineEdit, QComboBox, QSpinBox, QTextEdit { background: #0a131d; border: 1px solid #30465c; border-radius: 7px; padding: 8px; selection-background-color: #1687b8; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus { border-color: #55c7f6; }
QPushButton { background: #172637; border: 1px solid #35506a; border-radius: 7px; padding: 8px 13px; font-weight: 600; }
QPushButton:hover { background: #20354a; border-color: #59c8f5; }
QPushButton#Primary { background: #e7a83e; color: #111820; border-color: #ffc665; }
QPushButton#Primary:hover { background: #ffc665; }
QListWidget { background: transparent; border: 0; outline: 0; }
QListWidget::item { padding: 9px 11px; margin: 2px 6px; border-radius: 6px; color: #aebed0; }
QListWidget::item:hover { background: #172536; color: #f4f7fb; }
QListWidget::item:selected { background: #1d3548; color: #73d6ff; border-left: 3px solid #f3b64e; }
QTableWidget { background: #0e1823; alternate-background-color: #111e2b; gridline-color: #26384a; border: 1px solid #26384a; border-radius: 8px; }
QTableWidget::item { padding: 7px; }
QHeaderView::section { background: #162536; color: #9eb2c5; padding: 8px; border: 0; border-right: 1px solid #26384a; font-weight: 700; }
QTabWidget::pane { border: 1px solid #26384a; border-radius: 8px; top: -1px; background: #0e1722; }
QTabBar::tab { background: #101b27; color: #91a6b9; padding: 9px 15px; border: 1px solid #26384a; }
QTabBar::tab:selected { color: #68d2ff; background: #172738; border-bottom-color: #172738; }
QScrollBar:vertical { background: #0d1620; width: 11px; }
QScrollBar::handle:vertical { background: #30465c; min-height: 30px; border-radius: 5px; }
QToolTip { color: #eaf2f8; background: #182737; border: 1px solid #3c566d; }
"""


def title_block(title: str, subtitle: str, eyebrow: str = "FIELD REFERENCE") -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget); layout.setContentsMargins(0, 0, 0, 8); layout.setSpacing(3)
    top = QLabel(eyebrow); top.setObjectName("Eyebrow")
    heading = QLabel(title); heading.setObjectName("Title"); heading.setWordWrap(True)
    detail = QLabel(subtitle); detail.setObjectName("Muted"); detail.setWordWrap(True)
    layout.addWidget(top); layout.addWidget(heading); layout.addWidget(detail)
    return widget


def card(title: str, body: str = "") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(); frame.setObjectName("Card")
    layout = QVBoxLayout(frame); layout.setContentsMargins(16, 14, 16, 14); layout.setSpacing(8)
    heading = QLabel(title); heading.setObjectName("Section"); heading.setWordWrap(True); layout.addWidget(heading)
    if body:
        text = QLabel(body); text.setObjectName("Muted"); text.setWordWrap(True); layout.addWidget(text)
    return frame, layout


def output_box() -> QTextEdit:
    box = QTextEdit(); box.setReadOnly(True); box.setMinimumHeight(115); box.setFont(QFont("Cascadia Mono", 10)); return box


def format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.9g}" if math.isfinite(value) else str(value)
    if isinstance(value, bool): return "Yes" if value else "No"
    if isinstance(value, (list, tuple)): return ", ".join(map(str, value)) or "—"
    return str(value)


class ClickableList(QListWidget):
    chosen = Signal(str)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item and item.data(Qt.ItemDataRole.UserRole): self.chosen.emit(item.data(Qt.ItemDataRole.UserRole))
        super().mouseDoubleClickEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, service: ToolkitService) -> None:
        super().__init__()
        if "Segoe UI" not in QFontDatabase.families():
            QFontDatabase.addApplicationFont("C:/Windows/Fonts/segoeui.ttf")
            QApplication.instance().setFont(QFont("Segoe UI", 10))
        self.service = service
        self.setWindowTitle("Industrial Communications & OT Toolkit")
        self.resize(1440, 900); self.setMinimumSize(1040, 680)
        self.setStyleSheet(THEME); self.setWindowIcon(self._make_icon())
        self.pages: dict[str, QWidget] = {}
        self._build_shell()
        self.navigate("Dashboard")

    @staticmethod
    def _make_icon() -> QIcon:
        pixmap = QPixmap(64, 64); pixmap.fill(QColor("#0e1722"))
        painter = QPainter(pixmap); painter.setPen(QColor("#ffbd59")); painter.setBrush(QColor("#173447")); painter.drawRoundedRect(8, 8, 48, 48, 9, 9)
        painter.setPen(QColor("#68d2ff")); font = painter.font(); font.setBold(True); font.setPixelSize(24); painter.setFont(font); painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "OT"); painter.end()
        return QIcon(pixmap)

    def _build_shell(self) -> None:
        root = QWidget(); self.setCentralWidget(root); shell = QHBoxLayout(root); shell.setContentsMargins(0, 0, 0, 0); shell.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName("Sidebar"); sidebar.setFixedWidth(232); side = QVBoxLayout(sidebar); side.setContentsMargins(12, 18, 12, 14)
        brand = QLabel("OT TOOLKIT"); brand.setObjectName("Brand"); side.addWidget(brand)
        strap = QLabel("INDUSTRIAL COMMS DESK"); strap.setObjectName("Eyebrow"); side.addWidget(strap); side.addSpacing(18)
        self.nav = QListWidget()
        nav_items = ["Dashboard", "Communications", "Hierarchy Explorer", "Compare", "Data Converters", "Modbus Toolkit", "Network Toolkit", "Port Lookup", "Troubleshooting", "Glossary", "Favorites"]
        for text in nav_items:
            item = QListWidgetItem(text); self.nav.addItem(item)
        self.nav.currentTextChanged.connect(self.navigate); side.addWidget(self.nav, 1)
        offline = QLabel("OFFLINE DATA READY"); offline.setStyleSheet("color:#64d39a;font-size:12px;font-weight:700;padding:8px"); side.addWidget(offline)
        shell.addWidget(sidebar)
        work = QWidget(); work_layout = QVBoxLayout(work); work_layout.setContentsMargins(0, 0, 0, 0); work_layout.setSpacing(0)
        topbar = QFrame(); topbar.setObjectName("Topbar"); top = QHBoxLayout(topbar); top.setContentsMargins(24, 12, 24, 12)
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Search protocols, acronyms, files, ports…"); self.search_input.setClearButtonEnabled(True); self.search_input.returnPressed.connect(self.global_search)
        search_button = QPushButton("Search"); search_button.setObjectName("Primary"); search_button.clicked.connect(self.global_search)
        top.addWidget(self.search_input, 1); top.addWidget(search_button)
        self.stack = QStackedWidget(); work_layout.addWidget(topbar); work_layout.addWidget(self.stack, 1); shell.addWidget(work, 1)

    def navigate(self, name: str) -> None:
        if not name: return
        builders = {"Dashboard": self._dashboard, "Communications": self._communications, "Hierarchy Explorer": self._hierarchy, "Compare": self._compare, "Data Converters": self._data_tools, "Modbus Toolkit": self._modbus_tools, "Network Toolkit": self._network_tools, "Port Lookup": self._ports, "Troubleshooting": self._troubleshooting, "Glossary": self._glossary, "Favorites": self._favorites}
        if name not in self.pages:
            self.pages[name] = builders[name](); self.stack.addWidget(self.pages[name])
        self.stack.setCurrentWidget(self.pages[name])
        matches = self.nav.findItems(name, Qt.MatchFlag.MatchExactly)
        if matches and self.nav.currentItem() is not matches[0]: self.nav.setCurrentItem(matches[0])

    def _page(self) -> tuple[QScrollArea, QWidget, QVBoxLayout]:
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget(); layout = QVBoxLayout(body); layout.setContentsMargins(28, 24, 28, 28); layout.setSpacing(16); scroll.setWidget(body)
        return scroll, body, layout

    def _error(self, exc: Exception) -> None:
        QMessageBox.warning(self, "Check the input", str(exc))

    def global_search(self) -> None:
        query = self.search_input.text().strip()
        if not query: return
        page = self._search_results(query)
        key = "Search Results"
        if key in self.pages: self.stack.removeWidget(self.pages[key]); self.pages[key].deleteLater()
        self.pages[key] = page; self.stack.addWidget(page); self.stack.setCurrentWidget(page)

    def _search_results(self, query: str) -> QWidget:
        scroll, _, layout = self._page(); results = self.service.search(query)
        layout.addWidget(title_block(f"Search: {query}", f"{len(results)} matches across technologies, ports, and glossary.", "GLOBAL INDEX"))
        listing = ClickableList(); listing.setMinimumHeight(450); listing.chosen.connect(self.show_technology)
        for result in results:
            item = QListWidgetItem(f"{result.title}\n{result.kind.upper()}  ·  {result.subtitle}"); item.setData(Qt.ItemDataRole.UserRole, result.id if result.kind == "Technology" else ""); listing.addItem(item)
        if not results: listing.addItem("No matches. Try an acronym, port, standard, or configuration file name.")
        layout.addWidget(listing); return scroll

    def _dashboard(self) -> QWidget:
        scroll, _, layout = self._page()
        layout.addWidget(title_block("Engineering desk", "Reference the stack, decode field values, and isolate communication faults.", "INDUSTRIAL COMMUNICATIONS"))
        grid = QGridLayout(); grid.setSpacing(12)
        metrics = [(str(len(self.service.list_technologies())), "technologies", "Physical layers through application profiles"), (str(len(self.service.list_ports())), "common OT ports", "Searchable by number or protocol"), ("9", "field tools", "Local calculations with no live connections")]
        for column, (value, label, note) in enumerate(metrics):
            frame, box = card(f"{value}  {label}", note); grid.addWidget(frame, 0, column)
        layout.addLayout(grid)
        quick, ql = card("Quick paths", "Start with the job in front of you.")
        actions = QGridLayout()
        for index, (label, target) in enumerate([("Decode Modbus frame", "Modbus Toolkit"), ("Calculate a subnet", "Network Toolkit"), ("Compare protocols", "Compare"), ("Trace a technology stack", "Hierarchy Explorer"), ("Look up port 44818", "Port Lookup"), ("Open fault checklists", "Troubleshooting")]):
            button = QPushButton(label); button.clicked.connect(lambda checked=False, name=target: self.navigate(name)); actions.addWidget(button, index // 3, index % 3)
        ql.addLayout(actions); layout.addWidget(quick)
        maps, ml = card("Relationship maps", "Common paths from supervisory software to field devices.")
        map_grid = QGridLayout()
        relationships = [("SIEMENS-STYLE", "SCADA / HMI  →  OPC UA  →  PLC\nPROFINET  →  Remote I/O  →  IO-Link  →  Sensor"), ("ROCKWELL-STYLE", "SCADA  →  OPC UA  →  ControlLogix\nEtherNet/IP  →  Remote I/O / Drive"), ("MODBUS", "SCADA  →  Modbus TCP  →  Gateway\nModbus RTU  →  Energy Meter"), ("CAN", "Controller  →  CAN  →  CANopen\nDrive / Encoder / I/O")]
        for i, (name, chain) in enumerate(relationships):
            panel, pl = card(name, chain); map_grid.addWidget(panel, i // 2, i % 2)
        ml.addLayout(map_grid); layout.addWidget(maps); layout.addStretch(); return scroll

    def _communications(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("Communications library", "Classification is explicit: an electrical interface is not the same thing as an application protocol.", "CURATED OFFLINE REFERENCE"))
        for category in self.service.list_categories():
            section, box = card(category)
            grid = QGridLayout(); technologies = self.service.list_technologies(category)
            for index, item in enumerate(technologies):
                button = QPushButton(f"{item.name}\n{item.classification}"); button.setMinimumHeight(58); button.setStyleSheet("text-align:left;padding:9px"); button.clicked.connect(lambda checked=False, tech_id=item.id: self.show_technology(tech_id)); grid.addWidget(button, index // 3, index % 3)
            box.addLayout(grid); layout.addWidget(section)
        layout.addStretch(); return scroll

    def show_technology(self, technology_id: str) -> None:
        try: item = self.service.get_technology(technology_id)
        except KeyError: return
        key = "Technology Detail"
        if key in self.pages: self.stack.removeWidget(self.pages[key]); self.pages[key].deleteLater()
        scroll, _, layout = self._page()
        head = QHBoxLayout(); head.addWidget(title_block(item.name, item.overview, item.acronym), 1)
        favorite = QPushButton("Remove favorite" if item.id in self.service.favorites() else "Add favorite")
        def toggle() -> None:
            enabled = item.id not in self.service.favorites(); self.service.set_favorite(item.id, enabled); favorite.setText("Remove favorite" if enabled else "Add favorite")
            old_page = self.pages.pop("Favorites", None)
            if old_page is not None:
                self.stack.removeWidget(old_page); old_page.deleteLater()
        favorite.clicked.connect(toggle); head.addWidget(favorite, 0, Qt.AlignmentFlag.AlignTop); layout.addLayout(head)
        badge = QLabel(item.classification); badge.setObjectName("Badge"); badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed); layout.addWidget(badge)
        fields = [("Where it fits", f"Category: {item.category}\nRuns over: {format_value([self._name(x) for x in item.runs_over])}"), ("Communication stack", f"Architecture: {item.architecture or '—'}\nMedium: {item.physical_medium or '—'}\nTopology: {item.topology or '—'}"), ("Addressing & performance", f"Addressing: {item.addressing or '—'}\nSpeed: {item.speed or '—'}\nPorts: {format_value(item.ports)}"), ("Key concepts", format_value(item.key_concepts)), ("Typical devices", format_value(item.typical_devices)), ("Typical applications", format_value(item.applications)), ("Advantages", format_value(item.advantages)), ("Limitations", format_value(item.limitations)), ("Common faults", "\n".join(f"• {x}" for x in item.faults)), ("Troubleshooting", "\n".join(f"{i}. {x}" for i, x in enumerate(item.troubleshooting, 1))), ("Related technologies", format_value([self._name(x) for x in item.related])), ("Standards / organization", f"{item.organization or '—'}\n{item.standard or '—'}\nFiles: {format_value(item.files)}")]
        grid = QGridLayout(); grid.setSpacing(12)
        for i, (heading, text) in enumerate(fields):
            panel, pl = card(heading, text); grid.addWidget(panel, i // 2, i % 2)
        layout.addLayout(grid); layout.addStretch(); self.pages[key] = scroll; self.stack.addWidget(scroll); self.stack.setCurrentWidget(scroll)

    def _name(self, technology_id: str) -> str:
        try: return self.service.get_technology(technology_id).name
        except KeyError: return technology_id.upper()

    def _hierarchy(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("Hierarchy explorer", "Select a technology to see what it runs on, what builds on it, and adjacent technologies.", "STACK & RELATIONSHIPS"))
        picker = QComboBox()
        for item in self.service.list_technologies(): picker.addItem(item.name, item.id)
        layout.addWidget(picker)
        container = QWidget(); grid = QGridLayout(container); layout.addWidget(container)
        def refresh() -> None:
            while grid.count():
                child = grid.takeAt(0).widget()
                if child: child.deleteLater()
            result = self.service.hierarchy(picker.currentData()); item = result["technology"]
            fields = [("WHAT IT IS", f"{item.classification}\n\n{item.overview}"), ("RUNS OVER", "\n".join(x.name for x in result["runs_over"]) or "No lower layer modeled"), ("USED BY", "\n".join(x.name for x in result["used_by"]) or "No higher profiles modeled"), ("RELATED", "\n".join(x.name for x in result["related"]) or "No direct relations"), ("TYPICAL DEVICES", format_value(item.typical_devices)), ("APPLICATIONS", format_value(item.applications)), ("ORGANIZATION", f"{item.organization}\n{item.standard}")]
            for i, (heading, body) in enumerate(fields): panel, _ = card(heading, body); grid.addWidget(panel, i // 2, i % 2)
        picker.currentIndexChanged.connect(refresh); refresh(); layout.addStretch(); return scroll

    def _compare(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("Communication comparison", "Compare any two supported technologies from structured reference fields.", "SIDE-BY-SIDE"))
        controls = QHBoxLayout(); left = QComboBox(); right = QComboBox()
        technologies = self.service.list_technologies()
        for item in technologies: left.addItem(item.name, item.id); right.addItem(item.name, item.id)
        right.setCurrentIndex(next((i for i, x in enumerate(technologies) if x.id == "ethernet-ip"), 1)); controls.addWidget(left); controls.addWidget(QLabel("VERSUS")); controls.addWidget(right); layout.addLayout(controls)
        table = QTableWidget(); table.setColumnCount(3); table.setHorizontalHeaderLabels(["Property", "Technology A", "Technology B"]); table.verticalHeader().hide(); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); table.setAlternatingRowColors(True); table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); table.setMinimumHeight(540); layout.addWidget(table)
        def refresh() -> None:
            result = self.service.compare(left.currentData(), right.currentData()); table.setHorizontalHeaderLabels(["Property", result.left.name, result.right.name]); table.setRowCount(len(result.rows))
            for row, values in enumerate(result.rows):
                for col, value in enumerate(values): table.setItem(row, col, QTableWidgetItem(value))
            table.resizeRowsToContents()
        left.currentIndexChanged.connect(refresh); right.currentIndexChanged.connect(refresh); refresh(); return scroll

    def _data_tools(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("Data conversion toolkit", "Inspect PLC integers, bits, floating-point values, and byte order.", "LOCAL CALCULATORS"))
        tabs = QTabWidget(); tabs.addTab(self._number_tab(), "Number"); tabs.addTab(self._bit_tab(), "Bit inspector"); tabs.addTab(self._ieee_tab(), "IEEE-754"); tabs.addTab(self._endian_tab(), "Endianness"); tabs.setMinimumHeight(590); layout.addWidget(tabs); return scroll

    def _number_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); intro = QLabel("Enter decimal or use prefixes 0x, 0b, 0o, or PLC-style 16#."); intro.setObjectName("Muted"); layout.addWidget(intro)
        row = QHBoxLayout(); value = QLineEdit("123"); kind = QComboBox(); kind.addItems(["UInt8", "Int8", "UInt16", "Int16", "UInt32", "Int32", "UInt64", "Int64"]); run = QPushButton("Convert"); run.setObjectName("Primary"); row.addWidget(value, 2); row.addWidget(kind); row.addWidget(run); layout.addLayout(row); output = output_box(); layout.addWidget(output)
        def calculate() -> None:
            try:
                result = self.service.number_conversion(value.text(), kind.currentText()); output.setPlainText("\n".join(f"{key.upper():8}  {format_value(val)}" for key, val in result.items() if key != "bits"))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); value.returnPressed.connect(calculate); calculate(); layout.addStretch(); return page

    def _bit_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); controls = QHBoxLayout(); value = QLineEdit("16#8401"); bits = QComboBox(); bits.addItems(["8", "16", "32", "64"]); run = QPushButton("Inspect"); run.setObjectName("Primary"); controls.addWidget(value, 1); controls.addWidget(bits); controls.addWidget(run); layout.addLayout(controls)
        summary = QLabel(); summary.setObjectName("Section"); layout.addWidget(summary); bit_grid = QGridLayout(); layout.addLayout(bit_grid); checks: list[QCheckBox] = []
        def render(raw: int | None = None) -> None:
            try:
                width = int(bits.currentText())
                if raw is None: raw = int(self.service.number_conversion(value.text(), f"UInt{width}")["decimal"])
                while bit_grid.count():
                    widget = bit_grid.takeAt(0).widget()
                    if widget: widget.deleteLater()
                checks.clear()
                for position in reversed(range(width)):
                    check = QCheckBox(f"{position}"); check.setChecked(bool(raw & (1 << position))); check.setToolTip(f"Bit {position}"); checks.append(check); bit_grid.addWidget(check, (width - 1 - position) // 16, (width - 1 - position) % 16)
                    check.toggled.connect(update_from_bits)
                update_summary(raw, width)
            except Exception as exc: self._error(exc)
        def update_summary(raw: int, width: int) -> None:
            result = self.service.number_conversion(str(raw), f"UInt{width}"); summary.setText(f"DEC {result['decimal']}    HEX {result['hex']}    BIN {result['binary']}")
        def update_from_bits() -> None:
            width = int(bits.currentText()); raw = 0
            for index, check in enumerate(checks):
                position = width - 1 - index
                if check.isChecked(): raw |= 1 << position
            update_summary(raw, width); value.setText(str(raw))
        run.clicked.connect(render); bits.currentIndexChanged.connect(render); render(); layout.addStretch(); return page

    def _ieee_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); precision = QComboBox(); precision.addItems(["Float32", "Float64"]); layout.addWidget(precision)
        first, fl = card("Float → Hex"); value = QLineEdit("123.0"); button = QPushButton("Encode"); out = output_box(); row = QHBoxLayout(); row.addWidget(value); row.addWidget(button); fl.addLayout(row); fl.addWidget(out); layout.addWidget(first)
        second, sl = card("Hex → Float"); hex_value = QLineEdit("42F60000"); decode = QPushButton("Decode"); decoded = output_box(); row2 = QHBoxLayout(); row2.addWidget(hex_value); row2.addWidget(decode); sl.addLayout(row2); sl.addWidget(decoded); layout.addWidget(second)
        def bits() -> int: return 32 if precision.currentIndex() == 0 else 64
        def encode() -> None:
            try: out.setPlainText(self.service.ieee_to_hex(float(value.text()), bits()))
            except Exception as exc: self._error(exc)
        def decode_value() -> None:
            try: decoded.setPlainText(format_value(self.service.ieee_from_hex(hex_value.text(), bits())))
            except Exception as exc: self._error(exc)
        button.clicked.connect(encode); decode.clicked.connect(decode_value); encode(); decode_value(); return page

    def _endian_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); row = QHBoxLayout(); value = QLineEdit("42 F6 00 00"); run = QPushButton("Interpret four bytes"); run.setObjectName("Primary"); row.addWidget(value); row.addWidget(run); layout.addLayout(row)
        table = QTableWidget(0, 5); table.setHorizontalHeaderLabels(["Order", "Operation", "Hex", "UInt32 / Int32", "Float32"]); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); table.verticalHeader().hide(); layout.addWidget(table)
        def calculate() -> None:
            try:
                result = self.service.endian_decode(value.text()); table.setRowCount(len(result))
                for r, (order, data) in enumerate(result.items()):
                    values = [order, data["operation"], data["hex"], f"{data['uint32']} / {data['int32']}", format_value(data["float32"])]
                    for c, text in enumerate(values): table.setItem(r, c, QTableWidgetItem(str(text)))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); return page

    def _modbus_tools(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("Modbus toolkit", "Resolve addressing conventions, register layouts, CRCs, and basic RTU frames.", "REGISTER WORKBENCH")); tabs = QTabWidget(); tabs.addTab(self._modbus_address_tab(), "Address"); tabs.addTab(self._register_tab(), "Registers"); tabs.addTab(self._crc_tab(), "CRC"); tabs.addTab(self._frame_tab(), "Frame decoder"); tabs.addTab(self._modbus_reference_tab(), "Reference"); tabs.setMinimumHeight(590); layout.addWidget(tabs); return scroll

    def _modbus_address_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); warning = QLabel("[!] Vendors may use zero-based, one-based, or traditional 4xxxx notation. Confirm the device manual."); warning.setStyleSheet("color:#ffc76b"); warning.setWordWrap(True); layout.addWidget(warning); row = QHBoxLayout(); value = QLineEdit("40001"); run = QPushButton("Convert"); run.setObjectName("Primary"); row.addWidget(value); row.addWidget(run); layout.addLayout(row); output = output_box(); layout.addWidget(output)
        def calculate() -> None:
            try: output.setPlainText("\n".join(f"{k.replace('_',' ').title()}: {v}" for k, v in self.service.modbus_address(value.text()).items()))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); layout.addStretch(); return page

    def _register_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); label = QLabel("Enter two or four 16-bit registers (decimal or 0x-prefixed), separated by spaces or commas."); label.setObjectName("Muted"); layout.addWidget(label); row = QHBoxLayout(); value = QLineEdit("0x42F6 0x0000"); run = QPushButton("Decode"); run.setObjectName("Primary"); row.addWidget(value); row.addWidget(run); layout.addLayout(row); output = output_box(); output.setMinimumHeight(350); layout.addWidget(output)
        def calculate() -> None:
            try:
                registers = [int(part, 0) for part in value.text().replace(",", " ").split()]; result = self.service.modbus_registers(registers); lines = []
                for order, data in result.items(): lines.append(f"[{order}]  " + "  ·  ".join(f"{k}={format_value(v)}" for k, v in data.items()))
                output.setPlainText("\n".join(lines))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); return page

    def _crc_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); row = QHBoxLayout(); value = QLineEdit("01 03 00 00 00 02"); run = QPushButton("Calculate CRC-16"); run.setObjectName("Primary"); row.addWidget(value); row.addWidget(run); layout.addLayout(row); output = output_box(); layout.addWidget(output)
        def calculate() -> None:
            try:
                result = self.service.modbus_crc(value.text()); output.setPlainText(f"CRC VALUE           {result['crc']}\nTRANSMISSION ORDER  {result['transmission_order']}")
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); layout.addStretch(); return page

    def _frame_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); row = QHBoxLayout(); value = QLineEdit("01 03 00 00 00 02 C4 0B"); run = QPushButton("Decode frame"); run.setObjectName("Primary"); row.addWidget(value); row.addWidget(run); layout.addLayout(row); output = output_box(); output.setMinimumHeight(250); layout.addWidget(output)
        def calculate() -> None:
            try:
                result = self.service.modbus_frame(value.text()); data = asdict(result); output.setPlainText("\n".join(f"{k.replace('_',' ').upper():18} {format_value(v)}" for k, v in data.items()))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); return page

    def _modbus_reference_tab(self) -> QWidget:
        page = QWidget(); layout = QHBoxLayout(page); functions = {"01":"Read Coils","02":"Read Discrete Inputs","03":"Read Holding Registers","04":"Read Input Registers","05":"Write Single Coil","06":"Write Single Register","15":"Write Multiple Coils","16":"Write Multiple Registers","22":"Mask Write Register","23":"Read/Write Multiple Registers","43":"Encapsulated Interface Transport"}; exceptions = {"01":"Illegal Function","02":"Illegal Data Address","03":"Illegal Data Value","04":"Server Device Failure","05":"Acknowledge","06":"Device Busy","08":"Memory Parity Error","10":"Gateway Path Unavailable","11":"Gateway Target Failed to Respond"}
        for heading, data in (("Function codes", functions), ("Exception codes", exceptions)):
            panel, pl = card(heading); text = QLabel("\n".join(f"{code}   {name}" for code, name in data.items())); text.setWordWrap(True); pl.addWidget(text); layout.addWidget(panel)
        return page

    def _network_tools(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("Network toolkit", "Calculate IPv4 boundaries, compare subnets, validate address lists, and prepare safe diagnostic commands.", "IP WORKBENCH")); tabs = QTabWidget(); tabs.addTab(self._subnet_tab(), "Subnet"); tabs.addTab(self._same_subnet_tab(), "Same subnet"); tabs.addTab(self._validation_tab(), "IP validation"); tabs.addTab(self._commands_tab(), "Commands"); tabs.setMinimumHeight(590); layout.addWidget(tabs); return scroll

    def _subnet_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); row = QHBoxLayout(); ip = QLineEdit("192.168.1.20"); mask = QLineEdit("/24"); run = QPushButton("Calculate"); run.setObjectName("Primary"); row.addWidget(ip); row.addWidget(mask); row.addWidget(run); layout.addLayout(row); output = output_box(); output.setMinimumHeight(250); layout.addWidget(output)
        def calculate() -> None:
            try:
                result = asdict(self.service.subnet(ip.text(), mask.text())); output.setPlainText("\n".join(f"{k.replace('_',' ').upper():18} {v}" for k, v in result.items()))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); layout.addStretch(); return page

    def _same_subnet_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); grid = QGridLayout(); first = QLineEdit("192.168.1.20"); second = QLineEdit("192.168.1.99"); mask = QLineEdit("24"); grid.addWidget(QLabel("Device A"), 0, 0); grid.addWidget(first, 0, 1); grid.addWidget(QLabel("Device B"), 1, 0); grid.addWidget(second, 1, 1); grid.addWidget(QLabel("CIDR / mask"), 2, 0); grid.addWidget(mask, 2, 1); layout.addLayout(grid); run = QPushButton("Check networks"); run.setObjectName("Primary"); layout.addWidget(run); output = output_box(); layout.addWidget(output)
        def calculate() -> None:
            try:
                result = self.service.same_subnet(first.text(), second.text(), mask.text()); output.setPlainText(("SAME SUBNET" if result["same"] else "DIFFERENT SUBNETS") + f"\nDevice A network: {result['network_a']}\nDevice B network: {result['network_b']}")
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); layout.addStretch(); return page

    def _validation_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); note = QLabel("Enter one IPv4 address per line. Optional CIDR identifies network and broadcast addresses."); note.setObjectName("Muted"); layout.addWidget(note); addresses = QTextEdit("192.168.1.0\n192.168.1.20\n192.168.1.20\n192.168.1.255\n999.1.1.1"); cidr = QLineEdit("24"); cidr.setPlaceholderText("Optional CIDR or mask"); run = QPushButton("Validate"); run.setObjectName("Primary"); layout.addWidget(addresses); row = QHBoxLayout(); row.addWidget(cidr); row.addWidget(run); layout.addLayout(row); output = output_box(); layout.addWidget(output)
        def calculate() -> None:
            try:
                values = [x for x in addresses.toPlainText().splitlines() if x.strip()]; results = self.service.validate_ips(values, cidr.text() or None); output.setPlainText("\n".join(f"{x['ip']:16}  {'VALID' if x['valid'] else 'INVALID':7}  {x['kind'].upper():9}  {'DUPLICATE' if x['duplicate'] else ''}" for x in results))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); return page

    def _commands_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); notice = QLabel("Commands are generated for review only. This application never executes them."); notice.setStyleSheet("color:#ffc76b"); layout.addWidget(notice); row = QHBoxLayout(); host = QLineEdit("192.168.1.20"); port = QSpinBox(); port.setRange(0, 65535); port.setValue(502); port.setSpecialValueText("No port"); run = QPushButton("Generate"); run.setObjectName("Primary"); row.addWidget(host); row.addWidget(port); row.addWidget(run); layout.addLayout(row); output = output_box(); output.setMinimumHeight(360); layout.addWidget(output)
        def calculate() -> None:
            try:
                result = self.service.commands(host.text(), port.value() or None); output.setPlainText("WINDOWS / POWERSHELL\n" + "\n".join(result["windows"]) + "\n\nLINUX\n" + "\n".join(result["linux"]))
            except Exception as exc: self._error(exc)
        run.clicked.connect(calculate); calculate(); return page

    def _ports(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("OT port lookup", "Search by port number, protocol name, or technology.", "QUICK REFERENCE")); query = QLineEdit(); query.setPlaceholderText("Try 502, MQTT, CIP, or time"); query.setClearButtonEnabled(True); layout.addWidget(query); table = QTableWidget(); table.setColumnCount(5); table.setHorizontalHeaderLabels(["Port", "Transport", "Protocol", "Technology", "Purpose"]); table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); table.verticalHeader().hide(); table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); table.setAlternatingRowColors(True); layout.addWidget(table)
        def refresh() -> None:
            entries = self.service.list_ports(query.text()); table.setRowCount(len(entries))
            for row, item in enumerate(entries):
                for col, value in enumerate((item.port, item.transport, item.name, item.technology, item.purpose)): table.setItem(row, col, QTableWidgetItem(value))
        query.textChanged.connect(refresh); refresh(); return scroll

    def _troubleshooting(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("Troubleshooting quick guides", "Work upward: Physical → Link → Addressing → Network → Protocol configuration → Application.", "FAULT ISOLATION")); guides = self.service.list_troubleshooting()
        for item in self.service.list_technologies():
            if item.id not in guides: continue
            panel, pl = card(item.name, "\n".join(f"{i}. {step}" for i, step in enumerate(guides[item.id], 1))); open_button = QPushButton("Open technology page"); open_button.clicked.connect(lambda checked=False, tech_id=item.id: self.show_technology(tech_id)); pl.addWidget(open_button, 0, Qt.AlignmentFlag.AlignLeft); layout.addWidget(panel)
        layout.addStretch(); return scroll

    def _glossary(self) -> QWidget:
        scroll, _, layout = self._page(); layout.addWidget(title_block("OT communications glossary", "Search practical terms, configuration files, services, and network concepts.", "FIELD TERMINOLOGY")); query = QLineEdit(); query.setPlaceholderText("Search terms or definitions"); query.setClearButtonEnabled(True); layout.addWidget(query); listing = QListWidget(); listing.setMinimumHeight(560); layout.addWidget(listing)
        def refresh() -> None:
            listing.clear()
            for item in self.service.list_glossary(query.text()): listing.addItem(f"{item.term}  ·  {item.category}\n{item.definition}\nRelated: {format_value(item.related)}")
        query.textChanged.connect(refresh); refresh(); return scroll

    def _favorites(self) -> QWidget:
        scroll, _, layout = self._page(); ids = self.service.favorites(); layout.addWidget(title_block("Favorites", f"{len(ids)} saved reference items on this device.", "LOCAL COLLECTION")); listing = ClickableList(); listing.chosen.connect(self.show_technology); layout.addWidget(listing)
        for tech_id in sorted(ids):
            try:
                item = self.service.get_technology(tech_id); row = QListWidgetItem(f"FAVORITE  ·  {item.name}\n{item.classification} · {item.category}"); row.setData(Qt.ItemDataRole.UserRole, item.id); listing.addItem(row)
            except KeyError: pass
        if not ids: listing.addItem("No favorites yet. Open a technology page and choose Add favorite.")
        layout.addStretch(); return scroll
