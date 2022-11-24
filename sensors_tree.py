import sys
from abc import abstractmethod, ABC
from enum import Enum

from PyQt6 import QtGui
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QTreeWidgetItem, QTreeWidget


class SensorsTree(ABC):
    def __init__(self):
        self.devices = list()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sensors)
        self.timer.start(1000)  # TODO: Make optional and configurable

    def update_sensors(self):
        for device in self.devices:
            device.update_sensors()

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

    @abstractmethod
    def read(self):
        raise NotImplementedError()


class Device(ABC):
    def __init__(self, name):
        self.name = name
        self.sensors = list()

    @abstractmethod
    def update_sensors(self):
        raise NotImplementedError()


class Sensor(ABC):
    class Type(Enum):
        Temp = 1
        Voltage = 2
        Fan = 3
        Current = 4
        Power = 5
        Intrusion = 6

    def __init__(self, label, internal_data):
        self.label = label
        self._internal_data = internal_data

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

        self._tree_item.setIcon(0, QtGui.QIcon(f"icons:{self.get_icon()}"))

    @property
    @abstractmethod
    def get_type(self):
        raise NotImplementedError

    @abstractmethod
    def get_icon(self):
        feat_icon = None
        if self.get_type() == self.Type.Temp:
            feat_icon = "icons8-thermometer-96.png"
        elif self.get_type() == self.Type.Current:
            feat_icon = "icons8-high-voltage-96.png"
        elif self.get_type() == self.Type.Voltage:
            feat_icon = "icons8-voltmeter-100.png"
        elif self.get_type() == self.Type.Power:
            feat_icon = "icons8-shutdown-90.png"
        elif self.get_type() == self.Type.Fan:
            feat_icon = "icons8-fan-head-64.png"
        elif self.get_type() == self.Type.Intrusion:
            feat_icon = "icons8-hips-100.png"

        return feat_icon

    @abstractmethod
    def get_tree_widget_item(self):
        return self._tree_item
