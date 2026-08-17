"""Size India's international air travel market in 2030, three ways.

The three estimates are reconciled to a **band and never averaged**. Averaging
would destroy the only genuinely useful output, the spread. Where the methods
disagree tells you which assumption the answer actually depends on, and a single
averaged number hides exactly that.

The three are chosen for **different failure modes**, not for using different
spreadsheets:

  trend       Extrapolates DGCA's own history. Fails if the past rate stops
              holding, which is precisely what a capacity shock would do.
  propensity  Fits air trips per capita against GDP per capita across peer
              countries and asks where India lands at its 2030 income. Fails if
              India is structurally unlike its income peers.

              Independence caveat, stated because the alternative is a flattering
              overstatement: the *core* of this method (elasticity, income,
              population) is World Bank only and shares nothing with the trend
              method. But two bridging ratios, the international share of Indian
              carrier traffic and the Indian carrier share of India's
              international market, are computed from DGCA. So trend and
              propensity are largely, not wholly, independent. Read the closeness
              of their answers with that in mind.
  capacity    Counts the seats the announced order books can actually fly. Fails
              if orders slip or aircraft get deployed elsewhere.

Capacity depends on hand-entered figures and refuses to run until those are
verified. That refusal is deliberate. A band built partly on unchecked numbers is
worse than a band that says out loud which leg is missing.

Base measure throughout is **DGCA international sector passengers**, both
directions summed, all carriers. Not origin-destination. See data_dictionary.md
section 1.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import charts
from .data_pipeline import (
    UnverifiedAssumption,
    assumption,
    load_dgca_domestic_carrier,
    load_dgca_intl_country,
    load_worldbank_macro,
)

TARGET_YEAR = 2030
BASE_YEAR = 2024

# Covid distorts any growth rate straddling it. Rates are fitted on the clean
# pre-covid run and on the clean recovery, rather than fitted through a crater
# and called a trend.
PRE_COVID = (2015, 2019)
POST_COVID = (2022, 2025)

# Income peers for the propensity curve, chosen to span the income range India
# will move through rather than to resemble India today.
PEERS = ("IND", "CHN", "USA", "GBR", "DEU", "SGP", "ARE", "SAU", "QAT", "OMN", "KWT", "BHR")

SOURCE = (
    "DGCA traffic statistics via github.com/Vonter/india-aviation-traffic (ODbL); "
    "World Bank Open Data (CC BY 4.0). Pulled 2026-08-15"
)


@dataclass
class Estimate:
    """One method's answer, carrying the assumptions that produced it."""

    method: str
    value_m: float | None
    assumptions: dict = field(default_factory=dict)
    blocked_reason: str | None = None

    @property
    def available(self) -> bool:
        return self.value_m is not None


@dataclass
class Triangulation:
    estimates: list[Estimate]
    base_m: float

    @property
    def available(self) -> list[Estimate]:
        return [e for e in self.estimates if e.available]

    @property
    def blocked(self) -> list[Estimate]:
        return [e for e in self.estimates if not e.available]

    @property
    def band(self) -> tuple[float, float]:
        vals = [e.value_m for e in self.available]
        if not vals:
            raise RuntimeError("no sizing method produced a value")
        return (min(vals), max(vals))

    @property
    def is_provisional(self) -> bool:
        """True while any method is blocked on unverified inputs."""
        return bool(self.blocked)

    def summary(self) -> str:
        lo, hi = self.band
        head = (
            f"India international market {TARGET_YEAR}: {lo:.0f}M to {hi:.0f}M passengers "
            f"(base {self.base_m:.1f}M in {BASE_YEAR})"
        )
        if self.is_provisional:
            missing = ", ".join(e.method for e in self.blocked)
            head += (
                f"\nPROVISIONAL: {len(self.available)} of {len(self.estimates)} methods. "
                f"Blocked: {missing}"
            )
        return head


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _annual_international() -> pd.Series:
    """DGCA international sector passengers per year, all carriers."""
    return load_dgca_intl_country().groupby("year")["pax_total"].sum().sort_index()


def _cagr(series: pd.Series, start: int, end: int) -> float:
    if start not in series.index or end not in series.index:
        raise KeyError(f"series lacks {start} or {end}")
    return (series[end] / series[start]) ** (1 / (end - start)) - 1


# --------------------------------------------------------------------------
# method 1: trend
# --------------------------------------------------------------------------


def estimate_trend(target_year: int = TARGET_YEAR) -> Estimate:
    """Extrapolate DGCA's own international history.

    Two growth rates are fitted, one pre-covid and one on the recovery, and the
    slower is used. The recovery rate is inflated by rebound off a suppressed
    base, so carrying it to 2030 would be extrapolating a bounce as a trend.
    """
    series = _annual_international()
    pre = _cagr(series, *PRE_COVID)
    post = _cagr(series, *POST_COVID)
    rate = min(pre, post)

    base = series[BASE_YEAR]
    value = base * (1 + rate) ** (target_year - BASE_YEAR)
    return Estimate(
        method="Trend",
        value_m=float(value) / 1e6,
        assumptions={
            "pre_covid_cagr": round(pre, 4),
            "post_covid_cagr": round(post, 4),
            "rate_used": round(rate, 4),
            "rationale": "slower of the two; the recovery rate is a rebound off a suppressed base",
        },
    )


# --------------------------------------------------------------------------
# method 2: propensity
# --------------------------------------------------------------------------


def _propensity_curve() -> tuple[float, float, int]:
    """Fit log(air trips per capita) against log(GDP per capita) across peers.

    Returns slope, intercept, observation count. The slope is the income
    elasticity of air travel: per cent more flying per per cent more income.
    """
    wb = load_worldbank_macro()
    wide = (
        wb[wb["iso3"].isin(PEERS)]
        .pivot_table(index=["iso3", "year"], columns="indicator", values="value")
        .dropna(subset=["IS.AIR.PSGR", "SP.POP.TOTL", "NY.GDP.PCAP.CD"])
    )
    wide = wide[(wide["IS.AIR.PSGR"] > 0) & (wide["NY.GDP.PCAP.CD"] > 0)]

    trips_pc = wide["IS.AIR.PSGR"] / wide["SP.POP.TOTL"]
    x = np.log(wide["NY.GDP.PCAP.CD"].to_numpy(dtype=float))
    y = np.log(trips_pc.to_numpy(dtype=float))
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept), int(len(x))


def _project(series: pd.Series, target_year: int, lookback: int = 10) -> tuple[float, float]:
    """Compound a series forward at its own trailing CAGR. Returns (value, rate)."""
    last = int(series.index.max())
    rate = (series[last] / series[last - lookback]) ** (1 / lookback) - 1
    return float(series[last] * (1 + rate) ** (target_year - last)), float(rate)


def estimate_propensity(target_year: int = TARGET_YEAR) -> Estimate:
    """Where India's flying lands at its 2030 income, judged against peers.

    Touches no DGCA traffic series, which is what makes it a real second opinion
    rather than the first one rearranged.

    Two bridges are needed and both are stated rather than buried. The World Bank
    indicator counts passengers carried by Indian-registered carriers, domestic
    and international together. So the result is scaled by the international
    share of Indian carrier traffic, then divided by the Indian carrier share of
    India's international market, because foreign carriers fly most of the rest.
    """
    slope, intercept, n = _propensity_curve()

    wb = load_worldbank_macro()
    ind = wb[wb["iso3"] == "IND"].pivot_table(index="year", columns="indicator", values="value")
    gdp_2030, gdp_cagr = _project(ind["NY.GDP.PCAP.CD"].dropna(), target_year)
    pop_2030, _ = _project(ind["SP.POP.TOTL"].dropna(), target_year)

    trips_pc_2030 = float(np.exp(intercept + slope * np.log(gdp_2030)))
    total_trips = trips_pc_2030 * pop_2030

    dom = load_dgca_domestic_carrier()
    recent = dom[dom["year"] == 2025]
    dom_pax = recent.loc[recent["service_type"] == "ScheduledDomestic", "pax"].sum()
    intl_pax = recent.loc[recent["service_type"] == "ScheduledInternational", "pax"].sum()
    intl_share = float(intl_pax / (dom_pax + intl_pax))

    from .benchmarking import who_carries_india

    indian_carrier_share = float(
        who_carries_india().set_index("carrier_group").loc["Indian", "share_pct"] / 100
    )

    value = total_trips * intl_share / indian_carrier_share
    return Estimate(
        method="Propensity",
        value_m=value / 1e6,
        assumptions={
            "income_elasticity": round(slope, 3),
            "peer_observations": n,
            "india_gdp_pc_cagr": round(gdp_cagr, 4),
            "gdp_pc_2030_usd": round(gdp_2030),
            "trips_per_capita_2030": round(trips_pc_2030, 3),
            "intl_share_of_indian_carrier_traffic": round(intl_share, 4),
            "indian_carrier_share_of_india_intl": round(indian_carrier_share, 4),
        },
    )


# --------------------------------------------------------------------------
# method 3: capacity
# --------------------------------------------------------------------------


# The order book by variant, so seats are fleet-weighted rather than one type
# applied to every tail. Counting all 140 wide-bodies at A350-900 seating
# understates the book by about 5 percent, because the A350-1000 and the 777-9
# are materially larger aircraft.
#
# The counts are the composition recorded in the `air_india_widebody_on_order`
# and `indigo_a350_on_order` rows of assumptions.csv, both CORRECTED_VERIFIED
# against primary Airbus, Boeing and Air India releases. Read those notes for the
# sources; they are not restated here, so there is one copy to keep right.
#
# `variant_assumed` marks the two entries where the operator announced a type but
# not a variant. Both are assumed to be the SMALLER variant, so the error runs
# against our own argument rather than for it, and both are surfaced on the chart
# face rather than buried here.
_ORDER_BOOK = (
    # operator,     variant,     count, seat_key,                   variant_assumed
    ("IndiGo",      "A350-900",     60, "widebody_seats_a350_900",  False),
    ("Air India",   "A350-1000",    34, "widebody_seats_a350_1000", False),
    ("Air India",   "A350-900",      6, "widebody_seats_a350_900",  False),
    ("Air India",   "A350-900",     10, "widebody_seats_a350_900",  True),
    ("Air India",   "787-9",        20, "widebody_seats_b787_9",    True),
    ("Air India",   "777-9",        10, "widebody_seats_b777_9",    False),
)


def _widebody_seats() -> tuple[float, dict]:
    """Total seats on firm order, weighted by variant.

    Raises the same exceptions as `assumption` so the caller's gate still works.
    """
    total = 0.0
    by_variant: dict[str, float] = {}
    for _operator, variant, count, seat_key, _assumed in _ORDER_BOOK:
        seats = count * assumption(seat_key)
        total += seats
        by_variant[variant] = by_variant.get(variant, 0.0) + seats
    return total, by_variant


def estimate_capacity(target_year: int = TARGET_YEAR) -> Estimate:
    """Count the seats the announced order books can actually fly.

    Gated on the fleet, seat and utilisation figures. The gate held for most of
    this project's life and that was correct: the method would otherwise have
    emitted a confident number built on figures nobody had checked.

    Utilisation enters on an **owned-fleet** basis (10.06 hours/aircraft/day,
    IndiGo block hours over aircraft at period end, cross-checked against DGCA to
    0.31 percent). An active-fleet basis would be roughly 13 and would lift this
    leg by about a third, which is why the basis is named here and on the chart
    rather than left to the reader.
    """
    needed = (
        "air_india_widebody_on_order",
        "indigo_a350_on_order",
        "aircraft_utilisation_hours_per_day",
    )
    try:
        values = {k: assumption(k) for k in needed}
        seats, seats_by_variant = _widebody_seats()
    except (UnverifiedAssumption, KeyError) as exc:
        return Estimate(method="Capacity", value_m=None, blocked_reason=str(exc))

    # The variant table and the headline order-book rows are maintained
    # separately, so they must be reconciled or the mix can silently drift out of
    # step with a corrected order count.
    booked = values["air_india_widebody_on_order"] + values["indigo_a350_on_order"]
    in_table = sum(row[2] for row in _ORDER_BOOK)
    if in_table != booked:
        return Estimate(
            method="Capacity",
            value_m=None,
            blocked_reason=(
                f"order book mismatch: variant table holds {in_table:.0f} aircraft, "
                f"assumptions.csv holds {booked:.0f}. Update _ORDER_BOOK."
            ),
        )

    dom = load_dgca_domestic_carrier()
    recent = dom[(dom["year"] == 2025) & (dom["service_type"] == "ScheduledInternational")]
    load_factor = float(recent["rpk"].sum() / recent["ask"].sum())

    block_hours = 7.5
    cycles = values["aircraft_utilisation_hours_per_day"] * 365 / block_hours
    added = seats * cycles * load_factor

    base = float(_annual_international()[BASE_YEAR])
    return Estimate(
        method="Capacity",
        value_m=(base + added) / 1e6,
        assumptions={
            **values,
            "widebody_seats_total": round(seats),
            "widebody_seats_by_variant": {k: round(v) for k, v in seats_by_variant.items()},
            "mean_seats_per_widebody": round(seats / in_table, 1),
            "utilisation_basis": "owned fleet",
            "variants_assumed": [
                f"{row[2]:.0f}x {row[1]} ({row[0]})" for row in _ORDER_BOOK if row[4]
            ],
            "observed_intl_load_factor": round(load_factor, 4),
            "assumed_block_hours": block_hours,
        },
    )


# --------------------------------------------------------------------------
# triangulation
# --------------------------------------------------------------------------


def triangulate(target_year: int = TARGET_YEAR) -> Triangulation:
    return Triangulation(
        estimates=[
            estimate_trend(target_year),
            estimate_propensity(target_year),
            estimate_capacity(target_year),
        ],
        base_m=float(_annual_international()[BASE_YEAR]) / 1e6,
    )


def fig_triangulation(target_year: int = TARGET_YEAR) -> go.Figure:
    tri = triangulate(target_year)
    lo, hi = tri.band
    fig = charts.triangulation(
        {e.method: e.value_m for e in tri.available}, band=(lo, hi), value_fmt=",.0f"
    )

    subtitle = (
        f"Millions of international sector passengers in {target_year}, against "
        f"{tri.base_m:.1f}M in {BASE_YEAR}. The band is reported, never the average"
    )
    if tri.is_provisional:
        subtitle += (
            f". {len(tri.blocked)} of {len(tri.estimates)} methods withheld pending "
            "source verification"
        )

    # The capacity leg is the one that carries stated assumptions, and it is also
    # the leg that sets the bottom of the band, so the assumptions belong on the
    # chart face. Read them off the estimate rather than retyping them, or the
    # caption drifts from the model the first time a variant changes.
    cap = next((e for e in tri.available if e.method == "Capacity"), None)
    if cap is not None:
        assumed = cap.assumptions.get("variants_assumed") or []
        subtitle += (
            f". Capacity leg counts {cap.assumptions['widebody_seats_total']:,} seats on firm "
            f"order at published two-class layouts, flown at "
            f"{cap.assumptions['aircraft_utilisation_hours_per_day']} hours per aircraft per day "
            f"({cap.assumptions['utilisation_basis']} basis; an active-fleet basis would be "
            "materially higher)"
        )
        if assumed:
            subtitle += f". Variant assumed for {' and '.join(assumed)}"

    # The title deliberately does NOT say "independent methods". Trend and
    # propensity share two DGCA bridging ratios, so that word would claim more
    # than the model earns. State the range, let the methodology page explain
    # what the methods do and do not share.
    title = (
        f"India's international market reaches {lo:.0f}M to {hi:.0f}M passengers by "
        f"{target_year}, up from {tri.base_m:.0f}M"
    )
    return charts.finish(fig, title=title, subtitle=subtitle, source=SOURCE)


# Published under the same contract as every other analysis module. This was a
# bare call inside build_all, which meant the chart existed but was invisible to
# anything enumerating what the repo publishes, including the house-rule fixture
# in the test suite.
FIGURES = {
    "market_sizing": fig_triangulation,
}


def build_all() -> list[str]:
    written = []
    for name, builder in FIGURES.items():
        charts.export(builder(), name)
        written.append(name)
    return written


if __name__ == "__main__":
    _tri = triangulate()
    print(_tri.summary())
    print()
    for _e in _tri.estimates:
        if _e.available:
            print(f"  {_e.method:<12} {_e.value_m:>8.1f}M")
            for _k, _v in _e.assumptions.items():
                print(f"      {_k}: {_v}")
        else:
            print(f"  {_e.method:<12}   BLOCKED")
            print(f"      {_e.blocked_reason}")
        print()
    for _name in build_all():
        print("wrote", _name)
