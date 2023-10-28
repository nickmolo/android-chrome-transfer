import argparse
import json
import logging
import urllib.parse

import requests
from ppadb.client import Client as AdbClient
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)
from rich.traceback import install

install(show_locals=True)

progress = Progress(
    TextColumn("{task.description}", justify="right"),
    BarColumn(),
    TextColumn("[green]{task.completed}/{task.total}"),
    "•",
    TimeRemainingColumn(),
)

FORMAT = "%(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Restore Android Chrome tabs to device")
    parser.add_argument("-s", "--serial-no", help="Serial number of device to restore too", required=True)
    parser.add_argument("-t", "--tabs", help="json file of tabs to be restored.", required=True)

    args = parser.parse_args()
    logger.debug(args)
    # Default is "127.0.0.1" and 5037
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()

    for device in devices:
        logger.info(f"Found device [{device.serial}]")
        try:
            model = device.shell("getprop ro.product.model").strip()
            logger.info(f"SN: [{device.serial}] Model: [{model}]")
        except RuntimeError:
            logger.error(f"Device SN: [{device.serial}] is has not been authorized!")

        if device.serial == args.serial_no:
            logger.debug("Serial Match!")
            with open(args.tabs) as f:
                tabs = json.load(f)
            logger.debug(tabs)
            logger.info(f"Restoring [{len(tabs)}] tabs to: [{model}] SN: [{device.serial}]")
            device.forward("tcp:9222", "localabstract:chrome_devtools_remote")
            device.shell("monkey -p com.android.chrome 1")
            with progress:
                task = progress.add_task("Restoring Tabs", total=len(tabs))
                for tab in tabs:
                    logger.debug(tab["url"])
                    full_url = "http://localhost:9222/json/new?{}".format(urllib.parse.quote(tab["url"], safe=""))
                    logger.debug(full_url)
                    response = requests.put(full_url)
                    logger.debug(response)
                    progress.advance(task)
            progress.remove_task(task)
            device.killforward("tcp:9222")


if __name__ == "__main__":
    main()
