import os
from functools import cached_property

from PyQt6 import QtCore

from sensors_tree import SensorsTree, Device, Sensor


class HwmonSensors(SensorsTree):
    HWMON_PATH = "/sys/class/hwmon"

    def __init__(self):
        super().__init__()

    class HwmonDevice(Device):
        def __init__(self, name):
            super().__init__(name)

        def update_sensors(self):
            try:
                for sensor in self.sensors:
                    sensor.update_value()
            except:
                print(
                    f"couldn't read {self.name}/{sensor.label}, marking device as faulty"
                )
                self.faulty = True

        class HwmonSensor(Sensor):
            def __init__(self, label, internal_data):
                super().__init__(label, internal_data)

            def update_value(self):
                with open(self._internal_data["path"]) as f:
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
                    self.value_to_str(self._value),
                )
                self._tree_item.setData(
                    2,
                    QtCore.Qt.ItemDataRole.DisplayRole,
                    self.value_to_str(self._min_value),
                )
                self._tree_item.setData(
                    3,
                    QtCore.Qt.ItemDataRole.DisplayRole,
                    self.value_to_str(self._max_value),
                )

            @cached_property
            def type(self):
                internal_name = self._internal_data["fs_name"].split("_input")[0]

                if "temp" in internal_name:
                    return self.Type.Temp
                elif "in" in internal_name:
                    return self.Type.Voltage
                elif "fan" in internal_name:
                    if "flow" in self._internal_data["label"].lower():
                        return self.Type.Flow
                    return self.Type.Fan
                elif "curr" in internal_name:
                    return self.Type.Current
                elif "power" in internal_name:
                    return self.Type.Power
                elif "intrusion" in internal_name:
                    return self.Type.Intrusion

            def get_tree_widget_item(self):
                if self._value == 0:
                    return None
                return super().get_tree_widget_item()

            def value_to_str(self, value):
                if not type(value) == int:
                    return "N/A"

                if self.type == self.Type.Temp:
                    divide_by = 1000
                    unit = "C"
                elif self.type == self.Type.Voltage:
                    divide_by = 1000
                    unit = "V"
                elif self.type == self.Type.Fan:
                    divide_by = 1
                    unit = "RPM"
                elif self.type == self.Type.Current:
                    divide_by = 1000
                    unit = "A"
                elif self.type == self.Type.Power:
                    divide_by = 1000000
                    unit = "W"
                else:
                    divide_by = 1
                    unit = ""

                return f"{value / divide_by} {unit}"

    def read(self):
        hwmon_dirs = os.listdir(self.HWMON_PATH)
        for subdir in hwmon_dirs:
            subdir_path = os.path.join(self.HWMON_PATH, subdir)

            with open(os.path.join(subdir_path, "name")) as f:
                device_name = f.readline().strip()

            h_device = self.HwmonDevice(device_name)
            self.devices.append(h_device)

            for sensor in os.listdir(subdir_path):
                sensor_parts = sensor.split("_")
                sensor_label_path = os.path.join(
                    subdir_path, sensor_parts[0] + "_label"
                )
                sensor_label = sensor_parts[0]
                if os.path.exists(sensor_label_path):
                    with open(sensor_label_path) as f:
                        sensor_label = f.readline().strip()

                sensor_path = os.path.join(subdir_path, sensor)
                if os.path.isfile(sensor_path):
                    if "_input" in sensor:
                        with open(sensor_path) as f:
                            try:
                                internal_data = {
                                    "fs_name": sensor,
                                    "label": sensor_label,
                                    "path": sensor_path,
                                }

                                h_sensor = self.HwmonDevice.HwmonSensor(
                                    sensor_label, internal_data
                                )
                                h_sensor.update_value()
                                h_device.sensors.append(h_sensor)
                            except OSError:
                                pass  # TODO: Show error
