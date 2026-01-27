import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPainter, QColor, QPalette
from PySide6.QtCharts import QChart, QChartView, QLineSeries

from main import take_snapshot, engine_tick, MB


class RamMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyRamUtil")

        root_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        # Overview tab
        self.overview_tab = QWidget()
        overview_layout = QVBoxLayout(self.overview_tab)

        self.system_label = QLabel("System status")
        overview_layout.addWidget(self.system_label)

        self.role_label = QLabel("RAM usage by category")
        overview_layout.addWidget(self.role_label)

        self.series_used = QLineSeries()
        self.series_total = QLineSeries()

        self.series_used.setName("Used RAM")
        self.series_total.setName("Total RAM")

        self.series_used.setColor(QColor(220, 80, 80))
        self.series_total.setColor(QColor(120, 120, 120))

        self.chart = QChart()
        self.chart.addSeries(self.series_used)
        self.chart.addSeries(self.series_total)
        self.chart.createDefaultAxes()
        self.chart.setTitle("RAM Usage Over Time")

        self.chart.setBackgroundBrush(QColor(30, 30, 30))
        self.chart.setTitleBrush(QColor(220, 220, 220))

        axis_x, axis_y = self.chart.axes()
        axis_x.setLabelsColor(QColor(180, 180, 180))
        axis_y.setLabelsColor(QColor(180, 180, 180))
        axis_x.setGridLineColor(QColor(60, 60, 60))
        axis_y.setGridLineColor(QColor(60, 60, 60))

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        overview_layout.addWidget(self.chart_view)

        self.diff_table = QTableWidget(0, 3)
        self.diff_table.setHorizontalHeaderLabels(
            ["Process", "Change (MB)", "RSS (MB)"]
        )
        overview_layout.addWidget(self.diff_table)

        self.tabs.addTab(self.overview_tab, "Overview")

        # Processes tab
        self.process_tab = QWidget()
        process_layout = QVBoxLayout(self.process_tab)

        self.process_table = QTableWidget(0, 4)
        self.process_table.setStyleSheet(
            """
            QTableWidget {
                background-color: #181818;
                color: #dcdcdc;
                gridline-color: #2a2a2a;
            }

            QTableWidget::item {
                color: #dcdcdc;
            }

            QHeaderView::section {
                background-color: #222222;
                color: #dcdcdc;
                padding: 4px;
                border: 1px solid #333333;
            }
            """
        )

        self.process_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Private MB", "RSS MB"]
        )
        self.process_table.setSortingEnabled(True)

        process_layout.addWidget(self.process_table)
        self.tabs.addTab(self.process_tab, "Processes")

        self.prev_snapshot = take_snapshot()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(5000)

        self.update_ui()

    def render_diff(self, diff):
        self.diff_table.setRowCount(0)

        for m in diff["memory_changes"]:
            row = self.diff_table.rowCount()
            self.diff_table.insertRow(row)

            self.diff_table.setItem(row, 0, QTableWidgetItem(m["name"]))
            self.diff_table.setItem(row, 1, QTableWidgetItem(str(m["delta"] // MB)))
            self.diff_table.setItem(row, 2, QTableWidgetItem(str(m["rss"] // MB)))

    def render_processes(self, processes):
        self.process_table.setRowCount(0)

        for p in processes.values():
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)

            self.process_table.setItem(row, 0, QTableWidgetItem(p["name"]))
            self.process_table.setItem(row, 1, QTableWidgetItem(p["role"]))
            self.process_table.setItem(
                row, 2, QTableWidgetItem(str((p.get("private") or 0) // MB))
            )
            self.process_table.setItem(
                row, 3, QTableWidgetItem(str(p["rss"] // MB))
            )

    def update_ui(self):
        self.prev_snapshot, state = engine_tick(self.prev_snapshot)
        sys_mem = state["system"]

        self.system_label.setText(
            f"System: {state['condition'].upper()} | "
            f"Used: {sys_mem['used'] // MB} MB | "
            f"Available: {sys_mem['available'] // MB} MB\n"
            f"{state['condition_text']}"
        )

        roles = state["roles"]
        self.role_label.setText(
            "Private memory — Apps: {0} MB | Services: {1} MB | UI: {2} MB".format(
                roles["user_app"] // MB,
                roles["system_service"] // MB,
                roles["system_ui"] // MB,
            )
        )

        self.render_diff(state["diff"])

        x = self.series_used.count()
        used_mb = sys_mem["used"] // MB
        total_mb = sys_mem["total"] // MB

        self.series_used.append(x, used_mb)
        self.series_total.append(x, total_mb)

        self.chart.axisX().setRange(max(0, x - 60), x)
        self.chart.axisY().setRange(0, total_mb)

        self.render_processes(state["processes"])


app = QApplication(sys.argv)

dark = QPalette()
dark.setColor(QPalette.Window, QColor(30, 30, 30))
dark.setColor(QPalette.WindowText, QColor(220, 220, 220))
dark.setColor(QPalette.Base, QColor(25, 25, 25))
dark.setColor(QPalette.Text, QColor(220, 220, 220))
dark.setColor(QPalette.Button, QColor(45, 45, 45))
dark.setColor(QPalette.ButtonText, QColor(220, 220, 220))
dark.setColor(QPalette.Highlight, QColor(90, 140, 255))

app.setPalette(dark)

window = RamMonitor()
window.resize(900, 600)
window.show()

sys.exit(app.exec())
