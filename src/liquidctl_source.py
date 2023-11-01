import time
from functools import cached_property

from liquidctl import find_liquidctl_devices

from PyQt5 import QtCore

from sensors_tree import SensorsTree, Device, Sensor


class LiquidctlSensors(SensorsTree):
    def __init__(self):
        super().__init__()

    class LiquidctlDevice(Device):
        def __init__(self, name, liquidctl_device):
            super().__init__(name)
            self._device = liquidctl_device
            self._sensor_map = {}

        def __del__(self):
            self._device.disconnect()

        def update_sensors(self):
            try:
                for key, value, unit in self._device.get_status():
                    if key not in self._sensor_map:
                        new_sensor = self.LiquidctlSensor(
                            key, {"unit": unit}, self._device
                        )
                        new_sensor.update_value(value)
                        self._sensor_map[key] = new_sensor
                        self.sensors.append(new_sensor)
                    else:
                        self._sensor_map[key].update_value(value)
            except:
                print(f"couldn't read {self.name} from liquidctl, marking as faulty")
                self.faulty = True

        class LiquidctlSensor(Sensor):
            def __init__(self, label, internal_data, liquidctl_device):
                super().__init__(label, internal_data, liquidctl_device)

            def update_value(self, new_value):
                if type(new_value) is int or type(new_value) is float:
                    self._value = round(new_value, 2)
                    self._min_value = min(self._value, self._min_value)
                    self._max_value = max(self._value, self._max_value)

                    self._values_over_time[time.time()] = self._value
                else:
                    self._min_value = "N/A"
                    self._max_value = "N/A"

                    self._values_over_time[time.time()] = 0

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
                internal_name = self.label.lower()

                if "temp" in internal_name:
                    return self.Type.Temp
                elif "voltage" in internal_name:
                    return self.Type.Voltage
                elif "speed" in internal_name or "duty" in internal_name:
                    return self.Type.Fan
                elif "current" in internal_name:
                    return self.Type.Current
                elif "power" in internal_name:
                    return self.Type.Power
                elif "flow" in internal_name:
                    return self.Type.Flow

            def get_tree_widget_item(self):
                return super().get_tree_widget_item()

            def value_to_str(self, value):
                return f"{value} {self._internal_data['unit']}"

    def read(self):
        devices = find_liquidctl_devices()

        for dev in devices:
            dev.connect()
            init_status = dev.initialize()
            if init_status:
                new_device = self.LiquidctlDevice(dev.description, dev)
                new_device.update_sensors()
                self.devices.append(new_device)
            # TODO: else log
