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


def estimate_capacity(target_year: int = TARGET_YEAR) -> Estimate:
    """Count the seats the announced order books can actually fly.

    Blocked until the fleet and utilisation figures are verified. That is the
    gate doing its job: this method would otherwise emit a confident number built
    on four figures nobody has checked.
    """
    needed = (
        "air_india_widebody_on_order",
        "indigo_a350_on_order",
        "widebody_seats_a350_900",
        "aircraft_utilisation_hours_per_day",
    )
    try:
        values = {k: assumption(k) for k in needed}
    except (UnverifiedAssumption, KeyError) as exc:
        return Estimate(method="Capacity", value_m=None, blocked_reason=str(exc))

    seats = (values["air_india_widebody_on_order"] + values["indigo_a350_on_order"]) * values[
        "widebody_seats_a350_900"
    ]

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

    count = len(tri.available)
    title = (
        f"{'Two' if count == 2 else count} independent methods put India's {target_year} "
        f"international market between {lo:.0f}M and {hi:.0f}M passengers"
    )
    return charts.finish(fig, title=title, subtitle=subtitle, source=SOURCE)


def build_all() -> list[str]:
    charts.export(fig_triangulation(), "market_sizing")
    return ["market_sizing"]


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
