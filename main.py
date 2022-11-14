import os
import sys

from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMainWindow,
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt6.QtGui import QAction


class HwmonSensors:
    HWMON_PATH = "/sys/class/hwmon"

    class HwmonDevice:
        def __init__(self, name):
            self.name = name
            self.readings = {}

        def add_sensor(self, name, value):
            if name not in self.readings:
                self.readings[name] = value

    def __init__(self):
        self.devices = list()

    def get_tree_widget(self):
        tree_widget = QTreeWidget()
        tree_widget.setColumnCount(2)  # name, value
        tree_widget.setHeaderLabels(["Name", "Value"])
        for device in self.devices:
            device_item = QTreeWidgetItem([device.name, ""])
            for name, value in device.readings.items():
                device_sensor_item = QTreeWidgetItem([name, value])
                device_item.addChild(device_sensor_item)
            tree_widget.addTopLevelItem(device_item)

        return tree_widget

    def read(self):
        hwmon_dirs = os.listdir(self.HWMON_PATH)
        for subdir in hwmon_dirs:
            subdir_path = os.path.join(self.HWMON_PATH, subdir)

            with open(os.path.join(subdir_path, "name")) as f:
                device_name = f.readline().strip()

            h_device = HwmonSensors.HwmonDevice(device_name)
            self.devices.append(h_device)

            # TODO: Icons, types. labels
            for sensor in os.listdir(subdir_path):
                sensor_path = os.path.join(subdir_path, sensor)
                if os.path.isfile(sensor_path):
                    if "_input" in sensor:
                        with open(sensor_path) as f:
                            try:
                                h_device.add_sensor(sensor, f.readline().strip())
                            except OSError:
                                pass  # TODO: Show error


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "Lensors"
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480 * 2
        self.sensors_tree = None

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

    def _refresh_sensors_widget(self):
        hwmon = HwmonSensors()
        hwmon.read()
        self.sensors_tree = hwmon.get_tree_widget()
        self.sensors_tree.setSortingEnabled(True)
        self.sensors_tree.expandAll()
        self.sensors_tree.header().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.sensors_tree.header().setStretchLastSection(False)

        if self.tabs_init is False:
            sensors_layout = QVBoxLayout()
            sensors_layout.addWidget(self.sensors_tree)
            self.sensors_widget = QWidget()
            self.sensors_widget.setLayout(sensors_layout)
            self.tab_widget.addTab(self.sensors_widget, "Sensors")
            self.tabs_init = True

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
        self.tabs_init = False
        self._refresh_sensors_widget()

        self.setCentralWidget(self.tab_widget)

        self.show()
        self._center_window()

    def on_refresh_button_click(self):
        self._refresh_sensors_widget()

    def on_help_button_click(self):
        pass


app = QApplication(sys.argv)
ex = App()
sys.exit(app.exec())
