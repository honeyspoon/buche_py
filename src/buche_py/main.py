import sys
import re
import colorama
import json
import datetime
from colorama import Fore
from rich.pretty import pprint

LOG_LEVEL_REGEX = re.compile(r"\b(DEBUG|INFO|WARN|ERROR)\b")

OPTION_REGEX = re.compile(r"[A-Z][a-z]*\((.*)\)?")

TRAILING_COMMA_REGEX = re.compile(r",(?=\s*[\]}])")


def remove_trailing_commas(s):
    return re.sub(TRAILING_COMMA_REGEX, "", s)


def unwrap_option(s):
    s = re.sub(OPTION_REGEX, r"\1", s)
    return s


def remove_struct_names(s):
    return re.sub(r"\w+ { ", "{ ", s)


def replace_none(s):
    return s.replace("None", "null")


KEY_REGEX = re.compile(r"(\w+): ")


def quote_keys(s):
    return re.sub(KEY_REGEX, r'"\1": ', s)


VALUE_REGEX = re.compile(r": ([\w]*), ")


def quote_value(s):
    return re.sub(VALUE_REGEX, r': "\1", ', s)


DURATION_REGEX = re.compile(r": (\d*\w), ")


def quote_duration(s):
    return re.sub(DURATION_REGEX, r': "\1", ', s)


def rust_debug_to_json(s):
    s = remove_struct_names(s)
    while True:
        ss = unwrap_option(s)
        if s == ss:
            break
        s = ss
    s = replace_none(s)
    s = remove_trailing_commas(s)
    s = quote_keys(s)
    s = quote_value(s)
    s = quote_duration(s)
    s = s.replace(")", "")
    s = s.replace("(", "")

    return s


def format_timestamp(timestamp_ms):
    if isinstance(timestamp_ms, str):
        return timestamp_ms

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


MAX_LENGTH = 1000


def truncate(s):
    if not isinstance(s, str):
        return s

    if len(s) <= MAX_LENGTH:
        return s

    part_length = (MAX_LENGTH - 5) // 2
    return s[:part_length] + "\\r...\\r" + s[-part_length:]


def error_stack(v):
    v = v.replace(r"\n", "\n")
    v = truncate(v)
    return v


def main():
    colorama.init()

    for line in sys.stdin:
        try:
            o = json.loads(line)
            ts = format_timestamp(o.pop("timestamp", ""))
            level = o.pop("level", "")
            level = COLORS.get(level, Fore.WHITE) + level + Fore.RESET

            target = o.pop("target", "")
            filename = o.pop("filename", "")
            line_number = o.pop("line_number", "")

            message = o.pop("message", "")

            log = f"{ts} [{level}] [{target} {filename}:{line_number}] {message}"

            print(log)

            for k, v in o.items():
                if "dd." in k:
                    continue
                print(f"- {k}: ", end="")
                if k == "error.stack":
                    print(error_stack(v))
                    continue
                try:
                    v = rust_debug_to_json(v)
                    s = json.loads(v)
                except Exception:
                    s = truncate(v)

                pprint(s)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print("buche err", e)

        sys.stdout.flush()


if __name__ == "__main__":
    main()
