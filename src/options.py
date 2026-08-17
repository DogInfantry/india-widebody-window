"""Which way to add long-haul capacity, and what each option needs to be true.

`fleet_gap.py` establishes that the order book is sized for a longer network than
Indian carriers fly today. This module asks the next question, which is the
decision one: **of the ways to close that, which clear their own cost, and what
would have to hold for each?**

**Deliberately not a discounted cash flow.** A ten year NPV per option needs a
discount rate, an aircraft capital cost, a residual value and a yield by corridor.
Not one of those can be verified against a primary source here: Air India is
unlisted, DGCA publishes no fares, and aircraft transaction prices are
commercially confidential. Four unverifiable inputs stacked into one number
produces a figure that looks precise and cannot be checked, on a site whose whole
claim is that its numbers can be. The breakeven below asks the same question from
the other end, using published unit costs, and leaves the unknown where a reader
can apply their own judgement to it.

**The one modelling knob** is `cask_stage_length_elasticity`. Unit cost falls as
sectors lengthen, because per-departure costs are amortised over more available
seat kilometres. The shape is not in doubt; the exponent is, and it cannot be
fitted from anything here because IndiGo is the only Indian carrier that publishes
CASK at all, and one point fits no curve. `sensitivity()` turns it and a test
asserts the finding survives.

**Why headroom rather than a straight breakeven comparison.** The obvious exhibit
is breakeven yield per corridor against IndiGo's achieved 5.06 INR per RPK. It is
also wrong, in a way this repo has already been caught by once: yield per RPK
*falls* with stage length, so holding it flat across an 11,766 km sector flatters
long-haul, which is exactly the caveat `profit_pools` carries. Rather than model
the yield decline too, and add a second unverifiable knob, this reports the
**tolerance**: how far yield could fall from today's level before a corridor stops
covering its own cost. The unknown ends up on the reader's side of the line, as a
number to judge against, instead of buried in the model as an assumption.

**What it finds, and it cuts against the headline recommendation.** Gulf sectors
have the *least* cost headroom of any corridor, because they are short enough that
unit cost stays high. Long-haul has more. That does not overturn "Gulf first", but
it does mean the Gulf case rests on volume, bilateral position and the connect
premium rather than on unit economics, and the recommendation is stated that way
in `docs/recommendation.md` instead of implying the corridor is comfortable.

It is also a genuine corroboration. `profit_pools` reached the same ordering from
a completely different direction, modelling margin against stage length off an
EBITDAR anchor. This reaches it from published unit costs and a cost elasticity.
Two unrelated routes to the same shape.

**One sensitivity worth naming before a reader finds it.** The result moves
materially with the load factor chosen, and the choice is not arbitrary. Indian
carriers fly international sectors at **81.1%** and IndiGo's system runs at
**84.8%**, because domestic flies fuller. International is the right basis for
international corridors, and it is the one used throughout this repo, but it is
also the less flattering one: at the system load factor the Gulf comes out at
roughly breakeven instead of about four points under it. The ordering across
corridors does not change either way, and neither does the conclusion that the
Gulf is the tightest of them, which is what the recommendation actually turns on.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from . import charts
from .benchmarking import INTL_COUNTRY_YEAR, LATEST_COMPLETE_YEAR, corridor_scale
from .data_pipeline import assumption, load_dgca_domestic_carrier
from .fleet_gap import baseline
from .profit_pools import EXCLUDED_REGIONS, corridor_stage_lengths

# The carrier whose published unit cost anchors everything below. IndiGo is the
# only Indian carrier that publishes CASK, which is why it is the reference and
# not a choice.
REFERENCE_CARRIER = "IndiGo"

# The single modelling knob, and the number to attack first.
#
# Unit cost falls as sectors lengthen, because per-departure costs (ground
# handling, the turn, taxi fuel, the cycle-driven share of maintenance) are
# amortised over more available seat kilometres. The SHAPE is not in doubt. The
# exponent is, and it cannot be fitted from anything in this repo: IndiGo is the
# only Indian carrier that publishes CASK, which is one point, and one point fits
# no curve. Air India is unlisted and files nothing.
#
# -0.25 means doubling the sector cuts unit cost by about 16 per cent. It sits
# inside the range trade sources describe without matching any single one of
# them, so it is carried here as a judgement rather than dressed up with a
# citation it does not have.
#
# It lives here rather than in assumptions.csv on purpose, mirroring
# `profit_pools.MARGIN_STAGE_SENSITIVITY`. A modelled knob is not a hand-entered
# observation: there is no source to verify it against, so the gate has nothing
# to check and would only ever refuse it. Recording it in both places would put
# two copies of one number in the repo, which is the drift this project spends
# most of its effort avoiding. `sensitivity()` turns it and a test asserts the
# finding survives.
CASK_STAGE_ELASTICITY = -0.25

SOURCE = (
    "Unit costs and yields from IndiGo FY2026 and Emirates 2025-26 primary filings, verified "
    "in data/manual/assumptions.csv. Stage lengths are great circle from OurAirports (CC0); "
    "network averages and load factors computed from DGCA. Cost elasticity to stage length is "
    "modelled, see docs/methodology.md"
)


@dataclass(frozen=True)
class Reference:
    """The network that produced the published unit cost, measured from DGCA.

    CASK is a system figure, so the sector length it corresponds to has to be the
    system one, not the international one. Anchoring the cost curve at IndiGo's
    2,643 km international stage would price its domestic flying as though it
    were long-haul and shift every corridor's cost down with it.
    """

    carrier: str
    year: int
    stage_km: float
    load_factor: float
    cask: float
    yield_inr_per_rpk: float


def reference(year: int = LATEST_COMPLETE_YEAR) -> Reference:
    df = load_dgca_domestic_carrier()
    df = df[(df["airline"] == REFERENCE_CARRIER) & (df["year"] == year)]
    if df.empty:
        raise KeyError(f"no {REFERENCE_CARRIER} rows for {year}")
    pax, rpk, ask = df["pax"].sum(), df["rpk"].sum(), df["ask"].sum()
    return Reference(
        carrier=REFERENCE_CARRIER,
        year=year,
        stage_km=float(rpk / pax),
        load_factor=float(rpk / ask),
        cask=assumption("indigo_cask_inr_per_ask_fy2026"),
        yield_inr_per_rpk=assumption("indigo_yield_inr_per_rpk_fy2026"),
    )


# --------------------------------------------------------------------------
# the cost curve
# --------------------------------------------------------------------------


def cask_at_stage(stage_km: float, *, elasticity: float | None = None) -> float:
    """Unit cost at a given sector length, scaled off the published system figure.

        CASK(D) = CASK_ref x (D / D_ref) ^ elasticity

    A constant-elasticity form, because there is no evidence available to justify
    a richer shape and a richer shape would imply precision this has none of.
    """
    ref = reference()
    if elasticity is None:
        elasticity = CASK_STAGE_ELASTICITY
    return ref.cask * (stage_km / ref.stage_km) ** elasticity


def corridor_economics(
    year: int = INTL_COUNTRY_YEAR, *, elasticity: float | None = None
) -> pd.DataFrame:
    """Cost, breakeven yield and yield headroom for every corridor.

    `yield_headroom_pct` is the output that matters: the percentage by which
    achieved yield could fall from IndiGo's current level before that corridor
    stops covering its own unit cost. Negative means it does not cover it today.
    """
    ref = reference()
    base = baseline()

    pax = corridor_scale(year)
    pax = pax[~pax["region"].isin(EXCLUDED_REGIONS)]
    df = pax.merge(corridor_stage_lengths(), on="region", how="inner")

    df["cask_at_stage"] = [cask_at_stage(d, elasticity=elasticity) for d in df["stage_km"]]
    # The yield a corridor must achieve to cover its own cost, at the load factor
    # Indian carriers actually fly internationally.
    df["breakeven_yield"] = df["cask_at_stage"] / base.load_factor
    df["yield_headroom_pct"] = 100 * (
        ref.yield_inr_per_rpk - df["breakeven_yield"]
    ) / ref.yield_inr_per_rpk

    df["reachable_by_narrowbody"] = df["stage_km"] <= assumption("a321xlr_range_km")
    df["pax_m"] = df["pax_total"] / 1e6
    return df.sort_values("stage_km").reset_index(drop=True)


def sensitivity(values: tuple[float, ...] = (-0.15, -0.25, -0.35)) -> pd.DataFrame:
    """How far the finding moves when the one knob is turned.

    Published rather than kept in a notebook, because a modelled axis without a
    sensitivity is an assertion. Mirrors `profit_pools.sensitivity`.
    """
    rows = []
    for e in values:
        df = corridor_economics(elasticity=e).set_index("region")
        rows.append(
            {
                "elasticity": e,
                "gulf_headroom_pct": round(float(df.loc["Gulf", "yield_headroom_pct"]), 1),
                "europe_headroom_pct": round(float(df.loc["Europe", "yield_headroom_pct"]), 1),
                "north_america_headroom_pct": round(
                    float(df.loc["North America", "yield_headroom_pct"]), 1
                ),
                "gulf_is_tightest": bool(
                    df["yield_headroom_pct"].idxmin() == "Gulf"
                ),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# the connect gap, and what it is worth
# --------------------------------------------------------------------------


def connect_gap(year: int = INTL_COUNTRY_YEAR) -> dict:
    """The passengers whose real destination is past the Gulf hub they route through.

    DGCA counts the India to first-foreign-point sector, so a Delhi to Dubai to
    London passenger is recorded as traffic to the UAE. The sector share is
    therefore higher than the true origin-destination share, and the difference
    is the connecting traffic.

    The O-D side is read with `allow_unverified=True`, which is correct here and
    almost nowhere else. IATA sells origin-destination data and publishes no free
    table, so `gulf_od_share_pct` can never clear the gate. This function exists
    to put a bound on a figure that cannot be verified, exactly as
    `benchmarking.dubai_entitlement_check` does for the bilateral entitlement.
    Nothing derived from it is reported as a point.
    """
    corridors = corridor_scale(year)
    total = float(corridors["pax_total"].sum())
    sector_share = float(corridors.set_index("region").loc["Gulf", "share_pct"])
    od_share = assumption("gulf_od_share_pct", allow_unverified=True)

    gap_pts = sector_share - od_share
    return {
        "sector_share_pct": round(sector_share, 1),
        "od_share_pct": od_share,
        "gap_pts": round(gap_pts, 1),
        "connecting_pax_m": round(total * gap_pts / 100 / 1e6, 2),
        "total_intl_pax_m": round(total / 1e6, 1),
    }


def value_at_stake(year: int = INTL_COUNTRY_YEAR) -> dict:
    """Revenue riding on the connecting passengers, as a band.

    Those passengers are flying a full India to Europe journey and paying a Gulf
    carrier for it. The revenue is bounded rather than pointed, between the two
    yields this repo has actually verified:

      floor    IndiGo's FY2026 achieved 5.06 INR per RPK, an all-economy
               short-haul carrier's realisation
      ceiling  Emirates' 2025-26 achieved 9.924 INR per RPK, a long-haul carrier
               with substantial premium cabins

    Neither is right for the traffic in question and that is the point of a band.
    Read it as the size of the contested pool, **not** as a prize any single
    carrier could capture: it is the market's revenue on those journeys, before
    any assumption about who wins it or at what margin.
    """
    gap = connect_gap(year)
    stage = corridor_stage_lengths().set_index("region").loc["Europe", "stage_km"]
    pax = gap["connecting_pax_m"] * 1e6
    rpk = pax * float(stage)

    lo = rpk * assumption("indigo_yield_inr_per_rpk_fy2026") / 1e7
    hi = rpk * assumption("gulf_carrier_yield_inr_per_rpk") / 1e7
    indigo_revenue = assumption("indigo_revenue_fy2026_inr_cr")
    return {
        **gap,
        "reference_stage_km": float(stage),
        "revenue_floor_inr_cr": round(lo),
        "revenue_ceiling_inr_cr": round(hi),
        "as_multiple_of_indigo_revenue_floor": round(lo / indigo_revenue, 2),
        "as_multiple_of_indigo_revenue_ceiling": round(hi / indigo_revenue, 2),
    }


# --------------------------------------------------------------------------
# the option menu
# --------------------------------------------------------------------------


# Time to capacity and capital intensity are judgements, and are recorded as
# words rather than dressed up as scores. Inventing a 1-to-5 scale for them and
# plotting it would manufacture precision out of an opinion, which is the thing
# this repo refuses everywhere else. What IS computed sits in the two columns
# `corridors_reachable` and `clears_own_cost`.
_OPTIONS = (
    # name, time to capacity, capital, what has to be true
    (
        "Own wide-bodies",
        "2027 at the earliest",
        "High",
        "Deliveries arrive on a schedule no primary source states, and the network "
        "lengthens enough to absorb them",
    ),
    (
        "Lease or damp-lease bridge",
        "Immediate",
        "Low, but recurring",
        "Lease rates leave headroom over the corridor's own cost. Not quantifiable "
        "here: transaction rates are paywalled trade press and no row can clear",
    ),
    (
        "A321XLR on thin routes",
        "Near term",
        "Medium",
        "The corridor sits inside 8,700 km, which excludes North America, and thin "
        "demand suits a narrow-body's seat count",
    ),
    (
        "Codeshare or joint venture",
        "Immediate",
        "None",
        "A partner hub is worth more than the margin ceded, which reverses the "
        "recapture logic the rest of this case rests on",
    ),
    (
        "Do nothing",
        "n/a",
        "None",
        "The connect gap stays with the Gulf carriers, and the order book already "
        "placed is deployed at today's sector length",
    ),
)


def option_menu(year: int = INTL_COUNTRY_YEAR) -> pd.DataFrame:
    """The five ways to add capacity, with the computable columns computed."""
    econ = corridor_economics(year)
    reachable = econ[econ["reachable_by_narrowbody"]]["region"].tolist()
    clears = econ[econ["yield_headroom_pct"] > 0]["region"].tolist()

    rows = []
    for name, timing, capital, condition in _OPTIONS:
        rows.append(
            {
                "option": name,
                "time_to_capacity": timing,
                "capital_intensity": capital,
                "corridors_reachable": (
                    ", ".join(reachable) if name == "A321XLR on thin routes" else "All"
                ),
                "what_would_have_to_be_true": condition,
            }
        )
    df = pd.DataFrame(rows)
    df.attrs["corridors_clearing_own_cost"] = clears
    return df


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------


def fig_yield_headroom(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    df = corridor_economics(year)
    ref = reference()
    gulf = df.set_index("region").loc["Gulf"]

    fig = charts.bar(
        df,
        category="region",
        value="yield_headroom_pct",
        highlight="Gulf",
        orientation="h",
        value_fmt="+.0f",
    )
    fig.add_vline(x=0, line=dict(color=charts.INK, width=1))
    fig.update_xaxes(title_text="Yield could fall this far before the corridor stops covering its cost (%)", ticksuffix="%")

    return charts.finish(
        fig,
        modeled=True,
        title=(
            "The Gulf has the least room to absorb a yield decline of any corridor, "
            "because short sectors keep unit cost high"
        ),
        subtitle=(
            f"Headroom against IndiGo's achieved {ref.yield_inr_per_rpk:.2f} INR per RPK, at the "
            f"{100 * baseline().load_factor:.0f}% load factor Indian carriers fly internationally. "
            f"Unit cost is scaled from IndiGo's published {ref.cask:.2f} CASK at its "
            f"{ref.stage_km:,.0f} km system sector by a modelled elasticity of "
            f"{CASK_STAGE_ELASTICITY}. This says nothing about where the "
            "volume is: the Gulf is still half the market and the recommendation rests on that, "
            "on bilateral position and on the connect premium, not on unit economics"
        ),
        source=SOURCE,
    )


def fig_value_at_stake(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    v = value_at_stake(year)
    indigo_revenue = assumption("indigo_revenue_fy2026_inr_cr")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[v["revenue_floor_inr_cr"], v["revenue_ceiling_inr_cr"] - v["revenue_floor_inr_cr"]],
            y=["Contested connect revenue", "Contested connect revenue"],
            orientation="h",
            marker_color=[charts.GREY, charts.LIGHT],
            base=[0, v["revenue_floor_inr_cr"]],
            hovertemplate="%{x:,.0f} crore<extra></extra>",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Bar(
            x=[indigo_revenue],
            y=["IndiGo FY2026 revenue"],
            orientation="h",
            marker_color=charts.RED,
            text=[f"{indigo_revenue:,.0f}"],
            textposition="outside",
            hovertemplate="%{x:,.0f} crore<extra></extra>",
            showlegend=False,
        )
    )
    for value, label in (
        (v["revenue_floor_inr_cr"], f"{v['revenue_floor_inr_cr']:,.0f}<br>at IndiGo's yield"),
        (v["revenue_ceiling_inr_cr"], f"{v['revenue_ceiling_inr_cr']:,.0f}<br>at Emirates' yield"),
    ):
        fig.add_annotation(
            x=value,
            y="Contested connect revenue",
            text=label,
            showarrow=False,
            yshift=34,
            font=dict(size=11, color=charts.GREY),
        )

    fig.update_layout(barmode="overlay", showlegend=False)
    fig.update_xaxes(title_text="INR crore")
    fig.update_yaxes(title_text="")

    return charts.finish(
        fig,
        modeled=True,
        title=(
            f"The passengers India cannot see carry INR {v['revenue_floor_inr_cr']:,.0f} to "
            f"{v['revenue_ceiling_inr_cr']:,.0f} crore, a third to two thirds of IndiGo's revenue"
        ),
        subtitle=(
            f"{v['connecting_pax_m']:.1f}M passengers a year, the gap between the Gulf's "
            f"{v['sector_share_pct']:.1f}% of India's international sectors and roughly "
            f"{v['od_share_pct']:.0f}% of true origin-destination traffic, flown over a "
            f"{v['reference_stage_km']:,.0f} km reference journey. Banded between the only two "
            "yields this project has verified. The O-D share cannot be verified at all, because "
            "IATA sells that data. Read it as the size of the contested pool, not a prize any one "
            "carrier captures"
        ),
        source=SOURCE,
    )


FIGURES = {
    "yield_headroom": fig_yield_headroom,
    "value_at_stake": fig_value_at_stake,
}


def build_all() -> list[str]:
    written = []
    for name, builder in FIGURES.items():
        charts.export(builder(), name)
        written.append(name)
    return written


if __name__ == "__main__":
    _r = reference()
    print(f"reference: {_r.carrier} {_r.year}, system sector {_r.stage_km:,.0f} km, "
          f"CASK {_r.cask:.2f}, yield {_r.yield_inr_per_rpk:.2f}, LF {_r.load_factor:.1%}")
    print()
    _e = corridor_economics()
    print(_e[["region", "pax_m", "stage_km", "cask_at_stage", "breakeven_yield",
              "yield_headroom_pct", "reachable_by_narrowbody"]].round(2).to_string(index=False))
    print()
    print("sensitivity to the one knob:")
    print(sensitivity().to_string(index=False))
    print()
    for _k, _v in value_at_stake().items():
        print(f"  {_k}: {_v}")
    print()
    print(option_menu().to_string(index=False))
    print()
    for _n in build_all():
        print("wrote", _n)
