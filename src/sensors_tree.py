import sys
from abc import abstractmethod, ABC
from enum import Enum
from functools import cached_property

from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidget


class SensorsTree(ABC):
    def __init__(self):
        self.devices = list()
        self.tree_widget = QTreeWidget()

    def update_sensors(self):
        for device in self.devices:
            if not device.faulty:
                device.update_sensors()
            else:
                # Remove the faulty one
                self.tree_widget.takeTopLevelItem(
                    self.tree_widget.indexOfTopLevelItem(device.tree_item)
                )
                self.devices.remove(device)
                print(f"removed the faulty device: {device.name}")

    def get_tree_widget(self):
        self.tree_widget.setColumnCount(5)
        self.tree_widget.setHeaderLabels(["Name", "Value", "Min", "Max", "Graph?"])
        for device in self.devices:
            if device.faulty:
                continue
            device_item = DeviceTreeItem(device, [device.name])
            for sensor in device.sensors:
                device_item.addChild(sensor.get_tree_widget_item())
            # Don't show empty devices
            if device_item.childCount() != 0:
                self.tree_widget.addTopLevelItem(device_item)

        return self.tree_widget

    @abstractmethod
    def read(self):
        raise NotImplementedError()


class Device(ABC):
    def __init__(self, name):
        self.name = name
        self.sensors = list()
        self.faulty = False

        self.tree_item = None

    @abstractmethod
    def update_sensors(self):
        raise NotImplementedError()


class DeviceTreeItem(QTreeWidgetItem):
    def __init__(self, device, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device
        self.device.tree_item = self


class SensorTreeItem(QTreeWidgetItem):
    def __init__(self, sensor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensor = sensor
        self.setCheckState(4, Qt.CheckState.Unchecked)


class Sensor(ABC):
    class Type(Enum):
        Temp = 1
        Voltage = 2
        Fan = 3
        Current = 4
        Power = 5
        Intrusion = 6
        Flow = 7

    def __init__(self, label, internal_data, device):
        self.label = label.strip()
        self._internal_data = internal_data
        self._device = device

        # Plotting
        self._plot_line = None
        self._values_over_time = dict()

        self._value = 0
        self._min_value = sys.maxsize
        self._max_value = -sys.maxsize - 1

        self._tree_item = SensorTreeItem(
            self,
            [
                self.label,
                str(self._value),
                str(self._min_value),
                str(self._max_value),
                str(),
            ],
        )

        self._tree_item.setIcon(0, QtGui.QIcon(f"icons:{self.icon}"))

    @abstractmethod
    def type(self):
        raise NotImplementedError

    @cached_property
    def icon(self):
        feat_icon = None
        if self.type == self.Type.Temp:
            feat_icon = "icons8-thermometer-96.png"
        elif self.type == self.Type.Current:
            feat_icon = "icons8-high-voltage-96.png"
        elif self.type == self.Type.Voltage:
            feat_icon = "icons8-voltmeter-100.png"
        elif self.type == self.Type.Power:
            feat_icon = "icons8-shutdown-90.png"
        elif self.type == self.Type.Fan:
            feat_icon = "icons8-fan-head-64.png"
        elif self.type == self.Type.Intrusion:
            feat_icon = "icons8-hips-100.png"
        elif self.type == self.Type.Flow:
            feat_icon = "icons8-process-90.png"

        return feat_icon

    @abstractmethod
    def get_tree_widget_item(self):
        return self._tree_item
