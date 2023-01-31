import sys

from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QTimer, QEventLoop, QObject, QThread
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMainWindow,
    QHeaderView,
)
from PyQt6.QtGui import QAction

from hwmon_source import HwmonSensors
from liquidctl_source import LiquidctlSensors

class PollSourcesWorker(QObject):
    def update_sensors(self):
        self.hwmon_source.update_sensors()
        self.liquidctl_source.update_sensors()

    def __init__(self, hwmon_source, liquidctl_source, parent=None):
        super().__init__(parent)
        self.polling_timer = None

        self.hwmon_source = hwmon_source
        self.liquidctl_source = liquidctl_source

        self.polling_timer = QTimer()
        self.polling_timer.timeout.connect(self.update_sensors)

    def run(self):
        # TODO: Make interval configurable
        self.polling_timer.start(1000)

    def moveToThread(self, thread):
        thread.finished.connect(self.polling_timer.stop)
        super().moveToThread(thread)

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

        QtCore.QDir.addSearchPath("icons", "resources/icons/")

        self._init_ui()

    # Thanks to https://stackoverflow.com/a/68402005
    def _center_window(self):
        frame_geo = self.frameGeometry()
        screen = self.window().windowHandle().screen()
        center_loc = screen.geometry().center()
        frame_geo.moveCenter(center_loc)
        self.move(frame_geo.topLeft())

    """
    TODO: Opcije
    - Show empty entries
    - Retrieve feature labels
    - Sort by default?
    - Show PWM values?
    - All values/simple view (sensors)
    """

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
        self.tab_widget.addTab(self.sensors_widget, "Sensors")

        liquidctl_layout = QVBoxLayout()
        liquidctl_layout.addWidget(self.liquidctl_tree)
        self.liquidctl_widget = QWidget()
        self.liquidctl_widget.setLayout(liquidctl_layout)
        self.tab_widget.addTab(self.liquidctl_widget, "Liquidctl")

    def _init_menubar(self):
        tools_menu = self.menuBar().addMenu("Tools")
        button_action = QAction("Refresh", self)
        button_action.triggered.connect(self.on_refresh_button_click)
        tools_menu.addAction(button_action)

        help_menu = self.menuBar().addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.on_help_button_click)
        help_menu.addAction(about_action)

    def _init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self._init_menubar()

        self.tab_widget = QTabWidget()
        self.init_sensors_tab()

        self.setCentralWidget(self.tab_widget)

        self.show()
        self._center_window()

        # Start polling sensor sources
        self.worker = PollSourcesWorker(self.hwmon, self.liquidctl)
        self.polling_thread = QThread(self)
        self.worker.moveToThread(self.polling_thread)
        self.polling_thread.start()

        self.worker.run()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.polling_thread.quit()

    def on_refresh_button_click(self):
        # TODO
        self.hwmon.update_sensors()
        self.liquidctl.update_sensors()

    def on_help_button_click(self):
        pass


app = QApplication(sys.argv)
ex = App()
sys.exit(app.exec())
