import configargparse
from .http_server import HTTPServer
import uvicorn

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
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
    )

    parser.add_argument(
        "-b",
        "--backend-addr",
        type=str,
        help="Address of backend",
    )

    parser.add_argument(
        "--backend-port",
        type=int,
        help="Port of backend",
    )
    args, _ = parser.parse_known_args()

    print(args)

    http_server = HTTPServer()
    app = http_server.build_app()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        lifespan="on",
    )