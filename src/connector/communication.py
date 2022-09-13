import glob
import logging as logger
import sys
import time
from queue import Queue
from threading import Thread

import serial
from serial.tools import list_ports

from connector.status_handler import Status, StatusHandler

from .backend_connector import BackendConnector, MetricsData

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

    def __init__(self, statusHandler: StatusHandler):
        super(WriterThread, self).__init__()
        self.statusHandler = statusHandler
        self.message_queue = Queue()

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
                self.port.write(self.message_queue.get(block=True))
            except Exception as e:
                logger.debug(f"There was some error while sending a message: {e}")


class HardwareCommunicator(Thread):
    statusHandler: StatusHandler
    writerThread: WriterThread
    port: serial.Serial = None
    baudrate: int = 115200
    is_running: bool = True

    def __init__(self, statusHandler, *args):
        super(HardwareCommunicator, self).__init__()
        self.statusHandler = statusHandler

        self.writerThread = WriterThread(statusHandler)

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
            self.port = serial.Serial(sport, self.baudrate)
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

    def parse_debug_message(self, line):
        if "FAIL" in line:
            self.statusHandler.setStatus(Status(503, line))

    def parse_value_message(self, line):
        pass

    def parse_line(self, line):
        decoded = line.decode("ascii").replace("\r", "").replace("\n", "")
        if len(decoded) < 1:
            return
        if "Water" in decoded:
            # got the hello message. Decide what to do
            return
        logger.debug(f"Get line: {decoded}")
        try:
            {">": self.parse_debug_message, "$": self.parse_value_message}[decoded[0]](
                decoded
            )
        except Exception:
            logger.debug(f"Unrecognized command: {decoded}")

    def run(self):

        self.open_serial_port()

        while self.is_running:

            if self.port.is_open:
                line = self.port.readline()
                self.parse_line(line)
        # metric = MetricsData(measurement="waterlevel", field="tank1", value=level)
        # try:
        # backend_connector.push_metrics([metric])
        # except Exception:
        # pass
