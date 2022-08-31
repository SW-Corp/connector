import time
from threading import Thread

import configargparse
import uvicorn

from .backend_connector import BackendConfig, BackendConnector, MetricsData
from .http_server import HTTPServer, HTTPServerConfig


def dummy_run_hardware_communicator(backend_connector: BackendConnector):
    level = 0
    while True:
        time.sleep(1)
        metric = MetricsData(measurement="waterlevel", field="tank1", value=level)
        try:
            backend_connector.push_metrics([metric])
        except Exception:
            pass
        level += 1


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

    args, _ = parser.parse_known_args()

    print(args)

    backendConfig = BackendConfig(
        args.backend_addr,
        args.backend_port,
        args.workstation_name,
    )
    backendConnector = BackendConnector(backendConfig)
    dummyThread = Thread(
        target=dummy_run_hardware_communicator, args=(backendConnector,)
    )
    dummyThread.start()

    http_config = HTTPServerConfig(
        args.backend_addr,
        args.backend_port,
    )
    http_server = HTTPServer(http_config)
    app = http_server.build_app()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        lifespan="on",
    )
