"""What the order book can actually fly, against what the 2030 market needs.

The sizing modules answer "how big does the market get". This one answers the
decision question sitting behind it: **the firm order book is a fixed quantity of
capacity, so what has to be true for it to be absorbed?**

Capacity is measured in **available seat kilometres**, not seats or aircraft, and
that choice carries the whole module. A seat is not a unit of capacity until you
say how far and how often it flies, and this case turns entirely on how far. Two
carriers with identical fleets and identical load factors produce completely
different ASK if one flies Dubai and the other flies New York, which is the
observed IndiGo against Air India gap restated. ASK is also the denominator of
CASK and RASK, so the capacity side of this model and the unit-economics side of
`scenario.py` are denominated in the same thing.

**Everything on the supply side is computed from DGCA, including two figures
that would normally be assumed.** Block speed is `aircraft_km / aircraft_hours`,
and seats per departure is `ask / aircraft_km`. Both columns are published, so
neither enters as a judgement:

    Air India international 2025      698 km/h block speed, 254 seats/departure
    IndiGo international 2025         656 km/h block speed, 207 seats/departure

The difference between those two block speeds is not noise. Taxi, climb and
descent are a larger share of a short sector, so a 2,643 km network genuinely
blocks slower than a 5,316 km one. The data reproducing a known physical
relationship is a reason to trust the columns.

**What is modelled, and it is one thing:** the delivery schedule. The Airbus
release that confirms IndiGo's 60 firm A350s does not state when deliveries
begin, and one attempt to source it found nothing, so a start year is **not
asserted anywhere in this module**. It appears only as a scenario axis on the
year-path figure, and the headline figure does not need it at all.

**The finding.** At today's network shape the order book is roughly twice the
capacity needed to hold share. It only clears if the average sector lengthens by
about a quarter, or if Indian carriers take share well beyond parity, or some
combination. That is the recommendation restated in capacity terms: these
aircraft are not bought to carry more of the same traffic, they are bought to
carry it further.

**This is not a contradiction of hypothesis tree branch 4.2**, which reports that
the order book does not overshoot demand, and the two are worth reading together
because they look opposed and are not. They divide by different denominators:

    4.2, the capacity sizing leg   book against the growth of the WHOLE India
                                   international market, all carriers. 90.7M
                                   against a trend case of 108M, so it does not
                                   overshoot
    here                           book against the growth of INDIAN CARRIER
                                   capacity at constant share. Indian carriers
                                   are 45.9% of the market, so they need only
                                   their share of that growth, and the same book
                                   goes almost twice as far against it

Both are true and neither is the interesting one on its own. The interesting
statement is the pair: the aircraft are not enough to serve the whole market's
growth, and they are more than enough to serve one carrier group's share of it
at today's sector length. What sits between those two facts is the share
recapture the recommendation argues for.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import charts
from .benchmarking import LATEST_COMPLETE_YEAR, who_carries_india
from .data_pipeline import load_dgca_domestic_carrier
from .market_sizing import BASE_YEAR, TARGET_YEAR, _annual_international, _widebody_seats
from .scenario import scenario_paths, scenarios

# The long-haul block speed proxy. Air India's international operation IS a
# wide-body long-haul operation, so its observed block speed is the right figure
# for wide-body seats, and it is measured rather than assumed. Using IndiGo's
# 656 km/h would price the new aircraft at short-haul productivity, which is the
# exact error the case exists to argue against.
WIDEBODY_SPEED_PROXY = "Air India"

# Carriers too small to characterise a network. Below this they are charter-like
# tails whose stage length and block speed swing on a handful of sectors.
MIN_PAX_TO_CHARACTERISE = 500_000

SOURCE = (
    "Capacity, stage length and block speed computed from DGCA carrier operating "
    "statistics via github.com/Vonter/india-aviation-traffic (ODbL). Order book and "
    "seat counts from Airbus, Boeing and Air India primary releases, verified in "
    "data/manual/assumptions.csv"
)


@dataclass(frozen=True)
class Baseline:
    """What Indian carriers fly internationally today, all of it measured."""

    year: int
    pax: float
    ask: float
    stage_km: float
    load_factor: float
    widebody_block_speed_kmh: float

    @property
    def pax_m(self) -> float:
        return self.pax / 1e6

    @property
    def ask_bn(self) -> float:
        return self.ask / 1e9


def _international_operating(year: int) -> pd.DataFrame:
    """Per-carrier international operating statistics for one year.

    Indian carriers only. Foreign carriers file no operating statistics with
    DGCA, so their block speed and stage length are not knowable from this
    source and are not guessed.
    """
    df = load_dgca_domestic_carrier()
    df = df[(df["service_type"] == "ScheduledInternational") & (df["year"] == year)]
    out = df.groupby("airline", as_index=False).agg(
        pax=("pax", "sum"),
        rpk=("rpk", "sum"),
        ask=("ask", "sum"),
        aircraft_km=("aircraft_km", "sum"),
        aircraft_hours=("aircraft_hours", "sum"),
    )
    out = out[out["pax"] > MIN_PAX_TO_CHARACTERISE].copy()
    out["stage_km"] = out["rpk"] / out["pax"]
    out["block_speed_kmh"] = out["aircraft_km"] / out["aircraft_hours"]
    out["seats_per_departure"] = out["ask"] / out["aircraft_km"]
    out["load_factor"] = out["rpk"] / out["ask"]
    return out.sort_values("pax", ascending=False).reset_index(drop=True)


def baseline(year: int = LATEST_COMPLETE_YEAR) -> Baseline:
    """Today's installed international capacity, entirely from DGCA."""
    ops = _international_operating(year)
    proxy = ops.loc[ops["airline"] == WIDEBODY_SPEED_PROXY]
    if proxy.empty:
        raise KeyError(f"{WIDEBODY_SPEED_PROXY!r} has no international rows in {year}")

    pax = float(ops["pax"].sum())
    ask = float(ops["ask"].sum())
    rpk = float(ops["rpk"].sum())
    return Baseline(
        year=year,
        pax=pax,
        ask=ask,
        stage_km=rpk / pax,
        load_factor=rpk / ask,
        widebody_block_speed_kmh=float(proxy["block_speed_kmh"].iloc[0]),
    )


# --------------------------------------------------------------------------
# supply: what the firm order book can fly
# --------------------------------------------------------------------------


def order_book_ask(
    utilisation_hours_per_day: float | None = None, *, year: int = LATEST_COMPLETE_YEAR
) -> dict:
    """Annual ASK the firm wide-body order book can produce once delivered.

        ASK = seats x block speed x utilisation hours per day x 365

    Seats come from `market_sizing._widebody_seats`, which weights by variant and
    is gated on the same verified rows as the capacity sizing leg. Sharing that
    function rather than re-deriving seats here is deliberate: a second seat
    total would drift from the published band the first time a variant changed.

    **This is the same quantity the capacity sizing leg computes**, arrived at
    from the other direction, and a test pins the two together. `estimate_capacity`
    multiplies seats by cycles per year; cycles times sector length is kilometres,
    so both roads end at the same ASK. What that equivalence exposes is worth
    stating: the 7.5 block hours per cycle hardcoded in the sizing leg implies a
    sector of roughly 5,235 km at this block speed. The capacity leg has always
    assumed the wide-bodies fly long-haul. It just never said so.

    **Treated as net additional capacity, which overstates it.** Some of the book
    replaces retiring aircraft already inside the baseline. No public retirement
    schedule exists for either carrier, so the overstatement cannot be quantified,
    and its direction is stated instead: the absorption requirement below is a
    floor, not a ceiling.
    """
    from .data_pipeline import assumption

    if utilisation_hours_per_day is None:
        utilisation_hours_per_day = assumption("aircraft_utilisation_hours_per_day")

    seats, by_variant = _widebody_seats()
    speed = baseline(year).widebody_block_speed_kmh
    ask = seats * speed * utilisation_hours_per_day * 365
    return {
        "seats": seats,
        "seats_by_variant": {k: round(v) for k, v in by_variant.items()},
        "block_speed_kmh": speed,
        "utilisation_hours_per_day": utilisation_hours_per_day,
        "implied_sector_km": speed * 7.5,
        "ask": ask,
        "ask_bn": ask / 1e9,
    }


# --------------------------------------------------------------------------
# demand: the ASK the market asks for
# --------------------------------------------------------------------------


def ask_required(pax: float, stage_km: float, load_factor: float) -> float:
    """The capacity identity. ASK = passengers x sector length / load factor.

    No modelling in here at all, which is why it is its own function: every
    scenario below is this identity evaluated at different inputs.
    """
    return pax * stage_km / load_factor


def indian_carrier_pax(total_intl_pax: float, share: float) -> float:
    return total_intl_pax * share


def current_share(year: int = LATEST_COMPLETE_YEAR) -> float:
    """Indian carriers' share of India's international sector passengers."""
    return float(who_carries_india(year).set_index("carrier_group").loc["Indian", "share_pct"]) / 100


def _calibration(year: int = LATEST_COMPLETE_YEAR) -> float:
    """Reconcile the smooth demand path to what Indian carriers actually flew.

    The scenario paths compound from a 2024 base at a fitted CAGR, so their 2025
    value is where the curve says the market should have been, not where it was.
    Multiplying that by the carrier share lands about 2.6% below the observed
    36.4M. Small, but it would put the model's first year below today's measured
    capacity and make the fleet look surplus before a single aircraft arrived.

    So the path is scaled by a single constant that pins it to the observed
    baseline year. One number, applied to every year and every scenario alike, so
    it shifts the level and touches no growth rate. The alternative, compounding
    the observed baseline forward directly, gives the same answer; this way the
    market total and the carrier total stay driven by one published path.
    """
    base = baseline(year)
    modelled = _scenario_total(year, "Base") * current_share(year)
    return base.pax / modelled


def indian_carrier_pax_path(
    target_year: int = TARGET_YEAR,
    *,
    scenario_name: str = "Base",
    share: float | None = None,
) -> pd.DataFrame:
    """Indian carrier international passengers by year, calibrated to the baseline.

    `share` defaults to today's, which is the "hold share, gain nothing" case and
    the right default: it is the least flattering assumption the case can make.
    """
    base = baseline()
    share = current_share() if share is None else share
    factor = _calibration()

    paths = scenario_paths(target_year)
    path = paths[(paths["scenario"] == scenario_name) & (paths["year"] >= base.year)]
    if path.empty:
        raise KeyError(f"no scenario named {scenario_name!r}")

    out = path[["year"]].copy().reset_index(drop=True)
    out["scenario"] = scenario_name
    out["total_intl_pax_m"] = path["pax_m"].to_numpy()
    out["pax"] = path["pax_m"].to_numpy() * 1e6 * share * factor
    out["pax_m"] = out["pax"] / 1e6
    return out


# --------------------------------------------------------------------------
# the absorption frontier
# --------------------------------------------------------------------------


def absorption_frontier(
    target_year: int = TARGET_YEAR,
    *,
    scenario_name: str = "Base",
    shares: tuple[float, ...] = (0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70),
) -> pd.DataFrame:
    """Which (share, sector length) pairs exactly absorb the order book.

    The question this answers is the decision one. The book is a fixed quantity
    of ASK. Indian carriers can absorb it by carrying a larger share of the
    market, by flying the traffic further, or by some mix, and this returns the
    locus of combinations where the arithmetic closes.

    Read it as a constraint, not a forecast. Any point below the curve leaves the
    order book underemployed; any point above it needs capacity nobody has ordered.
    """
    base = baseline()
    book = order_book_ask()
    total = _scenario_total(target_year, scenario_name) * _calibration()

    available_ask = base.ask + book["ask"]
    rows = []
    for share in shares:
        pax = indian_carrier_pax(total, share)
        rows.append(
            {
                "share": share,
                "share_pct": 100 * share,
                "pax_m": pax / 1e6,
                # invert the identity: given pax and the ASK on hand, how far must
                # the average sector be for the capacity to be exactly used?
                "required_stage_km": available_ask * base.load_factor / pax,
            }
        )
    df = pd.DataFrame(rows)
    df["stage_uplift_pct"] = 100 * (df["required_stage_km"] / base.stage_km - 1)
    return df


def _scenario_total(target_year: int, scenario_name: str) -> float:
    """India international sector passengers in the target year, one scenario."""
    match = [s for s in scenarios() if s.name == scenario_name]
    if not match:
        raise KeyError(f"no scenario named {scenario_name!r}")
    base_value = float(_annual_international()[BASE_YEAR])
    return match[0].project(base_value, BASE_YEAR, target_year)


def absorption_summary(target_year: int = TARGET_YEAR, *, scenario_name: str = "Base") -> dict:
    """The headline: what holding share alone would require, and what it leaves over.

    Reported as the two pure cases plus the shortfall between them, because the
    honest answer is that neither lever alone is plausible and the recommendation
    is a mix.
    """
    base = baseline()
    book = order_book_ask()
    total = _scenario_total(target_year, scenario_name) * _calibration()
    share_now = current_share()

    pax_hold = indian_carrier_pax(total, share_now)
    ask_hold = ask_required(pax_hold, base.stage_km, base.load_factor)
    ask_available = base.ask + book["ask"]

    return {
        "scenario": scenario_name,
        "target_year": target_year,
        "total_intl_pax_m": total / 1e6,
        "share_held_pct": 100 * share_now,
        # holding share at today's network shape
        "pax_holding_share_m": pax_hold / 1e6,
        "ask_needed_holding_share_bn": ask_hold / 1e9,
        "ask_available_bn": ask_available / 1e9,
        "surplus_bn": (ask_available - ask_hold) / 1e9,
        "book_vs_growth_ratio": book["ask"] / (ask_hold - base.ask),
        # the two pure levers
        "stage_km_to_absorb": ask_available * base.load_factor / pax_hold,
        "stage_uplift_pct": 100 * (ask_available * base.load_factor / pax_hold / base.stage_km - 1),
        "share_pct_to_absorb": 100
        * (ask_available * base.load_factor / base.stage_km)
        / total,
    }


# --------------------------------------------------------------------------
# the gap by year
# --------------------------------------------------------------------------


def gap_path(
    *,
    scenario_name: str = "Base",
    first_delivery_year: int = 2027,
    ramp_years: int = 6,
    target_year: int = TARGET_YEAR,
    stage_km: float | None = None,
) -> pd.DataFrame:
    """ASK needed against ASK delivered, year by year.

    `first_delivery_year` is a SCENARIO INPUT, not a sourced fact. The Airbus
    release confirming the 60 firm A350s states no delivery timing and one
    attempt to source it found none, so this module never asserts a start year.
    `gap_band` runs the plausible ones and reports the spread.

    Deliveries are spread linearly across `ramp_years`. A real curve is
    S-shaped, but nobody publishes this one, and a linear ramp is the shape that
    claims least.
    """
    base = baseline()
    book = order_book_ask()
    stage = base.stage_km if stage_km is None else stage_km

    path = indian_carrier_pax_path(target_year, scenario_name=scenario_name)

    rows = []
    for year, pax in zip(path["year"], path["pax"]):
        delivered_fraction = np.clip((year - first_delivery_year + 1) / ramp_years, 0.0, 1.0)
        delivered_ask = book["ask"] * float(delivered_fraction)
        needed = ask_required(pax, stage, base.load_factor)
        rows.append(
            {
                "year": int(year),
                "scenario": scenario_name,
                "first_delivery_year": first_delivery_year,
                "pax_m": pax / 1e6,
                "ask_needed_bn": needed / 1e9,
                "ask_available_bn": (base.ask + delivered_ask) / 1e9,
                "delivered_pct": 100 * float(delivered_fraction),
                "gap_bn": (needed - base.ask - delivered_ask) / 1e9,
            }
        )
    return pd.DataFrame(rows)


def gap_band(
    *,
    scenario_name: str = "Base",
    start_years: tuple[int, ...] = (2027, 2028, 2029),
    **kwargs,
) -> pd.DataFrame:
    """The gap path under each plausible delivery start. The spread is the output."""
    return pd.concat(
        [gap_path(scenario_name=scenario_name, first_delivery_year=y, **kwargs) for y in start_years],
        ignore_index=True,
    )


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------


def fig_absorption_frontier(target_year: int = TARGET_YEAR) -> go.Figure:
    df = absorption_frontier(target_year)
    base = baseline()
    summary = absorption_summary(target_year)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["share_pct"],
            y=df["required_stage_km"],
            mode="lines",
            name="Absorbs the order book",
            line=dict(color=charts.RED, width=3),
            hovertemplate="Share %{x:.0f}%<br>needs %{y:,.0f} km average sector<extra></extra>",
        )
    )

    # Where Indian carriers actually are today. The distance between this marker
    # and the curve is the entire decision.
    fig.add_trace(
        go.Scatter(
            x=[100 * current_share()],
            y=[base.stage_km],
            mode="markers+text",
            marker=dict(size=13, color=charts.INK, symbol="circle"),
            text=[f"  Today: {100 * current_share():.0f}% share, {base.stage_km:,.0f} km"],
            textposition="middle right",
            textfont=dict(size=12, color=charts.INK),
            hovertemplate="Today<extra></extra>",
            showlegend=False,
        )
    )

    fig.add_annotation(
        x=df["share_pct"].iloc[len(df) // 2],
        y=df["required_stage_km"].iloc[len(df) // 2],
        text="<b>underemployed below</b><br>the line",
        showarrow=False,
        yshift=-46,
        font=dict(size=11, color=charts.GREY),
    )

    fig.update_layout(showlegend=False)
    fig.update_xaxes(title_text="Indian carrier share of India's international market (%)", ticksuffix="%")
    fig.update_yaxes(title_text="Average sector needed (km)")

    return charts.finish(
        fig,
        modeled=True,
        title=(
            f"The order book clears only if the average sector lengthens about "
            f"{summary['stage_uplift_pct']:.0f}%, or share passes "
            f"{summary['share_pct_to_absorb']:.0f}%"
        ),
        subtitle=(
            f"Combinations that exactly absorb {summary['ask_available_bn'] - base.ask_bn:.0f}bn ASK of "
            f"firm wide-body order on top of today's {base.ask_bn:.0f}bn, against a "
            f"{summary['total_intl_pax_m']:.0f}M passenger market in {target_year}. Block speed and "
            "sector length are computed from DGCA; the book is treated as net additional capacity, "
            "which overstates it, so the requirement shown is a floor"
        ),
        source=SOURCE,
    )


def fig_fleet_gap(target_year: int = TARGET_YEAR) -> go.Figure:
    band = gap_band(target_year=target_year)
    base = baseline()

    fig = go.Figure()

    # Demand is identical across the three delivery cases, so it is drawn once.
    needed = band[band["first_delivery_year"] == band["first_delivery_year"].min()]
    fig.add_trace(
        go.Scatter(
            x=needed["year"],
            y=needed["ask_needed_bn"],
            mode="lines",
            name="Capacity the market asks for",
            line=dict(color=charts.INK, width=2.5),
            hovertemplate="%{x}: needs %{y:,.0f}bn ASK<extra></extra>",
        )
    )

    greys = [charts.MUTED[0], charts.MUTED[1], charts.MUTED[2]]
    for colour, (start, grp) in zip(greys, band.groupby("first_delivery_year")):
        fig.add_trace(
            go.Scatter(
                x=grp["year"],
                y=grp["ask_available_bn"],
                mode="lines",
                name=f"Deliveries from {start}",
                line=dict(color=colour, width=2, dash="dash"),
                hovertemplate=f"from {start}" + " %{x}: %{y:,.0f}bn available<extra></extra>",
            )
        )

    # The one red element: the surplus the book leaves at the target year, which
    # is the finding. Drawn as a bracket between the two curves at the right edge.
    last = band[band["year"] == target_year]
    top = float(last["ask_available_bn"].max())
    bottom = float(last["ask_needed_bn"].iloc[0])
    fig.add_shape(
        type="line",
        x0=target_year,
        x1=target_year,
        y0=bottom,
        y1=top,
        line=dict(color=charts.RED, width=3),
    )
    fig.add_annotation(
        x=target_year,
        y=(top + bottom) / 2,
        text=f"<b>{top - bottom:,.0f}bn ASK<br>spare at today's<br>sector length</b>",
        xanchor="right",
        xshift=-10,
        showarrow=False,
        font=dict(size=12, color=charts.RED),
    )

    fig.update_layout(showlegend=True)
    fig.update_xaxes(title_text="", dtick=1)
    fig.update_yaxes(title_text="Available seat kilometres (bn)")

    return charts.finish(
        fig,
        modeled=True,
        title=(
            "Delivery timing changes when the capacity lands, not whether it is more "
            "than holding share requires"
        ),
        subtitle=(
            f"Indian carrier international ASK, base demand case, share held at "
            f"{100 * current_share():.0f}% and sector length held at today's "
            f"{base.stage_km:,.0f} km. Delivery start is a scenario input, never asserted: the "
            "Airbus release confirming the 60 firm A350s states no schedule. Linear ramp over "
            "six years"
        ),
        source=SOURCE,
    )


FIGURES = {
    "absorption_frontier": fig_absorption_frontier,
    "fleet_gap": fig_fleet_gap,
}


def build_all() -> list[str]:
    written = []
    for name, builder in FIGURES.items():
        charts.export(builder(), name)
        written.append(name)
    return written


if __name__ == "__main__":
    _b = baseline()
    print(f"baseline {_b.year}: {_b.pax_m:.1f}M pax, {_b.ask_bn:.1f}bn ASK, "
          f"{_b.stage_km:,.0f} km sector, LF {_b.load_factor:.1%}, "
          f"wide-body block speed {_b.widebody_block_speed_kmh:.0f} km/h")
    print()
    print(_international_operating(_b.year).round(1).to_string(index=False))
    print()
    _book = order_book_ask()
    print(f"order book: {_book['seats']:,.0f} seats -> {_book['ask_bn']:.1f}bn ASK "
          f"at {_book['block_speed_kmh']:.0f} km/h and "
          f"{_book['utilisation_hours_per_day']} h/day")
    print(f"  implied sector in the sizing leg: {_book['implied_sector_km']:,.0f} km")
    print(f"  by variant: {_book['seats_by_variant']}")
    print()
    for _k, _v in absorption_summary().items():
        print(f"  {_k}: {_v if isinstance(_v, str) else round(_v, 2)}")
    print()
    print(absorption_frontier().round(1).to_string(index=False))
    print()
    print(gap_band().round(1).to_string(index=False))
    print()
    for _n in build_all():
        print("wrote", _n)
