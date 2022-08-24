import configargparse

def main():
    parser = configargparse.ArgParser()

    parser.add_argument(
        "-c",
        "--config",
        is_config_file=True,
        help="The configuration file",
    )
    
    parser.add_argument(
        "-b",
        "--backend-addr",
        type=str,
        help="Address of backend",
    )

    parser.add_argument(
        "-p",
        "--backend-port",
        type=str,
        help="Port of backend",
    )