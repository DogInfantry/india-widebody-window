"""Single entry point: pull the data, rebuild every figure, write the KPI cards.

This is exactly what CI runs. If it works here it works there, so there is no
second code path to keep in sync and no chance of the page being built by a
process nobody can reproduce.

    python scripts/refresh.py
    python scripts/refresh.py --no-fetch    # rebuild figures from cached pulls
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (  # noqa: E402
    app_export,
    benchmarking,
    cargo,
    charts,
    data_pipeline,
    fleet_gap,
    market_sizing,
    options,
    profit_pools,
    scenario,
)


def build_kpis() -> list[dict]:
    """The static site's four hero cards.

    The computation lives in `src/app_export.kpi_band()`, which returns six: the
    four below plus the two the delivery app adds. Slicing here rather than
    keeping a second copy is what stops the two surfaces disagreeing about a
    hero number, which is the easiest thing in a project like this to leave
    stale.
    """
    return app_export.kpi_band()[:4]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="skip the source pull and rebuild figures from what is already cached",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-download even if today's cache exists",
    )
    args = parser.parse_args()

    if not args.no_fetch:
        print("pulling sources")
        frames = data_pipeline.build_all(force=args.force)
        for name, df in frames.items():
            print(f"  {name:<24} {len(df):>7,} rows")

    print("building figures")
    for name in (
        benchmarking.build_all()
        + market_sizing.build_all()
        + profit_pools.build_all()
        + scenario.build_all()
        + fleet_gap.build_all()
        + options.build_all()
        + cargo.build_all()
    ):
        print(f"  {name}")

    print("exporting app data")
    for path in app_export.write_all():
        print(f"  {path.name}")

    cards = build_kpis()
    charts.export_kpis(cards)
    print("building kpis")
    for card in cards:
        print(f"  {card['value']:>6}  {card['label']}")

    tri = market_sizing.triangulate()
    if tri.is_provisional:
        blocked = ", ".join(e.method for e in tri.blocked)
        print(f"\nNOTE: market sizing is provisional. Blocked methods: {blocked}")
        print("      Verify the rows in data/manual/assumptions.csv to unblock them.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
