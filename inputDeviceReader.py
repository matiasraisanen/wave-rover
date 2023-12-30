import evdev
from logger import Logger
import logging


class InputDeviceReader:
    def __init__(self, device_path=None):
        self.logger = Logger(
            module_name=__name__,
            log_file="rover.log",
            log_level=logging.DEBUG,
            delete_old_logfile=True,
            streamhandler=True,
            filehandler=True,
        )
        # If no device path is specified, use the first device in the list
        try:
            if device_path is None:
                devices = self.list_devices()
                device_path = evdev.InputDevice(devices[0].path)
        except IndexError:
            raise Exception("No input devices found")
        self.device = evdev.InputDevice(device_path)

        # Initialize key states
        self.key_states = {2: 0, 5: 0, 0: 0}

    def read_events(self, callback):
        for event in self.device.read_loop():
            # EV_KEY is for buttons
            if event.type == evdev.ecodes.EV_KEY:
                key_event = evdev.categorize(event)
                key_number = key_event.scancode
                key_name = key_event.keycode
                key_value = key_event.keystate
                percentage = None
                # key_press = callback("key", key_number, key_value)
            # EV_ABS is for analog inputs
            if event.type == evdev.ecodes.EV_ABS:
                abs_event = evdev.categorize(event)
                key_number = abs_event.event.code
                key_value = abs_event.event.value
                percentage = self.value_to_percentage(key_number, key_value)
                # key_press = callback("abs", key_number, key_value, percentage)

            # use key percentage if it is not None, otherwise use key value
            self.logger.log.debug(
                f"KeyNumber: {key_number} Value: {key_value} Percentage: {percentage}%"
            )
            self.key_states[key_number] = percentage or key_value
            # self.key_states[key_number] = key_value
            # callback("abs", key_number, key_value, percentage)
            callback(self.key_states)

    # Returns analog values as percentages
    def value_to_percentage(self, key_number, key_value):
        joysticks = [0, 1, 3, 4]  # Left X, Left Y, Right X, Right Y
        triggers = [2, 5]  # Left Trigger, Right Trigger

        # These are the max values for analog inputs on the XBOX One controller (M1142084-007).
        joystick_max = 32767
        trigger_max = 1023

        if key_number in joysticks:
            percentage = int((key_value / joystick_max) * 100) * -1
        elif key_number in triggers:
            percentage = int((key_value / trigger_max) * 100)
        return percentage

    def list_devices(self):
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        # for device in devices:
        #     print(device.path, device.name, device.phys)
        return devices

    def print_event(self, event_type, key_number, key_value, key_name=None):
        if event_type == "key":
            key_press = (key_number, key_value)
            print(f"Key: {key_name} KeyNumber: {key_number} Value: {key_value}")
        elif event_type == "abs":
            key_press = (key_number, key_value)
            percentage = self.value_to_percentage(key_number, key_value)
            print(
                f"KeyNumber: {key_number} Value: {key_value} Percentage: {percentage}%"
            )
        return key_press


if __name__ == "__main__":
    reader = InputDeviceReader()
    reader.read_events(reader.print_event)
