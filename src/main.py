import sys
from datetime import datetime

from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import QTimer, QObject, QThread, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QMainWindow,
    QHeaderView,
    QLabel,
)

from hwmon_source import HwmonSensors
from liquidctl_source import LiquidctlSensors
from sensors_tree import DeviceTreeItem, SensorTreeItem
from src.graphing import GraphingWindow


class PollSourcesWorker(QObject):
    stopping = pyqtSignal()

    def __init__(self, hwmon_source, liquidctl_source):
        super().__init__()

        self.polling_timer = None
        self.hwmon_source = hwmon_source
        self.liquidctl_source = liquidctl_source
        self.stopping.connect(self.stop)

    @pyqtSlot()
    def start(self):
        self.polling_timer = QTimer()
        self.polling_timer.timeout.connect(self.update_sensors)
        self.polling_timer.start(1000)  # TODO: Make interval configurable

    @pyqtSlot()
    def stop(self):
        self.polling_timer.stop()

    def update_sensors(self):
        self.hwmon_source.update_sensors()
        self.liquidctl_source.update_sensors()


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "Lensors"
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480 * 2
        self.sensors_tree = None
        self.hwmon = None
        self.liquidctl = None
        self.liquidctl_tree = None
        self.poll_worker = None
        self.poll_worker_thread = None
        self.graphing_window = GraphingWindow()

        QtCore.QDir.addSearchPath("icons", "resources/icons/")

        self._init_ui()

    # Thanks to https://stackoverflow.com/a/68402005
    def _center_window(self):
        frame_geo = self.frameGeometry()
        screen = self.window().windowHandle().screen()
        center_loc = screen.geometry().center()
        frame_geo.moveCenter(center_loc)
        self.move(frame_geo.topLeft())

    def show_permanent_status_message(self, text):
        self.status_label.setText(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

    def hwmon_row_changed(self, item: SensorTreeItem, column):
        sensor = item.sensor

        if item.checkState(4) == Qt.CheckState.Checked:
            if sensor._plot_line is None:
                sensor._plot_line = self.graphing_window.graphWidget.plot(
                    list(sensor._values_over_time.keys()),
                    list(sensor._values_over_time.values()),
                )
        else:
            if sensor._plot_line:
                self.graphing_window.graphWidget.removeItem(sensor._plot_line)

    def init_sensors_tab(self):
        if self.hwmon is None:
            self.hwmon = HwmonSensors()
            self.hwmon.read()

        if self.liquidctl is None:
            self.liquidctl = LiquidctlSensors()
            self.liquidctl.read()

        self.sensors_tree = self.hwmon.get_tree_widget()
        self.sensors_tree.setSortingEnabled(True)
        self.sensors_tree.expandAll()
        self.sensors_tree.header().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.sensors_tree.itemChanged.connect(self.hwmon_row_changed)
        self.sensors_tree.header().setStretchLastSection(False)

        self.liquidctl_tree = self.liquidctl.get_tree_widget()
        self.liquidctl_tree.setSortingEnabled(True)
        self.liquidctl_tree.expandAll()
        self.liquidctl_tree.header().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.liquidctl_tree.header().setStretchLastSection(False)

        sensors_layout = QVBoxLayout()
        sensors_layout.addWidget(self.sensors_tree)
        self.sensors_widget = QWidget()
        self.sensors_widget.setLayout(sensors_layout)
        self.tab_widget.addTab(self.sensors_widget, "HWMON")

        liquidctl_layout = QVBoxLayout()
        liquidctl_layout.addWidget(self.liquidctl_tree)
        self.liquidctl_widget = QWidget()
        self.liquidctl_widget.setLayout(liquidctl_layout)
        self.tab_widget.addTab(self.liquidctl_widget, "Liquidctl")

    def _init_ui(self):
        uic.loadUi("src/ui/mainwindow.ui", self)

        self.setWindowTitle(self.title)
        self.init_sensors_tab()

        # Qt Designer apparently does not do this for us
        self.centralWidget().setContentsMargins(9, 6, 9, 6)

        # Add permanent QLabel to status bar
        self.status_label = QLabel()
        self.statusBar().addPermanentWidget(self.status_label)

        # Connect buttons
        self.actionStartMonitoring.triggered.connect(self.start_polling)
        self.actionStopMonitoring.triggered.connect(self.stop_polling)
        self.actionReload.triggered.connect(self.oneshot_reload)
        self.actionGraphing.triggered.connect(self.show_graphing)

        self.show()
        self._center_window()

        self.init_polling()

    def init_polling(self):
        self.poll_worker_thread = QThread()
        self.poll_worker = PollSourcesWorker(self.hwmon, self.liquidctl)
        self.poll_worker.moveToThread(self.poll_worker_thread)

        self.poll_worker_thread.started.connect(self.poll_worker.start)
        self.poll_worker_thread.start()

        self.show_permanent_status_message("Started monitoring.")

    def start_polling(self):
        self.poll_worker.start()

        self.show_permanent_status_message("Started monitoring.")

    def stop_polling(self):
        self.poll_worker.stop()

        self.show_permanent_status_message("Stopped monitoring.")

    def oneshot_reload(self):
        self.hwmon.update_sensors()
        self.liquidctl.update_sensors()

    def show_graphing(self):
        if self.graphing_window.isVisible():
            self.graphing_window.hide()
        else:
            self.graphing_window.show()

    def closeEvent(self, a0: QtGui.QCloseEvent):
        # TODO: Sometimes gives an error
        self.poll_worker.stopping.emit()
        self.poll_worker_thread.quit()
        self.poll_worker_thread.wait()

        self.graphing_window.close()

    def on_help_button_click(self):
        pass


if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


app = QApplication(sys.argv)
ex = App()
sys.exit(app.exec())
