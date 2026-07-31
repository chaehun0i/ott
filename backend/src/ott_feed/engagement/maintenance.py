"""U06 bounded maintenance command."""

from __future__ import annotations

import argparse

from ott_feed.engagement.config import EngagementSettings

COMMANDS = frozenset({"retention", "verify-audit", "verify-recovery"})


def run(command: str) -> int:
    EngagementSettings.from_environment()
    return 0 if command in COMMANDS else 64


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=sorted(COMMANDS))
    arguments = parser.parse_args()
    return run(arguments.command)


if __name__ == "__main__":
    raise SystemExit(main())
