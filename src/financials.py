"""IndiGo's own numbers: the P&L, the unit economics and the scale of the commitment.

**Why this module exists.** Every other module in this repo asks a market
question: how big the corridor is, who flies it, whether the aircraft can be
absorbed. None of them asks whether *the client* can carry the decision. The
analysis was always IndiGo-anchored and the delivery never said so, which is why
it read as sector research.

**What it is, exactly.** A P&L, unit-economics and capital-scale view built
entirely from rows that already cleared the gate in
`data/manual/assumptions.csv`. Nothing new is sourced here, so this module adds
no new provenance risk: every figure it returns is either an `assumption()` read
or arithmetic over two of them.

**What it deliberately is not.** A balance sheet, a return on invested capital, a
weighted average cost of capital, or a financing plan. IndiGo publishes an annual
report, but this project's contract is that a hard number is computed in-repo or
carries a source URL and a pull date, and no balance-sheet row has cleared that.
`docs/storyline.md` already names financing as out of scope. Capital scale here
means *how large the commitment is relative to what the airline earns*, expressed
in capacity and revenue rather than in a price nobody publishes.

**The one trap this module exists to not fall into.** IndiGo reported an FY2026
EBITDAR margin of **17.8%**; the ex-forex figure is **27.3%**. This project has
already published and retracted a margin claim once (see `docs/methodology.md`),
and the symmetric error, quoting the flattering ex-forex number alone, is just as
easy. `margin_ladder()` therefore returns *both*, in one table, with which is
which stated in the row. There is no way to read one out of this module without
the other.

    python -m src.financials
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .benchmarking import LATEST_COMPLETE_YEAR, carrier_operating_summary, carrier_share_trend
from .data_pipeline import assumption
from .fleet_gap import baseline
from .market_sizing import _ORDER_BOOK
from .options import CASK_STAGE_ELASTICITY, reference

SOURCE = (
    "IndiGo Q4 & FY2026 results release and Annual Report FY26, Emirates Group 2025-26 "
    "results, and the Airbus order confirmation, all verified in "
    "data/manual/assumptions.csv. Stage lengths, load factors and carrier shares computed "
    "from DGCA"
)

CLIENT = "IndiGo"

# The operator whose commitment this module sizes. Air India's 80 wide-bodies are
# the competitive backdrop and are handled in fleet_gap; this is the client's own
# book and nothing else.
CLIENT_ORDER_OPERATOR = "IndiGo"


# --------------------------------------------------------------------------
# the spread
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Spread:
    """Unit revenue against unit cost, and what it would take to close the gap.

    `inverted` is the finding: in FY2026 IndiGo did not cover its unit cost at
    the operating line as reported. It is one paisa per available seat kilometre,
    which is why the currency comparison beside it matters so much: the rupee
    added 0.41 to CASK in the same year, forty times the gap.
    """

    year: str
    rask: float
    cask: float
    spread: float
    spread_pct_of_rask: float
    inverted: bool
    currency_contribution: float
    currency_vs_gap: float
    stage_km_to_close: float
    stage_uplift_pct_to_close: float
    reference_stage_km: float


def unit_spread() -> Spread:
    """RASK against CASK, and the two ways of reading the gap.

    **The stage-length leg carries a caveat that must travel with it.** Unit cost
    falls as sectors lengthen, so a longer network closes the gap on the cost
    side. Unit *revenue* per seat kilometre falls with stage length too, and this
    repo refuses to compare corridor breakevens against a flat yield for exactly
    that reason (`options.py`, and gotcha 27). The figure below is therefore a
    **cost-side equivalence only**: the sector length at which IndiGo's own cost
    curve reaches today's RASK, holding unit revenue flat, which it will not be.
    It is reported because it is small, not because it is a plan.
    """
    from .scenario import cask_bridge

    rask = assumption("indigo_rask_inr_per_ask_fy2026")
    cask = assumption("indigo_cask_inr_per_ask_fy2026")

    # Read off the published bridge rather than differenced here. The obvious
    # arithmetic, FY2026 ex-fuel minus FY2026 ex-fuel ex-forex, gives 0.52, which
    # is the forex LEVEL sitting in non-fuel cost, not the year-on-year
    # contribution. The contribution is 0.41, because 0.11 of the 0.52 rise is
    # genuine non-fuel inflation. Those two numbers are eleven paise apart and
    # one of them is wrong in every sentence this module writes.
    bridge = cask_bridge().set_index("step")
    currency = float(bridge.loc["Currency", "inr_per_ask"])

    ref = reference()
    spread = rask - cask
    # CASK(D) = CASK_ref (D / D_ref) ^ e, solved for CASK(D) = RASK.
    stage_to_close = ref.stage_km * (rask / cask) ** (1.0 / CASK_STAGE_ELASTICITY)

    return Spread(
        year="FY2026",
        rask=rask,
        cask=cask,
        spread=spread,
        spread_pct_of_rask=100 * spread / rask,
        inverted=spread < 0,
        currency_contribution=currency,
        currency_vs_gap=abs(currency / spread) if spread else float("nan"),
        stage_km_to_close=stage_to_close,
        stage_uplift_pct_to_close=100 * (stage_to_close / ref.stage_km - 1),
        reference_stage_km=ref.stage_km,
    )


# --------------------------------------------------------------------------
# the P&L
# --------------------------------------------------------------------------


def revenue_bridge() -> pd.DataFrame:
    """FY2025 to FY2026 revenue, and what the client's own order book would add.

    The third bar is a **memo item, not a forecast**: the 60 A350s flown at
    FY2026's realised unit revenue and the owned-fleet utilisation basis. It
    answers "how large is this commitment against the business that carries it",
    which is the capital-scale question, without needing an aircraft price, a
    discount rate or a delivery schedule, none of which is verifiable here.
    """
    fy25 = assumption("indigo_revenue_fy2025_inr_cr")
    fy26 = assumption("indigo_revenue_fy2026_inr_cr")
    order = capital_scale()

    return pd.DataFrame(
        [
            {"step": "FY2025 revenue", "inr_cr": fy25, "measure": "absolute", "kind": "actual"},
            {"step": "Growth", "inr_cr": fy26 - fy25, "measure": "relative", "kind": "actual"},
            {"step": "FY2026 revenue", "inr_cr": fy26, "measure": "total", "kind": "actual"},
            {
                "step": "60 A350s at FY2026 RASK",
                "inr_cr": order["revenue_potential_inr_cr"],
                "measure": "relative",
                "kind": "memo",
            },
        ]
    )


def margin_ladder() -> pd.DataFrame:
    """Both FY2026 margins, in one table, because publishing one alone is the error.

    Returned as four rows rather than two so the FY2025 comparative sits beside
    each basis. Reading down the `reported` column tells the story the company
    told; reading down `ex_forex` tells the operating one. Neither is available
    from this function without the other.
    """
    rev25 = assumption("indigo_revenue_fy2025_inr_cr")
    rev26 = assumption("indigo_revenue_fy2026_inr_cr")
    ebitdar25 = assumption("indigo_operating_profit_fy2025_inr_cr")
    ebitdar26_exforex = assumption("indigo_operating_profit_fy2026_inr_cr")
    reported26 = assumption("indigo_ebitdar_margin_fy2026_reported_pct")

    margin25 = 100 * ebitdar25 / rev25
    margin26_exforex = 100 * ebitdar26_exforex / rev26

    return pd.DataFrame(
        [
            {
                "basis": "As reported",
                "year": "FY2025",
                "margin_pct": margin25,
                "note": "EBITDAR over revenue from operations, as published",
            },
            {
                "basis": "As reported",
                "year": "FY2026",
                "margin_pct": reported26,
                "note": (
                    "IndiGo's own financial highlights table. Includes a Q4 forex loss on "
                    "USD lease liabilities"
                ),
            },
            {
                "basis": "Excluding forex",
                "year": "FY2025",
                "margin_pct": margin25,
                "note": "no material forex effect in the comparative year",
            },
            {
                "basis": "Excluding forex",
                "year": "FY2026",
                "margin_pct": margin26_exforex,
                "note": (
                    "the operating read, and the anchor the corridor profit pool uses, "
                    "because forex on lease liabilities is not a route outcome"
                ),
            },
        ]
    )


def cost_stack() -> pd.DataFrame:
    """CASK decomposed twice over, FY2025 against FY2026.

    Three bases, not two, because the middle one is where the FY2026 story hides:
    ex-fuel cost rose 0.52, of which 0.41 is currency and 0.11 is genuine
    non-fuel inflation. Gotcha 20 in CLAUDE.md exists because 3.00 is *both*
    FY2025 CASK ex-fuel and FY2026 CASK ex-fuel ex-forex, and confusing them
    collapses the bridge.
    """
    rows = [
        ("CASK", "indigo_cask_fy2025_inr_per_ask", "indigo_cask_inr_per_ask_fy2026",
         "all-in unit cost"),
        ("CASK ex-fuel", "indigo_cask_exfuel_fy2025_inr_per_ask",
         "indigo_cask_exfuel_inr_per_ask_fy2026", "fuel stripped out"),
        ("CASK ex-fuel ex-forex", "indigo_cask_exfuel_exforex_fy2025_inr_per_ask",
         "indigo_cask_exfuel_exforex_fy2026_inr_per_ask",
         "the basis to use when an FX lever is running, or forex is double counted"),
    ]
    out = []
    for label, key25, key26, note in rows:
        fy25, fy26 = assumption(key25), assumption(key26)
        out.append(
            {
                "basis": label,
                "fy2025": fy25,
                "fy2026": fy26,
                "change": fy26 - fy25,
                "change_pct": 100 * (fy26 / fy25 - 1),
                "note": note,
            }
        )
    return pd.DataFrame(out)


# --------------------------------------------------------------------------
# the commitment
# --------------------------------------------------------------------------


def _client_order_seats() -> tuple[float, int]:
    """Seats on the client's own firm book, read off the shared order table.

    `market_sizing._ORDER_BOOK` is the single place the order book is written
    down, and it is gated on the same verified seat rows as the capacity sizing
    leg. Filtering it here rather than restating 60 A350-900s is what stops this
    module drifting from the sizing band the first time a variant changes.
    """
    seats = 0.0
    count = 0
    for operator, _variant, n, seat_key, _assumed in _ORDER_BOOK:
        if operator != CLIENT_ORDER_OPERATOR:
            continue
        seats += n * assumption(seat_key)
        count += n
    return seats, count


def capital_scale() -> dict:
    """How large the commitment is against the business carrying it.

    **No aircraft price appears here, and that is the point.** List prices are
    not transaction prices, transaction prices are commercially confidential, and
    inventing one would put an unverifiable number at the centre of the client
    page. Scale is expressed instead in the two units this repo can compute:
    capacity the aircraft can produce, and the revenue that capacity would earn
    at the unit revenue the airline actually realised.

    Utilisation is the **owned-fleet** 10.06 hours a day, the same basis the
    capacity sizing leg uses and the same basis gotcha 21 says to state.
    """
    seats, aircraft = _client_order_seats()
    speed = baseline().widebody_block_speed_kmh
    utilisation = assumption("aircraft_utilisation_hours_per_day")
    rask = assumption("indigo_rask_inr_per_ask_fy2026")
    revenue = assumption("indigo_revenue_fy2026_inr_cr")
    ebitdar = assumption("indigo_operating_profit_fy2026_inr_cr")

    ask = seats * speed * utilisation * 365
    revenue_potential = ask * rask / 1e7  # INR to crore

    return {
        "aircraft": aircraft,
        "seats": seats,
        "block_speed_kmh": speed,
        "utilisation_hours_per_day": utilisation,
        "ask": ask,
        "ask_bn": ask / 1e9,
        "revenue_potential_inr_cr": revenue_potential,
        "pct_of_fy2026_revenue": 100 * revenue_potential / revenue,
        "multiple_of_fy2026_ebitdar": revenue_potential / ebitdar,
        "fy2026_revenue_inr_cr": revenue,
        "fy2026_ebitdar_exforex_inr_cr": ebitdar,
        "purchase_rights_not_converted": 40,
    }


# --------------------------------------------------------------------------
# competitive position and operations
# --------------------------------------------------------------------------


def competitive_position(year: int = LATEST_COMPLETE_YEAR) -> pd.DataFrame:
    """The client against the carrier it is competing with for the same passenger.

    One row per carrier, and only the columns that can be filled from a primary
    source or DGCA. Air India's yield is deliberately blank: it is unlisted and
    files nothing, which is a `NOT_AVAILABLE` row in the assumptions ledger
    rather than a gap to be plugged with a proxy.

    **The yield gap is a bound, not a measurement.** Emirates carries substantial
    premium cabins where IndiGo is all-economy, and yield per RPK normally falls
    with stage length, so a long-haul carrier earning double a short-haul one per
    kilometre is a wide gap even after cabin mix. It bounds the prize; it does
    not measure a connect premium.
    """
    intl = carrier_operating_summary(year, international=True).set_index("airline")
    trend = carrier_share_trend()
    last = trend.iloc[-1]

    def row(airline: str) -> dict:
        r = intl.loc[airline] if airline in intl.index else None
        return {
            "carrier": airline,
            "stage_length_km": float(r["stage_length_km"]) if r is not None else None,
            "load_factor_pct": float(r["load_factor_pct"]) if r is not None else None,
            "intl_pax_m": float(r["pax"]) / 1e6 if r is not None else None,
        }

    indigo = row("IndiGo") | {
        "yield_inr_per_rpk": assumption("indigo_yield_inr_per_rpk_fy2026"),
        "group_share_pct": float(last["Indian"]),
        "group": "Indian carriers",
    }
    air_india = row("Air India") | {
        "yield_inr_per_rpk": None,  # unlisted, files nothing. NOT_AVAILABLE in the ledger
        "group_share_pct": float(last["Indian"]),
        "group": "Indian carriers",
    }
    emirates = {
        "carrier": "Emirates",
        "stage_length_km": None,  # not a DGCA carrier row: it flies India as one point
        "load_factor_pct": None,
        "intl_pax_m": None,
        "yield_inr_per_rpk": assumption("gulf_carrier_yield_inr_per_rpk"),
        "group_share_pct": float(last["Gulf"]),
        "group": "Gulf carriers",
    }
    df = pd.DataFrame([indigo, air_india, emirates])
    base = df.loc[df["carrier"] == "IndiGo", "yield_inr_per_rpk"].iloc[0]
    df["yield_vs_indigo"] = df["yield_inr_per_rpk"] / base
    return df


# IndiGo's own FY2026 block hours, 1,220,966 domestic plus 398,604 international,
# read off the Annual Report row that gates `aircraft_utilisation_hours_per_day`.
# Held here as the two components rather than the sum, because the reconciliation
# below only makes sense if you can see which side each part came from.
PUBLISHED_BLOCK_HOURS_FY2026 = {"domestic": 1_220_966.0, "international": 398_604.0}

# Financial year, not calendar year. DGCA publishes monthly and IndiGo reports
# April to March, so the reconciliation has to be run on the airline's basis or
# it compares two different twelve-month windows.
FISCAL_YEAR_END = 2026


def _fiscal_year_rows(df: pd.DataFrame, fy_end: int) -> pd.DataFrame:
    """April of fy_end - 1 through March of fy_end."""
    return df[
        ((df["year"] == fy_end - 1) & (df["month"] >= 4))
        | ((df["year"] == fy_end) & (df["month"] <= 3))
    ]


def operations(fy_end: int = FISCAL_YEAR_END) -> dict:
    """Utilisation, and the second both-ends cross-check in the repo.

    DGCA's aircraft-hours column and IndiGo's own published block hours measure
    the same fleet from opposite ends. **Two bases are reported, and the
    difference between them is itself the finding.**

    On DGCA's *scheduled* services alone the two agree to 0.31%, which is the
    figure published throughout this project. Add DGCA's non-scheduled
    international rows, which is the like-for-like comparison because IndiGo's
    published total includes them, and the gap closes to under a thousandth of a
    per cent. The residual 0.31% was never measurement error: it was
    non-scheduled flying sitting outside the filter.

    Both are returned. The scheduled figure stays the headline so no other
    surface has to move, and the all-services figure is what the reconciliation
    is actually worth.
    """
    from .data_pipeline import load_dgca_domestic_carrier

    # One table, despite the name: `load_dgca_domestic_carrier` returns the DGCA
    # operating file, which carries scheduled domestic, scheduled international
    # and non-scheduled international rows behind `is_scheduled` and
    # `is_international`. There is no aircraft_hours column on the country-pair
    # table at all.
    rows = _fiscal_year_rows(load_dgca_domestic_carrier(), fy_end)
    rows = rows[rows["airline"] == CLIENT]

    scheduled = float(rows[rows["is_scheduled"]]["aircraft_hours"].sum())
    all_services = float(rows["aircraft_hours"].sum())
    published = sum(PUBLISHED_BLOCK_HOURS_FY2026.values())

    utilisation = assumption("aircraft_utilisation_hours_per_day")

    return {
        "fiscal_year_end": fy_end,
        "utilisation_hours_per_day": utilisation,
        "utilisation_basis": "owned fleet, block hours over aircraft at period end",
        "published_block_hours": published,
        "dgca_scheduled_hours": scheduled,
        "dgca_all_services_hours": all_services,
        "reconciliation_pct": 100 * abs(scheduled - published) / published,
        "reconciliation_all_services_pct": 100 * abs(all_services - published) / published,
        "implied_aircraft": published / utilisation / 365,
        "non_scheduled_intl_hours": all_services - scheduled,
    }


def summary() -> dict:
    """Everything the client page needs, in one call."""
    spread = unit_spread()
    return {
        "client": CLIENT,
        "spread": spread.__dict__,
        "revenue_bridge": revenue_bridge().to_dict(orient="records"),
        "margin_ladder": margin_ladder().to_dict(orient="records"),
        "cost_stack": cost_stack().to_dict(orient="records"),
        "capital_scale": capital_scale(),
        "competitive_position": competitive_position().to_dict(orient="records"),
        "operations": operations(),
        "source": SOURCE,
    }


def main() -> int:
    s = unit_spread()
    print(f"{CLIENT} {s.year}")
    print(f"  RASK {s.rask:.2f} against CASK {s.cask:.2f}, spread {s.spread:+.2f} INR per ASK")
    print(f"  inverted: {s.inverted}. Currency added {s.currency_contribution:+.2f}, "
          f"{s.currency_vs_gap:.0f}x the gap")
    print(f"  cost-side close at {s.stage_km_to_close:,.0f} km "
          f"({s.stage_uplift_pct_to_close:+.1f}% on {s.reference_stage_km:,.0f} km)")

    print("\nmargin ladder")
    print(margin_ladder().to_string(index=False, columns=["basis", "year", "margin_pct"]))

    print("\ncost stack")
    print(cost_stack().to_string(index=False, columns=["basis", "fy2025", "fy2026", "change"]))

    cap = capital_scale()
    print(f"\ncapital scale: {cap['aircraft']} aircraft, {cap['seats']:,.0f} seats, "
          f"{cap['ask_bn']:.1f}bn ASK")
    print(f"  revenue potential INR {cap['revenue_potential_inr_cr']:,.0f} cr, "
          f"{cap['pct_of_fy2026_revenue']:.0f}% of FY2026 revenue, "
          f"{cap['multiple_of_fy2026_ebitdar']:.2f}x EBITDAR ex forex")

    ops = operations()
    print(f"\noperations: {ops['utilisation_hours_per_day']:.2f} h/day, DGCA vs published "
          f"block hours agree to {ops['reconciliation_pct']:.2f}%")

    print("\ncompetitive position")
    print(competitive_position().to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
