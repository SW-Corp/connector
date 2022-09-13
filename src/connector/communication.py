import time
import sys
import glob
import serial
from serial.tools import list_ports
import logging as logger

from connector.status_handler import StatusHandler, Status

from .backend_connector import MetricsData, BackendConnector
from threading import Thread

vidpid_pairs = set([
    (0x2341, 0x43), # Arduino Uno R3
    (0x1A86, 0x7523), # CH340
    (0x1A86, 0x7522), # CH340
    (0x1A86, 0x5523), # CH341 in serial mode
    (0x1A86, 0x7584), # CH340S
])

class HardwareCommunicator(Thread):
    statusHandler: StatusHandler
    port: serial.Serial = None
    baudrate: int = 115200
    is_running: bool = True
    
    def __init__(self, statusHandler, *args):
        super(HardwareCommunicator, self).__init__()
        self.statusHandler = statusHandler
    
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
            self.statusHandler.setStatus(Status(200, "Serial port opened successfully."))
        except:
            logger.error(f"Can't open serial port {sport}")
            self.statusHandler.setStatus(Status(500, f"Can't open serial port {sport}"))

    def parse_line(self, line):
        logger.info(f"Get line: {line.decode('ascii')}")
    
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