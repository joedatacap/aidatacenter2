"""Validate a licensed provider export and atomically update the separate market cache.

Credentials belong to the server-side exporter, never this public snapshot.
Input requirements and licensing gate: docs/WATCH_MARKET_DATA.md.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from neocloud.market_snapshot import CACHE, atomic_json, refresh_market_snapshot, utc
from neocloud.market_snapshot import registry_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Local reviewed/licensed provider JSON export; never committed raw credentials.",
    )
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument(
        "--now",
        default=datetime.now(timezone.utc).isoformat(),
        help="Explicit timezone timestamp; defaults to actual refresh time.",
    )
    parser.add_argument(
        "--allow-partial-regression",
        action="store_true",
        help="Explicitly replace wider previous coverage with an audited partial snapshot. Dates are still validated.",
    )
    args = parser.parse_args()
    try:
        with args.input.open("rb") as source:
            raw = source.read(10_000_001)
        if len(raw) > 10_000_000:
            raise ValueError("Input exceeds 10 MB bounded snapshot limit")
        payload = json.loads(raw)
    except (OSError, ValueError) as exc:
        atomic_json(
            args.cache.with_suffix(".refresh.json"),
            {
                "status": "failed",
                "last_attempt_at": utc(args.now),
                "error_type": type(exc).__name__,
                "reason": "Provider input unavailable or malformed; last good market cache retained.",
            },
        )
        print(
            json.dumps(
                {
                    "status": "failed",
                    "cache_replaced": False,
                    "error_type": type(exc).__name__,
                }
            )
        )
        return 2
    result = refresh_market_snapshot(
        payload,
        cache_path=args.cache,
        now=args.now,
        registry=registry_rows(),
        allow_partial_regression=args.allow_partial_regression,
    )
    print(json.dumps(result))
    return 0 if result["status"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
