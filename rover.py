import time
import serial
import json
from logger import Logger
import logging

# Class for controlling the Wave Rover by sending JSON commands over serial.
# Wave Rover wiki: https://www.waveshare.com/wiki/WAVE_ROVER


class Rover:
    def __init__(self, port="/dev/ttyUSB0", baudrate=1000000):
        self.logger = Logger(
            module_name=__name__,
            log_file="rover.log",
            log_level=logging.DEBUG,
            delete_old_logfile=True,
        )
        self.ser = serial.Serial(port, baudrate)

    def read_data(self):
        if self.ser.isOpen():
            return self.ser.read_all().decode().strip()
            # return self.ser.readline().decode().strip()

    def close_connection(self):
        if self.ser.isOpen():
            self.ser.close()

    def send_json(self, data):
        if self.ser.isOpen():
            json_data = json.dumps(data)
            self.logger.log.debug(f"Sending JSON command: {json_data}")
            self.ser.write(json_data.encode())
            time.sleep(0.05)  # give the device time to respond
            response = json.loads(self.ser.read_all().decode().strip())
            self.logger.log.debug(f"Command response: {response}")
            return response

    def oled_set(self, line, text):
        if len(text) > 22:
            text = text[:22]
        command = {"T": 3, "lineNum": line, "Text": text}
        self.send_json(command)

    def oled_clear(self):
        for line in range(4):
            command = {"T": 3, "lineNum": line, "Text": ""}
            self.send_json(command)

    def oled_default(self):
        OLED_DEFAULT = {"T": -3}
        self.send_json(OLED_DEFAULT)

    def rover_exit(self):
        if self.ser.isOpen():
            self.close_connection()
            exit(0)

    def pid_set(self, P=170, I=90):
        """
        PID control for closed-loop motor control.
        Note: This function is not available for chassis without speed feedback like WAVE ROVER.
        P: Proportional gain
        I: Integral gain
        """
        PID_SET = {"T": 2, "P": P, "I": I}
        self.send_json(PID_SET)

    def speed_input(self, speed_left, speed_right):
        """
        Set the speed of the left and right wheels
        speed_left: -255 ... 255
        speed_right: -255 ... 255
        """
        SPEED_INPUT = {"T": 1, "L": speed_left, "R": speed_right}
        self.send_json(SPEED_INPUT)

    def emergency_stop(self):
        EMERGENCY_STOP = {"T": 0}
        self.send_json(EMERGENCY_STOP)

    def pwm_servo_control(self, position, speed):
        PWM_SERVO_CTRL = {"T": 40, "pos": position, "spd": speed}
        self.send_json(PWM_SERVO_CTRL)

    def pwm_servo_mid(self):
        """
        The PWM servo is turned to the center position, which is the 90° position.
        """
        PWM_SERVO_MID = {"T": -4}
        self.send_json(PWM_SERVO_MID)

    def bus_servo_ctrl(self, servo_id, position, speed, acceleration):
        """
        Regarding the serial bus servo control commands, here you should note that the connected serial bus servo operating voltage and the driver board power supply voltage are consistent, you can directly use our ST3215 serial bus servo.

        servo_id: ID of the bus servo, the ID of the serial bus servo connected to the driver board should not be duplicated.

        position: The target position to be rotated to by the servo, for ST3215 servo, in angle control mode, this value can be 0-4095, which corresponds to the clockwise rotation range of 0-360°; in continuous rotation mode, the value can be ±32766.

        speed: rotation speed of the bus servo, the number of steps per unit of time (per second), 50 steps/second = 0.732 RPM (revolutions per minute), the larger the value, the faster the speed (but the speed of the servo has a limit), when the parameter is 0, it will run at the maximum speed.

        acceleration: acceleration of bus servo rotation, the smaller the value, the smoother the start-stop, the value can be 0-254, such as set to 10, then according to the 1000 steps per second square acceleration speed, when the parameter is 0, then according to the maximum acceleration operation.
        """
        BUS_SERVO_CTRL: {
            "T": 50,
            "id": servo_id,
            "pos": position,
            "spd": speed,
            "acc": acceleration,
        }
        self.send_json(BUS_SERVO_CTRL)

    def bus_servo_mid(self, servo_id):
        """
        The bus servo is turned to the center position, which is the 90° position.
        """
        BUS_SERVO_MID = {"T": -5, "id": servo_id}
        self.send_json(BUS_SERVO_MID)

    def bus_servo_scan(self, number):
        """
        Used to scan which servos are connected to the bus, no duplicate IDs are allowed, and the result will be returned and displayed at the top of the input field.

        number: Maximum ID of the servo. The larger the value, the longer the scanning time.
        """
        BUS_SERVO_SCAN: {"T": 52, "num": number}
        self.send_json(BUS_SERVO_SCAN)
        # data = self.read_data()
        # print(f"Bus servo: {data}")

    def bus_servo_info(self, servo_id):
        """
        It is used to get the information feedback of a particular servo, which contains the position, speed, voltage, torque, and other information of the servo.
        """
        BUS_SERVO_INFO: {"T": 53, "id": servo_id}
        self.send_json(BUS_SERVO_INFO)
        # data = self.read_data()
        # print(f"Bus servo: {data}")

    def bus_servo_id_set(self, old_id, new_id):
        """
        Used to change the ID of a servo, the ID of each new servo is 1 by default, if you don't know the ID of the servo at hand, you can use the above BUS_SERVO_SCAN command to get it, but the premise is that when checking the ID of this servo, the driver board is connected to only this one servo, otherwise you don't know which ID corresponds to which servo.

        old: ID of the servo whose ID is to be changed.

        new: New ID to be set
        """
        BUS_SERVO_ID_SET: {"T": 54, "old": old_id, "new": new_id}
        self.send_json(BUS_SERVO_ID_SET)

    def bus_servo_torque_lock(self, servo_id, status):
        """
        Servo torque lock switch.

        id: ID of the servo to control the torque lock.

        status: parameter of torque lock switch, 1 is to enable torque lock, the servo will keep its position; 0 is to disable torque lock, the servo will rotate under external force.
        """
        BUS_SERVO_TORQUE_LOCK: {"T": 55, "id": servo_id, "status": status}
        self.send_json(BUS_SERVO_TORQUE_LOCK)

    def bus_servo_torque_limit(self, servo_id, limit):
        """
        Servo torque limit command.

        id: ID of the target servo.

        limit: Torque limiting ratio, 500 is 50%* locked rotor torque, 1000 is 100%* locked rotor torque, after limiting the torque, when the servo is subjected to external force when the torque of the external force is greater than the limiting torque, the servo will rotate with the external force, but it will still provide this torque, this function can be used to design the clamp of the robotic arm.
        """
        BUS_SERVO_TORQUE_LIMIT: {"T": 56, "servo_id": 1, "limit": limit}
        self.send_json(BUS_SERVO_TORQUE_LIMIT)

    def bus_servo_mode(self, servo_id, mode):
        """
        Servo operation mode.
        id: ID of target servo.
        mode: operation mode value, 0: position servo mode, used to control the absolute angle of the servo; 3: stepper servo mode, also use the BUS_SERVO_CTRL command to control the servo.
        """
        BUS_SERVO_MODE = {"T": 57, "id": servo_id, "mode": mode}
        self.send_json(BUS_SERVO_MODE)

    def wifi_scan(self):
        """
        WIFI scanning command, which disconnects the existing WIFI connection to scan for surrounding WIFI hotspots.
        """
        WIFI_SCAN = {"T": 60}
        self.send_json(WIFI_SCAN)

    def wifi_try_sta(self):
        """
        WIFI connection command, STA mode, for connecting to a known WIFI.
        """
        WIFI_TRY_STA = {"T": 61}
        self.send_json(WIFI_TRY_STA)

    def wifi_ap_default(self):
        """
        Enabling the WIFI hotspot command, AP mode, the robot will automatically create a WIFI hotspot.
        Hotspot name: WAVE_ROVER
        Hotspot Password: 12345678
        """
        WIFI_AP_DEFAULT = {"T": 62}
        self.send_json(WIFI_AP_DEFAULT)

    def wifi_info(self):
        """
        For obtaining WIFI information.
        """
        WIFI_INFO = {"T": 65}
        self.send_json(WIFI_INFO)

    def wifi_off(self):
        """
        Disable the WiFi function.
        """
        WIFI_OFF = {"T": 66}
        self.send_json(WIFI_OFF)

    def ina219_info(self):
        """
        Get information about the INA219, including the voltage and current power of the power supply.
        """
        INA219_INFO = {"T": 70}
        info = self.send_json(INA219_INFO)

        # make sure no property is None
        for key in info:
            if info[key] is None:
                info[key] = 0

        shunt_voltage = info["shunt_mV"]
        load_voltage = info["load_V"]
        bus_voltage = info["bus_V"]
        current = info["current_mA"]
        power = info["power_mW"]

        self.get_rover_power_state(info)

        battery_percentage = (bus_voltage - 9) / 3.6 * 100
        if battery_percentage > 100:
            battery_percentage = 100
        if battery_percentage < 0:
            battery_percentage = 0

        # print("PSU Voltage:   {:6.3f} V".format(bus_voltage + shunt_voltage))
        # print("Shunt Voltage: {:9.6f} V".format(shunt_voltage))
        # print("Load Voltage:  {:6.3f} V".format(bus_voltage))
        # print("Current:       {:9.6f} A".format(current))
        # print("Power:         {:6.3f} W".format(power))
        self.logger.log.debug("Battery:        {:3.1f}%".format(battery_percentage))
        self.logger.log.debug("Shunt Voltage: {:9.6f} V".format(shunt_voltage))
        self.logger.log.debug("Bus Voltage:    {:6.3f} V".format(bus_voltage))
        self.logger.log.debug("Load Voltage:   {:6.3f} V".format(load_voltage))
        self.logger.log.debug("Current:        {:9.6f} A".format(current))
        self.logger.log.debug("Power:          {:6.3f} W".format(power))
        # print("")

    def imu_info(self):
        """
        Used to obtain IMU information, including heading angle, geomagnetic field, acceleration, attitude, temperature, etc.
        """
        IMU_INFO = {"T": 71}
        self.send_json(IMU_INFO)

    def encoder_info(self):
        """
        Used to get motor encoder information. (Not applicable to WAVE ROVER as there are no encoders).
        """
        ENCODER_INFO = {"T": 73}
        self.send_json(ENCODER_INFO)

    def device_info(self):
        """
        Used to get the device information, the device information is required to be customized by the user, used to introduce the use of this device or other information.
        """
        DEVICE_INFO = {"T": 74}
        self.send_json(DEVICE_INFO)

    def io_ir_cut(self, status):
        """
        It is used to control the high and low levels of the IO5 pin on top of the driver board, which can be used to control the night vision function switch of the infrared camera or to control the relay.
        """
        IO_IR_CUT = {"T": 80, "status": status}
        self.send_json(IO_IR_CUT)

    def set_spd_rate(self, L, R):
        """
        Used to adjust the power of each side motor. When giving the robot the same power for the left and right motors, if the robot's movement is not straight, you can use this command to fine-tune the power of the motors on both sides, and the value will be used as a coefficient multiplied by the motor's output power to change the motor's power.
        L: Power coefficient of left side motor.
        R: The power coefficient of the right side motor.
        """
        SET_SPD_RATE = {"T": 901, "L": L, "R": R}
        self.send_json(SET_SPD_RATE)

    def get_spd_rate(self):
        """
        Get the power coefficients of the left and right side motors.
        """
        GET_SPD_RATE = {"T": 902}
        self.send_json(GET_SPD_RATE)

    def spd_rate_save(self):
        """
        Saving the power coefficient of the motor will be saved in the nvs area of the ESP32 and will not be lost after power down, and this speed coefficient will be read and loaded by the nvs area after power up.
        """
        SPD_RATE_SAVE = {"T": 903}
        self.send_json(SPD_RATE_SAVE)

    def get_nvs_space(self):
        """
        Get the remaining space in the nvs area of ESP32.
        """
        GET_NVS_SPACE = {"T": 904}
        self.send_json(GET_NVS_SPACE)

    def nvs_clear(self):
        """
        Clear nvs zone, this command deletes the entire contents of the nvs zone, and the speed coefficient changes back to the default value of 1.0.
        """
        NVS_CLEAR = {"T": 905}
        self.send_json(NVS_CLEAR)

    def get_rover_power_state(self, data):
        if data["shunt_mV"] < 0 and data["load_V"] < 1:
            state = "Charger: OFF, PowerSwitch: OFF"
        elif data["shunt_mV"] < 0 and data["load_V"] > 1:
            state = "Charger: ON, PowerSwitch: OFF"
        elif data["shunt_mV"] > 0 and data["load_V"] > 11.7:
            state = "Charger: ON, PowerSwitch: ON"
        elif data["shunt_mV"] > 0 and data["load_V"] < 11.7:
            state = "Charger: OFF, PowerSwitch: ON"
        else:
            state = "Unknown state"

        self.logger.log.debug(f"Rover power state: {state}")
        return state


if __name__ == "__main__":
    # Example usage. Note: The port may be different on your system.
    port = "/dev/ttyUSB0"
    rover = Rover(port)

    # rover.oled_set(0, "Hello")
    # rover.oled_set(1, "World")
    # rover.oled_set(2, "Hello")
    # rover.oled_set(3, "World")
    rover.ina219_info()
    # time.sleep(2)
    # rover.oled_default()
    rover.close_connection()
