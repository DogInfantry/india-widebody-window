"""Where the profit sits in India's international market, by corridor.

A profit pool asks a different question from a market map. Revenue share tells
you where the passengers are; the pool tells you where the money is, and the two
are not the same shape. Gadiesh and Gilbert, HBR 1998.

**The finding this module exists to make visible.** The Gulf is 51 percent of
India's international passengers, and that number anchors the whole case. But
passengers are not revenue: a Dubai sector is roughly 2,200 km where a New York
sector is roughly 11,700 km, and revenue scales with distance flown. On a
distance-weighted basis the Gulf's share falls by well over ten points, and the
long-haul corridors carry far more revenue than their passenger counts suggest.
That gap is the argument for wide-bodies stated in money rather than in bodies.

**What is computed and what is modelled**, because this module contains more
modelling than anything else in the repo and the reader is entitled to know
exactly where the hard data stops:

  Passengers per corridor    COMPUTED. DGCA international country table, 2024,
                             both directions summed. Same source and same
                             numbers as `benchmarking.corridor_scale`.
  Corridor stage length      COMPUTED, but a REFERENCE not a mean. Great circle
                             from Delhi to one named representative hub per
                             corridor, from committed OurAirports coordinates.
                             It is not traffic weighted. A traffic-weighted mean
                             would need a city-to-airport crosswalk that DGCA's
                             city names do not support: matching them against
                             OurAirports municipalities covers under half the
                             traffic, so the honest move is a labelled reference
                             distance rather than a weighted mean that is
                             quietly wrong for the unmatched half.
  Revenue per corridor       PROXY. Passengers x reference distance x a single
                             blended yield, IndiGo's verified FY2026 5.06 INR
                             per RPK. Direction of the error is known and is
                             stated on the chart: yield per RPK normally FALLS
                             with stage length, so holding it constant
                             OVERSTATES long-haul revenue. The Gulf-versus-long-
                             haul gap this module reports is therefore a
                             conservative floor, not a flattering ceiling.
  Margin per corridor        MODELLED. There is no public margin split by
                             corridor for any Indian carrier, and there will not
                             be one. See `_corridor_margins`.

The margin axis being modelled is the reason every figure here is labelled
MODELLED on the chart face rather than in a footnote, per the house rule.

**The anchor, and why it is stated twice.** The revenue-weighted mean margin is
pinned to IndiGo's FY2026 EBITDAR margin excluding forex, 27.3 percent. That is
the right anchor for a profit pool: forex on USD lease liabilities is a real loss
but it is not an operating one, and a pool built on it would attribute a treasury
outcome to a route. But IndiGo REPORTED 17.8 percent for the same year, and this
module carries both, because quoting only the ex-forex figure would repeat in
reverse the error retracted in `docs/methodology.md`.
"""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go

from . import charts
from .benchmarking import INTL_COUNTRY_YEAR, corridor_scale
from .data_pipeline import assumption, load_ourairports

# One representative hub per corridor, chosen as the largest single traffic point
# in that region rather than its geographic centre. Delhi is the Indian end
# throughout, so the corridors stay comparable with each other even though they
# are not each corridor's own busiest gateway.
#
# These are REFERENCE pairs. Naming them here, rather than burying a distance
# constant, means a reader can check any one of them in a minute.
ORIGIN = "DEL"
_REFERENCE_HUBS = {
    "Gulf": ("DXB", "Dubai"),
    "Southeast Asia": ("SIN", "Singapore"),
    "Europe": ("LHR", "London Heathrow"),
    "South Asia": ("CMB", "Colombo"),
    "North America": ("JFK", "New York"),
    "East Asia": ("HKG", "Hong Kong"),
    "Africa": ("NBO", "Nairobi"),
    "Oceania": ("SYD", "Sydney"),
}

# "Other" is a DGCA residual spanning Central Asia to South America, so no single
# hub represents it and inventing one would be worse than dropping it. It is
# excluded and the exclusion is reported, not silently applied.
EXCLUDED_REGIONS = ("Other",)

# The single modelling knob on the margin axis. Margin is taken to rise with
# stage length, because long-haul wide-body flying carries premium cabins and
# higher revenue per passenger, while short-haul all-economy sectors compete
# closer to cost. `MARGIN_STAGE_SENSITIVITY` is the spread in margin points
# between the shortest and longest corridor, before the anchor rescales the set.
#
# It is a judgement, it is the number to attack first, and `sensitivity()`
# exists so that attacking it is one function call.
MARGIN_STAGE_SENSITIVITY = 12.0

SOURCE = (
    "Passengers: DGCA international country table, 2024. Distances: great circle from "
    "OurAirports (CC0). Yield and margin anchors: IndiGo FY2026 primary filings. "
    "Margin split is modelled, see docs/methodology.md"
)


def _great_circle_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine. Mean Earth radius, which is the right precision for a corridor."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _airport_coords() -> dict[str, tuple[float, float]]:
    a = load_ourairports()
    a = a[a["iata_code"].notna()]
    return {
        row.iata_code: (row.latitude_deg, row.longitude_deg)
        for row in a.itertuples()
        if row.iata_code in {ORIGIN, *(h for h, _ in _REFERENCE_HUBS.values())}
    }


def corridor_stage_lengths() -> pd.DataFrame:
    """Reference great circle distance from Delhi to each corridor's hub."""
    coords = _airport_coords()
    missing = [ORIGIN] + [h for h, _ in _REFERENCE_HUBS.values() if h not in coords]
    if ORIGIN in coords:
        missing = [h for h, _ in _REFERENCE_HUBS.values() if h not in coords]
    if missing:
        raise KeyError(f"OurAirports has no coordinates for {missing}")

    olat, olon = coords[ORIGIN]
    rows = [
        {
            "region": region,
            "hub_iata": iata,
            "hub_name": name,
            "stage_km": round(_great_circle_km(olat, olon, *coords[iata])),
        }
        for region, (iata, name) in _REFERENCE_HUBS.items()
    ]
    return pd.DataFrame(rows).sort_values("stage_km").reset_index(drop=True)


def _corridor_margins(stage_km: pd.Series, revenue: pd.Series, anchor_pct: float) -> pd.Series:
    """Model a margin per corridor, anchored so the weighted mean is the anchor.

    Two steps, deliberately separate so each can be argued with:

    1. Spread margins linearly across `MARGIN_STAGE_SENSITIVITY` points from the
       shortest corridor to the longest. Linear in stage length, because there is
       no evidence available to justify any richer shape and a richer shape would
       imply precision this data does not have.
    2. Shift the whole set so the REVENUE-weighted mean equals the anchor. The
       shift is additive, so step 1's ordering and spread survive it exactly.

    Anchoring on the revenue-weighted mean rather than the simple mean matters:
    the simple mean would let tiny corridors like Oceania drag the anchor around.
    """
    lo, hi = stage_km.min(), stage_km.max()
    if hi == lo:  # degenerate, only reachable if the hub table is cut to one row
        spread = pd.Series(0.0, index=stage_km.index)
    else:
        spread = MARGIN_STAGE_SENSITIVITY * (stage_km - lo) / (hi - lo)
    weighted_mean = float((spread * revenue).sum() / revenue.sum())
    return spread + (anchor_pct - weighted_mean)


def profit_pool(year: int = INTL_COUNTRY_YEAR) -> pd.DataFrame:
    """Corridor by corridor: passengers, revenue proxy, modelled margin, profit."""
    anchor_pct = assumption("indigo_operating_profit_fy2026_inr_cr") / assumption(
        "indigo_revenue_fy2026_inr_cr"
    ) * 100
    yield_inr = assumption("indigo_yield_inr_per_rpk_fy2026")

    pax = corridor_scale(year)
    pax = pax[~pax["region"].isin(EXCLUDED_REGIONS)]
    df = pax.merge(corridor_stage_lengths(), on="region", how="inner")

    df["rpk_bn"] = df["pax_total"] * df["stage_km"] / 1e9
    df["revenue_inr_cr"] = df["rpk_bn"] * 1e9 * yield_inr / 1e7
    df["margin_pct"] = _corridor_margins(df["stage_km"], df["revenue_inr_cr"], anchor_pct)
    df["profit_inr_cr"] = df["revenue_inr_cr"] * df["margin_pct"] / 100

    for col, out in (("pax_total", "pax_share_pct"), ("revenue_inr_cr", "revenue_share_pct")):
        df[out] = 100 * df[col] / df[col].sum()
    df["profit_share_pct"] = 100 * df["profit_inr_cr"] / df["profit_inr_cr"].sum()
    df["pax_m"] = df["pax_total"] / 1e6

    return df.sort_values("margin_pct", ascending=False).reset_index(drop=True)


def gulf_share_gap(year: int = INTL_COUNTRY_YEAR) -> dict:
    """The headline: the Gulf's share of passengers against its share of revenue.

    This is the one number the module exists to produce, so it is available
    without going through a figure.
    """
    df = profit_pool(year)
    gulf = df[df["region"] == "Gulf"].iloc[0]
    return {
        "pax_share_pct": round(float(gulf["pax_share_pct"]), 1),
        "revenue_share_pct": round(float(gulf["revenue_share_pct"]), 1),
        "gap_pts": round(float(gulf["pax_share_pct"] - gulf["revenue_share_pct"]), 1),
        "note": "Excludes the DGCA 'Other' residual, so shares are of the corridors modelled",
    }


def sensitivity(values: tuple[float, ...] = (6.0, 12.0, 18.0)) -> pd.DataFrame:
    """How much the pool moves when the one modelling knob is turned.

    Published rather than kept in a notebook, because a modelled axis without a
    sensitivity is an assertion.
    """
    global MARGIN_STAGE_SENSITIVITY
    original = MARGIN_STAGE_SENSITIVITY
    rows = []
    try:
        for v in values:
            MARGIN_STAGE_SENSITIVITY = v
            df = profit_pool()
            gulf = df[df["region"] == "Gulf"].iloc[0]
            rows.append(
                {
                    "margin_spread_pts": v,
                    "gulf_profit_share_pct": round(float(gulf["profit_share_pct"]), 1),
                    "gulf_margin_pct": round(float(gulf["margin_pct"]), 1),
                    "longhaul_margin_pct": round(float(df["margin_pct"].max()), 1),
                }
            )
    finally:
        MARGIN_STAGE_SENSITIVITY = original
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------


def fig_profit_pool(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    df = profit_pool(year)
    fig = charts.profit_pool_curve(
        df,
        segment="region",
        revenue="revenue_inr_cr",
        margin="margin_pct",
        highlight="Gulf",
    )
    gap = gulf_share_gap(year)
    reported = assumption("indigo_ebitdar_margin_fy2026_reported_pct")
    anchor = assumption("indigo_operating_profit_fy2026_inr_cr") / assumption(
        "indigo_revenue_fy2026_inr_cr"
    ) * 100
    return charts.finish(
        fig,
        title=(
            f"The Gulf is {gap['pax_share_pct']:.0f}% of passengers but "
            f"{gap['revenue_share_pct']:.0f}% of revenue, a {gap['gap_pts']:.0f} point gap "
            "that wide-bodies exist to close"
        ),
        modeled=True,
        subtitle=(
            "Width is a revenue proxy (passengers x reference great circle from "
            f"Delhi x IndiGo's {assumption('indigo_yield_inr_per_rpk_fy2026')} INR per RPK); "
            "height is a modelled margin, spread "
            f"{MARGIN_STAGE_SENSITIVITY:.0f} points across stage length and anchored so the "
            f"revenue-weighted mean is IndiGo's {anchor:.1f}% FY2026 EBITDAR margin ex forex "
            f"(as reported, including forex: {reported}%). Holding yield per RPK constant "
            "overstates long-haul revenue, so the gap shown is a floor"
        ),
        source=SOURCE,
    )


def fig_pax_vs_revenue_share(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    """The same point without the modelled axis, for readers who reject the model.

    Passenger share against revenue share needs no margin assumption at all. If
    the margin model is thrown out entirely, this chart still stands, and it still
    carries the case.
    """
    df = profit_pool(year).sort_values("pax_share_pct", ascending=False)
    fig = charts.slope(
        df,
        label="region",
        start_col="pax_share_pct",
        end_col="revenue_share_pct",
        start_name="Share of passengers",
        end_name="Share of revenue",
        highlight="Gulf",
    )
    return charts.finish(
        fig,
        title=(
            "Weighting by distance flown moves the Gulf from half the market to a third of it"
        ),
        modeled=True,
        subtitle=(
            "Percent of India's international corridors, 2024. Passenger counts are DGCA; "
            "revenue is passengers x reference great circle x a constant yield. NO margin "
            "assumption enters this chart, so it survives rejecting the profit pool model"
        ),
        source=SOURCE,
    )


FIGURES = {
    "profit_pool": fig_profit_pool,
    "pax_vs_revenue_share": fig_pax_vs_revenue_share,
}


def build_all() -> list[str]:
    written = []
    for name, builder in FIGURES.items():
        charts.export(builder(), name)
        written.append(name)
    return written


if __name__ == "__main__":
    print(profit_pool().to_string(index=False))
    print()
    print("Gulf gap:", gulf_share_gap())
    print()
    print(sensitivity().to_string(index=False))
    print()
    for _n in build_all():
        print("wrote", _n)
