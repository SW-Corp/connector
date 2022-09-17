import glob
import logging as logger
import sys
import time
from queue import Queue
from threading import Lock, Thread

import serial
from serial.tools import list_ports

from connector.status_handler import Status, StatusHandler

from .backend_connector import BackendConnector, MetricsData

STATE_UP = 0

vidpid_pairs = set(
    [
        (0x2341, 0x43),  # Arduino Uno R3
        (0x1A86, 0x7523),  # CH340
        (0x1A86, 0x7522),  # CH340
        (0x1A86, 0x5523),  # CH341 in serial mode
        (0x1A86, 0x7584),  # CH340S
    ]
)


class WriterThread(Thread):
    statusHandler: StatusHandler
    message_queue: Queue
    port: serial.Serial = None
    is_running: bool = True
    last_ask_timestamp: int = 0
    ask_period: int = 5  # every n seconds send '?' char to request current status. Do it in pseudo-async way

    def __init__(self, statusHandler: StatusHandler, askperiod: int = 5):
        super(WriterThread, self).__init__()
        self.statusHandler = statusHandler
        self.message_queue = Queue()
        self.ask_period = askperiod

    def set_serial_port(self, serialport: serial.Serial):
        self.port = serialport

    def stop(self):
        self.is_running = False

    def send(self, message: str):
        msg = message.encode("ascii")
        if message[-2:] != "\r\n":
            msg += "\r\n".encode("ascii")
        self.message_queue.put(msg)

    def run(self):

        while self.is_running:

            try:
                msg = self.message_queue.get(block=True, timeout=5)
                self.port.write(msg)
            except Exception as e:
                # here we should suppress Empty exception and handle all the others
                # logger.debug(f"There was some error while sending a message: {e}")
                pass

            if int(time.time()) - self.last_ask_timestamp >= self.ask_period:
                self.send(
                    "?\r\n"
                )  # According to the protocol, question mark is requesting a report of the current status of every component
                self.last_ask_timestamp = int(time.time())


class HardwareCommunicator(Thread):
    statusHandler: StatusHandler
    writerThread: WriterThread
    port: serial.Serial = None
    baudrate: int = 115200  # fallback to default value
    is_running: bool = True
    status_report_lock: Lock = Lock()

    def __init__(self, statusHandler, arguments, *args):
        super(HardwareCommunicator, self).__init__()
        self.statusHandler = statusHandler
        self.baudrate = arguments.baudrate

        self.writerThread = WriterThread(statusHandler, arguments.interval)

        self.status_report = {
            "containers": {
                "C1": (False, 0.0),  # (float_switch_up [0 or 1], pressure [hPa])
                "C2": (False, 0.0),
                "C3": (False, 0.0),
                "C4": (False, 0.0),
                "C5": (False, 0.0),
            },
            "ref_pressure": 0.0,  # only pressure
            "pumps": {
                "P1": (0.0, 0.0),  # (current [A], voltage [V])
                "P2": (0.0, 0.0),
                "P3": (0.0, 0.0),
                "P4": (0.0, 0.0),
            },
            "valves": {
                "V1": (0.0, 0.0),
                "V2": (0.0, 0.0),
                "V3": (0.0, 0.0),
            },
        }

    def open_serial_port(self):
        sport = None

        for port in list(list_ports.comports()):
            if port.vid and port.pid:
                if (port.vid, port.pid) in vidpid_pairs:
                    print(f"Found a serial port. Location: {port.device}")
                    sport = port.device
                    break

        if not sport:
            logger.error("No valid COM port was found. Check your USB device.")
            self.statusHandler.setStatus(Status(500, "No valid COM port was found."))

        try:
            self.port = serial.Serial(sport, self.baudrate, timeout=2)
            self.writerThread.set_serial_port(self.port)
            self.writerThread.start()  # start writer thread
            self.statusHandler.setStatus(
                Status(200, "Serial port opened successfully.")
            )
        except:
            logger.error(f"Can't open serial port {sport}")
            self.statusHandler.setStatus(Status(500, f"Can't open serial port {sport}"))

    def send(self, message: str):
        self.writerThread.send(message)

    def stop(self):
        logger.debug("Shutting down hardware communication thread...")
        self.writerThread.stop()
        self.writerThread.join()
        self.is_running = False

    def parse_debug_message(self, line: str):
        if "FAIL" in line:
            self.statusHandler.setStatus(Status(503, line))
            return

        if "REPORT" in line and "FINISHED" in line:
            # read and push metrics here
            pass

    def set_pump_details(self, id: str, first_value: str, second_value: str):
        logger.debug(f"Got pump setting: {id} {first_value} {second_value}")
        self.status_report["pumps"][id] = (float(first_value), float(second_value))
        pass

    def set_valve_details(self, id: str, first_value: str, second_value: str):
        logger.debug(f"Got valve setting: {id} {first_value} {second_value}")
        self.status_report["valves"][id] = (float(first_value), float(second_value))
        pass

    def set_container_details(self, id: str, first_value: str, second_value: str):
        logger.debug(f"Got container setting: {id} {first_value} {second_value}")
        if id == "RF":
            self.status_report["ref_pressure"] = float(second_value)
            return

        self.status_report["containers"][id] = (
            False if int(first_value) == 1 else True,
            float(second_value),
        )

    def parse_value_message(self, line: str):
        """
        format of the message:    $Cx 0 1023.28   - report of a container status, first number tells whether float switch is up or down (by default, 1-down, 0-up), second: pressure in a container
                                  $Px 0.00 0.00   - report of a pump status, first number: current flowing through the component, second: voltage
                                  $Vx 0.00 0.00   - report of a valve status, first number: current flowing through the component, second: voltage
        """

        self.status_report_lock.acquire()

        {
            "C": self.set_container_details,
            "R": self.set_container_details,
            "P": self.set_pump_details,
            "V": self.set_valve_details,
        }[line[1]](*(line.split(" ")))

        self.status_report_lock.release()

    def parse_line(self, line: bytes):
        """
        Parse pure message straight from the serial port. It should be an ascii-encoded bytes object.
        """
        if len(line) < 1:
            return
        decoded = line.decode("ascii").replace("\r", "").replace("\n", "")
        if "Water" in decoded:
            logger.debug(
                f"Got the hello message. We are good to go. Protocol version: {decoded.split(' ')[-1]}"
            )
            return
        # logger.debug(f"Get line: {decoded}")
        try:
            {">": self.parse_debug_message, "$": self.parse_value_message}[decoded[0]](
                decoded
            )
        except Exception:
            logger.debug(f"Unrecognized command: {decoded}")

    def run(self):

        self.open_serial_port()

        line = b""

        while self.is_running:

            if self.port.is_open:
                c = self.port.read(1)
                line += c
                if len(line) > 1 and (
                    line[-2:].decode("ascii") == "\r\n" or line[-1] == b"\n"
                ):
                    self.parse_line(line)
                    line = b""
            else:
                time.sleep(3)  # avoid spinning the loop constantly

        # metric = MetricsData(measurement="waterlevel", field="tank1", value=level)
        # try:
        # backend_connector.push_metrics([metric])
        # except Exception:
        # pass
