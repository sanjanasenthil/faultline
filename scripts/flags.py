#!/usr/bin/env python3
"""Small helper for the OpenTelemetry Demo flagd-ui API."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


DEFAULT_API = "http://localhost:8080/feature/api"
DAY1_FLAGS = {
    "adFailure": "on",
    "cartFailure": "100%",
    "paymentFailure": "100%",
}


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Flag API request failed: {exc}") from exc
    return json.loads(body) if body else {}


def read_config(api: str) -> dict:
    return request_json("GET", f"{api}/read")


def write_config(api: str, config: dict) -> None:
    request_json("POST", f"{api}/write", {"data": config})


def validate_flag(config: dict, flag: str, variant: str) -> None:
    flags = config.get("flags", {})
    if flag not in flags:
        available = ", ".join(sorted(flags))
        raise SystemExit(f"Unknown flag '{flag}'. Available flags: {available}")
    variants = flags[flag].get("variants", {})
    if variant not in variants:
        available = ", ".join(sorted(variants))
        raise SystemExit(f"Unknown variant '{variant}' for {flag}. Available variants: {available}")


def set_flag(api: str, flag: str, variant: str) -> None:
    config = read_config(api)
    validate_flag(config, flag, variant)
    config["flags"][flag]["defaultVariant"] = variant
    write_config(api, config)


def reset_flags(api: str, flags: list[str] | None = None) -> None:
    config = read_config(api)
    target_flags = flags or list(config.get("flags", {}))
    for flag in target_flags:
        validate_flag(config, flag, "off")
        config["flags"][flag]["defaultVariant"] = "off"
    write_config(api, config)


def list_flags(api: str) -> None:
    config = read_config(api)
    for flag, body in sorted(config.get("flags", {}).items()):
        variants = ", ".join(body.get("variants", {}).keys())
        print(f"{flag}: default={body.get('defaultVariant')} variants=[{variants}]")


def cycle_day1(api: str, hold_seconds: float) -> None:
    print("Resetting Day 1 flags to off")
    reset_flags(api, list(DAY1_FLAGS))
    for flag, variant in DAY1_FLAGS.items():
        print(f"Enabling {flag}={variant}")
        set_flag(api, flag, variant)
        time.sleep(hold_seconds)
        print(f"Resetting {flag}=off")
        set_flag(api, flag, "off")
    print("Done")


def main() -> int:
    parser = argparse.ArgumentParser(description="Toggle OpenTelemetry Demo feature-flag faults.")
    parser.add_argument("--api", default=DEFAULT_API, help=f"flagd-ui API base URL, default {DEFAULT_API}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List live flags and variants.")

    set_parser = subparsers.add_parser("set", help="Set one flag default variant.")
    set_parser.add_argument("flag")
    set_parser.add_argument("variant")

    reset_parser = subparsers.add_parser("reset", help="Reset flags to their off variant.")
    reset_parser.add_argument("flags", nargs="*", help="Optional specific flags. Defaults to all flags.")

    cycle_parser = subparsers.add_parser("cycle-day1", help="Enable and reset the three Day 1 faults.")
    cycle_parser.add_argument("--hold-seconds", type=float, default=10.0)

    args = parser.parse_args()
    if args.command == "list":
        list_flags(args.api)
    elif args.command == "set":
        set_flag(args.api, args.flag, args.variant)
    elif args.command == "reset":
        reset_flags(args.api, args.flags or None)
    elif args.command == "cycle-day1":
        cycle_day1(args.api, args.hold_seconds)
    else:
        parser.error("unknown command")
    return 0


if __name__ == "__main__":
    sys.exit(main())
