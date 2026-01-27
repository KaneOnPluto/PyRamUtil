import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import QTimer

from main import take_snapshot, engine_tick  # main.py connection

class RamMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyRamUtil")

        self.layout = QVBoxLayout(self)

        self.system_label = QLabel("System status")
        self.layout.addWidget(self.system_label)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Process", "Change", "RSS"])
        self.layout.addWidget(self.table)

        self.prev_snapshot = take_snapshot()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(5000)  # 5 seconds

    def update_ui(self):
        self.prev_snapshot, state = engine_tick(self.prev_snapshot)

        sys_mem = state["system"]
        self.system_label.setText(
            f"Used: {sys_mem['used'] // (1024**2)} MB | "
            f"Available: {sys_mem['available'] // (1024**2)} MB"
        )

        self.render_diff(state["diff"])

    def render_diff(self, diff):
        self.table.setRowCount(0)

        for m in diff["memory_changes"]:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(m["name"]))
            self.table.setItem(
                row, 1,
                QTableWidgetItem(f"{m['delta'] // (1024**2)} MB")
            )
            self.table.setItem(
                row, 2,
                QTableWidgetItem(f"{m['rss'] // (1024**2)} MB")
            )

app = QApplication(sys.argv)
window = RamMonitor()
window.show()
sys.exit(app.exec())
    