import contextlib
import logging as logger
import signal
import time
from threading import Thread

import configargparse
import uvicorn

from connector.status_handler import Status, StatusHandler

from .backend_connector import BackendConfig, BackendConnector, MetricsData
from .communication import HardwareCommunicator
from .http_server import HTTPServer, HTTPServerConfig

LOGGER_FORMAT = "%(levelname)s:\t%(asctime)s - %(name)s  - %(message)s"


def main():
    parser = configargparse.ArgParser()

    parser.add_argument(
        "-c",
        "--config",
        is_config_file=True,
        help="The configuration file",
    )

    parser.add_argument(
        "--host",
        type=str,
        required=True,
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        required=True,
    )

    parser.add_argument(
        "-b",
        "--backend-addr",
        type=str,
        help="Address of backend",
        required=True,
    )

    parser.add_argument(
        "--backend-port",
        type=int,
        help="Port of backend",
        required=True,
    )

    parser.add_argument(
        "--workstation-name",
        type=str,
        required=True,
    )

    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        help="Interval between messages requesting the status of the whole station",
        required=False,
        default=5,
    )

    parser.add_argument(
        "-br",
        "--baudrate",
        type=int,  # consider using choice type
        required=False,
        default=115200,
    )

    parser.add_argument("-d", "--debug", action="store_true", required=False)

    args, _ = parser.parse_known_args()

    backendConfig = BackendConfig(
        args.backend_addr,
        args.backend_port,
        args.workstation_name,
    )
    # backendConnector = BackendConnector(backendConfig)

    globalStatusHandler = StatusHandler(Status(200, "Starting up."))

    logger.basicConfig(level=logger.DEBUG, format=LOGGER_FORMAT)

    communicationThread = HardwareCommunicator(globalStatusHandler, args)
    communicationThread.start()

    def killall(*args):
        logger.debug("Initiating graceful shutdown")
        with contextlib.suppress(Exception):
            communicationThread.stop()
            communicationThread.join()
            exit(0)

    signal.signal(signal.SIGINT, killall)

    http_config = HTTPServerConfig(
        args.backend_addr,
        args.backend_port,
    )
    http_server = HTTPServer(http_config, globalStatusHandler, communicationThread)
    app = http_server.build_app()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        lifespan="on",
    )

    with contextlib.suppress(Exception):
        communicationThread.stop()
        communicationThread.join()
        exit(0)
