import datetime
import json
import logging
import operator

import requests
from ppadb.client import Client as AdbClient
from rich.logging import RichHandler
from rich.traceback import install

install(show_locals=True)

FORMAT = "%(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main():
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
        logger.info(f"Backing up tabs from device: [{model}] SN: [{device.serial}]")
        now = datetime.datetime.now().isoformat(timespec="seconds").replace(":", "")
        out_file = "{}-{}-{}.json".format(now, model.replace(" ", "-"), device.serial)

        logger.info(f"Will write tabs to [{out_file}]")

        device.forward("tcp:9222", "localabstract:chrome_devtools_remote")
        device.shell("monkey -p com.android.chrome 1")
        response = requests.get("http://localhost:9222/json/list")
        data = json.loads(response.content)
        data = [item for item in data if item["id"].isdigit()]
        data.sort(key=lambda x: int(operator.itemgetter("id")(x)))

        with open(out_file, "w+") as f:
            json.dump(data, f, indent=4)
        device.killforward("tcp:9222")


if __name__ == "__main__":
    main()
