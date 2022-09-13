import time
from threading import Thread

import configargparse
import uvicorn
import logging as logger

from connector.status_handler import StatusHandler, Status

from .backend_connector import BackendConfig, BackendConnector, MetricsData
from .http_server import HTTPServer, HTTPServerConfig

from .communication import HardwareCommunicator

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
        "-d",
        "--debug",
        action="store_true",
        required=False
    )

    args, _ = parser.parse_known_args()

    backendConfig = BackendConfig(
        args.backend_addr,
        args.backend_port,
        args.workstation_name,
    )
    # backendConnector = BackendConnector(backendConfig)

    globalStatusHandler = StatusHandler(Status(200, "Starting up."))

    logger.basicConfig(level=logger.DEBUG, format=LOGGER_FORMAT)

    communicationThread = HardwareCommunicator(globalStatusHandler)
    communicationThread.start()

"""
    http_config = HTTPServerConfig(
        args.backend_addr,
        args.backend_port,
    )
    http_server = HTTPServer(http_config, globalStatusHandler)
    app = http_server.build_app()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        lifespan="on",
    )
    """
