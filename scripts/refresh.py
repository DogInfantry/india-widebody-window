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
    benchmarking,
    charts,
    data_pipeline,
    market_sizing,
    profit_pools,
    scenario,
)


def build_kpis() -> list[dict]:
    """The three hero numbers, computed rather than typed.

    Every one of these is recomputed from the parquet on each refresh, so the
    page cannot drift away from the data behind it. A hardcoded hero number is
    the easiest thing in a project like this to leave stale.
    """
    corridor = benchmarking.corridor_scale()
    carriers = benchmarking.who_carries_india()
    intl = benchmarking.load_dgca_intl_country()
    total = intl[intl["year"] == benchmarking.INTL_COUNTRY_YEAR]["pax_total"].sum()

    gulf = corridor.set_index("region").loc["Gulf"]
    europe = corridor.set_index("region").loc["Europe"]
    indian = carriers.set_index("carrier_group").loc["Indian", "share_pct"]

    stage = benchmarking.carrier_operating_summary(
        benchmarking.LATEST_COMPLETE_YEAR, international=True
    ).set_index("airline")

    return [
        charts.kpi(
            f"{total / 1e6:.0f}M",
            "India international sector passengers",
            note=f"{benchmarking.INTL_COUNTRY_YEAR}, both directions, all carriers (DGCA)",
        ),
        charts.kpi(
            f"{gulf['share_pct']:.0f}%",
            "of that traffic touches a Gulf point",
            note=f"{gulf['pax_total'] / 1e6:.1f}M passengers, "
            f"{gulf['pax_total'] / europe['pax_total']:.1f}x the entire direct Europe market",
        ),
        charts.kpi(
            f"{indian:.0f}%",
            "is flown by Indian carriers",
            note="Gulf carriers take a quarter of India's own international market",
        ),
        charts.kpi(
            f"{stage.loc['Air India', 'stage_length_km'] / stage.loc['IndiGo', 'stage_length_km']:.1f}x",
            "Air India's average international flight vs IndiGo's",
            note=f"{stage.loc['Air India', 'stage_length_km']:,.0f} km against "
            f"{stage.loc['IndiGo', 'stage_length_km']:,.0f} km, {benchmarking.LATEST_COMPLETE_YEAR}",
        ),
    ]


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
    ):
        print(f"  {name}")

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
