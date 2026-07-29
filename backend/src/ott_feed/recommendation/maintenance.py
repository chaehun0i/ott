"""One-shot U05 maintenance entrypoint."""

from __future__ import annotations

import argparse

from ott_feed.recommendation.application.retention import plan_retention


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="recommendation-maintenance")
    parser.add_argument("operation", choices=("retention", "verify"))
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args(argv)
    if args.operation == "retention":
        plan_retention((), args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
