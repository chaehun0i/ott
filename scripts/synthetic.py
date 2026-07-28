"""External user-path synthetic checks without third-party dependencies."""

import json
import os
import sys
import urllib.request


def check(base_url: str, path: str) -> None:
    with urllib.request.urlopen(f"{base_url.rstrip('/')}{path}", timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"synthetic failed: {path} status={response.status}")
        json.loads(response.read())


if __name__ == "__main__":
    check(sys.argv[1], "/api/v1/health/ready")
    if os.getenv("SYNTHETIC_FULL") == "1":
        check(sys.argv[1], "/api/v1/feed?limit=1")
        check(sys.argv[1], "/api/v1/recommendations/fallback?synthetic=true")
    print("synthetic_success")
