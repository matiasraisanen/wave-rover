from rover import Rover
from logger import Logger
import logging
from inputDeviceReader import InputDeviceReader
import threading


class Main:
    def __init__(self):
        self.logger = Logger(
            module_name=__name__,
            log_level=logging.DEBUG,
            streamhandler=True,
            filehandler=True,
            log_file="rover.log",
            delete_old_logfile=True,
        )

        self.rover = Rover()
        self.reader = InputDeviceReader()

    def start(self):
        # thread = threading.Thread(
        #     target=self.reader.read_events, args=(self.rover.process_input_data,)
        # )
        # thread.start()

        self.reader.read_events(self.rover.process_input_state)


if __name__ == "__main__":
    robot = Main()
    # robot.rover.device_info()
    # robot.rover.imu_info()
    robot.start()
