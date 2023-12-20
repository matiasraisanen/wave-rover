from rover import Rover
from logger import Logger
import logging
from inputDeviceReader import InputDeviceReader
import threading


class Main:
    def __init__(self):
        self.rover = Rover()
        self.logger = Logger(
            module_name=__name__,
            log_file="rover.log",
            log_level=logging.DEBUG,
            delete_old_logfile=True,
        )
        self.reader = InputDeviceReader()

    def start(self):
        thread = threading.Thread(
            target=self.reader.read_events, args=(self.rover.process_input_data,)
        )
        thread.start()


# Usage
robot = Main()
robot.start()
