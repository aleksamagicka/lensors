import os
import sys
from enum import Enum

from PyQt6 import QtCore, QtGui
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
        class HwmonSensor:
            class Type(Enum):
                Temp = 1
                Voltage = 2
                Fan = 3
                Current = 4
                Power = 5
                Intrusion = 6

            def __init__(self, label, internal_name, value_path):
                self.label = label

                self._value_path = value_path

                self._value = 0
                self._min_value = sys.maxsize
                self._max_value = -sys.maxsize - 1

                self._tree_item = QTreeWidgetItem(
                    [
                        label,
                        str(self._value),
                        str(self._min_value),
                        str(self._max_value),
                    ]
                )

                self._type = None
                # Determine type
                if "temp" in internal_name:
                    self._type = self.Type.Temp
                elif "in" in internal_name:
                    self._type = self.Type.Voltage
                elif "fan" in internal_name:
                    self._type = self.Type.Fan
                elif "curr" in internal_name:
                    self._type = self.Type.Current
                elif "power" in internal_name:
                    self._type = self.Type.Power
                elif "intrusion" in internal_name:
                    self._type = self.Type.Intrusion

                # Set icon
                feat_icon = None
                if self._type == self.Type.Temp:
                    feat_icon = "icons8-thermometer-96.png"
                elif self._type == self.Type.Current:
                    feat_icon = "icons8-high-voltage-96.png"
                elif self._type == self.Type.Voltage:
                    feat_icon = "icons8-voltmeter-100.png"
                elif self._type == self.Type.Power:
                    feat_icon = "icons8-shutdown-90.png"
                elif self._type == self.Type.Fan:
                    feat_icon = "icons8-fan-head-64.png"
                elif self._type == self.Type.Intrusion:
                    feat_icon = "icons8-hips-100.png"

                self._tree_item.setIcon(0, QtGui.QIcon(f"icons:{feat_icon}"))

            def value_to_string(self, value):
                if not type(value) == int:
                    return value

                if self._type == self.Type.Temp:
                    divide_by = 1000
                    unit = "C"
                elif self._type == self.Type.Voltage:
                    divide_by = 1000
                    unit = "V"
                elif self._type == self.Type.Fan:
                    divide_by = 1
                    unit = "RPM"
                elif self._type == self.Type.Current:
                    divide_by = 1000
                    unit = "A"
                elif self._type == self.Type.Power:
                    divide_by = 1000000
                    unit = "W"
                else:
                    divide_by = 1
                    unit = ""

                return f"{value / divide_by} {unit}"

            def update_value(self):
                with open(self._value_path) as f:
                    self._value = f.readline().strip()
                    if self._value.isdecimal():
                        self._value = int(self._value)
                        self._min_value = min(self._value, self._min_value)
                        self._max_value = max(self._value, self._max_value)
                    else:
                        self._min_value = "N/A"
                        self._max_value = "N/A"

                self._tree_item.setData(
                    1,
                    QtCore.Qt.ItemDataRole.DisplayRole,
                    self.value_to_string(self._value),
                )
                self._tree_item.setData(
                    2,
                    QtCore.Qt.ItemDataRole.DisplayRole,
                    self.value_to_string(self._min_value),
                )
                self._tree_item.setData(
                    3,
                    QtCore.Qt.ItemDataRole.DisplayRole,
                    self.value_to_string(self._max_value),
                )

            def get_tree_widget_item(self):
                if self._value == 0:
                    return None
                return self._tree_item

        def __init__(self, name):
            self.name = name
            self.sensors = list()

    def __init__(self):
        self.devices = list()

    def update_sensors(self):
        for device in self.devices:
            for sensor in device.sensors:
                sensor.update_value()

    def get_tree_widget(self):
        tree_widget = QTreeWidget()
        tree_widget.setColumnCount(4)
        tree_widget.setHeaderLabels(["Name", "Value", "Min", "Max"])
        for device in self.devices:
            device_item = QTreeWidgetItem([device.name])
            for sensor in device.sensors:
                device_item.addChild(sensor.get_tree_widget_item())
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

            # TODO: Icons
            for sensor in os.listdir(subdir_path):
                sensor_parts = sensor.split("_")
                sensor_label_path = os.path.join(subdir_path, sensor_parts[0], "_label")
                sensor_label = sensor_parts[0]
                if os.path.exists(sensor_label_path):
                    with open(sensor_label_path) as f:
                        sensor_label = f.readline().strip()

                sensor_path = os.path.join(subdir_path, sensor)
                if os.path.isfile(sensor_path):
                    if "_input" in sensor:
                        with open(sensor_path) as f:
                            try:
                                h_sensor = HwmonSensors.HwmonDevice.HwmonSensor(
                                    sensor_label, sensor_parts[0], sensor_path
                                )
                                h_sensor.update_value()
                                h_device.sensors.append(h_sensor)
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
        self.hwmon = None

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

        self.sensors_tree = self.hwmon.get_tree_widget()
        self.sensors_tree.setSortingEnabled(True)
        self.sensors_tree.expandAll()
        self.sensors_tree.header().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.sensors_tree.header().setStretchLastSection(False)

        sensors_layout = QVBoxLayout()
        sensors_layout.addWidget(self.sensors_tree)
        self.sensors_widget = QWidget()
        self.sensors_widget.setLayout(sensors_layout)
        self.tab_widget.addTab(self.sensors_widget, "Sensors")

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

    def on_refresh_button_click(self):
        self.hwmon.update_sensors()

    def on_help_button_click(self):
        pass


app = QApplication(sys.argv)
ex = App()
sys.exit(app.exec())
