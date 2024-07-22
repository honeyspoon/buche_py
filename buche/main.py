import sys
import re
import colorama
import json
import datetime
from colorama import Fore, Style

LOG_LEVEL_REGEX = re.compile(r"\b(DEBUG|INFO|WARN|ERROR)\b")


def format_timestamp(timestamp_ms):
    timestamp_s = timestamp_ms / 1000.0
    dt = datetime.datetime.fromtimestamp(timestamp_s)
    time_str = dt.strftime("%H:%M:%S")

    return time_str


COLORS = {
    "DEBUG": Fore.BLUE,
    "INFO": Fore.GREEN,
    "WARN": Fore.YELLOW,
    "ERROR": Fore.RED,
}


def main():
    colorama.init()

    for line in sys.stdin:
        try:
            o = json.loads(line)
            ts = format_timestamp(o["timestamp"])
            del o["timestamp"]
            level = o["level"]
            level = COLORS.get(level, Fore.WHITE) + level + Fore.RESET

            del o["level"]
            target = o["target"]
            del o["target"]
            message = o["message"]
            del o["message"]

            log = f"{ts} [{level}] [{target}] {message}"
            sys.stdout.write(log)
            sys.stdout.write("\n")
            sys.stdout.write(o)
        except Exception:
            sys.stdout.write(line)

        sys.stdout.flush()


if __name__ == "__main__":
    main()
