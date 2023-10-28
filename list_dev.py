import logging

from ppadb.client import Client as AdbClient
from rich.logging import RichHandler
from rich.traceback import install

install(show_locals=True)

FORMAT = "%(message)s"
logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])


def main():
    # Default is "127.0.0.1" and 5037
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()

    for device in devices:
        logging.info(f"Found device [{device.serial}]")
        try:
            model = device.shell("getprop ro.product.model").strip()
            logging.info(f"SN: [{device.serial}] Model: [{model}]")
        except RuntimeError:
            logging.error(f"Device SN: [{device.serial}] is has not been authorized!")


if __name__ == "__main__":
    main()
