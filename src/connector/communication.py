import time
import sys
import glob
import serial
from serial.tools import list_ports
import logging as logger

from connector.status_handler import StatusHandler, Status

from .backend_connector import MetricsData, BackendConnector

vidpid_pairs = set([
    (0x2341, 0x43), # Arduino Uno R3
    (0x1A86, 0x7523), # CH340
    (0x1A86, 0x7522), # CH340
    (0x1A86, 0x5523), # CH341 in serial mode
    (0x1A86, 0x7584), # CH340S
])

def start_hardware_comm(statusHandler: StatusHandler): #backend_connector: BackendConnector):
    
    sport = None
    baudrate = 115200  # should be configurable
    
    for port in list(list_ports.comports()):
        if port.vid and port.pid:
            if (port.vid, port.pid) in vidpid_pairs:
                print(f"Found a serial port. Location: {port.device}")
                sport = port.device
                break

    if not sport:
        logger.error("No valid COM port was found. Check your USB device.")
        statusHandler.setStatus(Status(500, "No valid COM port was found."))
    
    # serial_port = serial.Serial()
    
    while True:
        time.sleep(1)
        # metric = MetricsData(measurement="waterlevel", field="tank1", value=level)
        # try:
            # backend_connector.push_metrics([metric])
        # except Exception:
            # pass