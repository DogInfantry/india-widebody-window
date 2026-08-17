"""Base, bull and bear paths for India's international market to 2030.

All three levers of the original design are now built: demand, fuel and FX.

Fuel and FX were absent for most of this project's life on the stated grounds
that they price into revenue and revenue depends on gated yields. That was half
right, and the half that was wrong is worth recording: they do not need a YIELD,
they need a UNIT COST decomposition, and IndiGo publishes one. Once the CASK
rows were split into fuel, dollar-linked and rupee components, both levers fell
straight out and reconcile to the published CASK to the paisa.

The two families answer different questions and are kept apart on purpose:

  demand      how many passengers there are, in 2030
  fuel, FX    what a passenger is worth, at today's volumes

Folding the second into the first would imply a price elasticity nobody here has
measured. Demand scenarios need nothing but passenger counts, all of which are
measured.

The three rates are anchored on observed history rather than picked to look
symmetric around the base:

  bear  the slowest sustained rate India actually recorded pre-covid
  base  the full pre-covid CAGR, which is what the trend sizing method uses
  bull  the pre-covid rate plus the gap to the post-covid recovery rate,
        capped, on the argument that recovery pace is a real upper bound on how
        fast this market can add capacity

A symmetric plus or minus two points around the base would have been easier and
would have meant nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from . import charts
from .data_pipeline import assumption
from .market_sizing import BASE_YEAR, POST_COVID, PRE_COVID, TARGET_YEAR, _annual_international, _cagr

SOURCE = (
    "DGCA traffic statistics via github.com/Vonter/india-aviation-traffic (ODbL). "
    "Pulled 2026-08-15"
)

# Ceiling on the bull case. India added international capacity fastest during the
# post-covid restart, which is a genuine physical bound on how quickly aircraft,
# crew and slots can be brought on. Beyond it the constraint stops being demand.
BULL_CAP = 0.12


@dataclass(frozen=True)
class Scenario:
    name: str
    cagr: float
    rationale: str

    def project(self, base_value: float, from_year: int, to_year: int) -> float:
        return base_value * (1 + self.cagr) ** (to_year - from_year)

    def path(self, base_value: float, from_year: int, to_year: int) -> pd.DataFrame:
        years = list(range(from_year, to_year + 1))
        return pd.DataFrame(
            {
                "year": years,
                "scenario": self.name,
                "pax_m": [self.project(base_value, from_year, y) / 1e6 for y in years],
            }
        )


def scenarios() -> list[Scenario]:
    """Build the three cases from observed rates, not from round numbers."""
    series = _annual_international()
    pre = _cagr(series, *PRE_COVID)
    post = _cagr(series, *POST_COVID)

    # The slowest sustained stretch this market has actually delivered.
    #
    # Rolled across BOTH clean blocks, pre-covid and post-recovery, skipping the
    # 2020-21 collapse. An earlier version rolled a four-year window across the
    # four-year pre-covid block alone, which admits exactly one stretch: the bear
    # case came out identical to the base by construction. Caught because the two
    # printed the same number.
    window = 3
    blocks = [series.loc[PRE_COVID[0] : PRE_COVID[1]], series.loc[POST_COVID[0] : POST_COVID[1]]]
    rates = [
        _cagr(block, y, y + window)
        for block in blocks
        for y in block.index
        if y + window in block.index
    ]
    if not rates:
        raise RuntimeError("no clean multi-year stretch available to anchor the bear case")
    bear_rate = min(rates)

    bull_rate = min(pre + (post - pre) * 0.35, BULL_CAP)

    return [
        Scenario(
            "Bear",
            bear_rate,
            f"slowest sustained {window} year stretch across both clean blocks, "
            "pre-covid and post-recovery",
        ),
        Scenario("Base", pre, f"pre-covid CAGR {PRE_COVID[0]} to {PRE_COVID[1]}"),
        Scenario(
            "Bull",
            bull_rate,
            f"part way to the post-covid recovery rate, capped at {BULL_CAP:.0%} "
            "because capacity cannot be added faster",
        ),
    ]


def scenario_table(target_year: int = TARGET_YEAR) -> pd.DataFrame:
    base_value = float(_annual_international()[BASE_YEAR])
    rows = []
    for s in scenarios():
        value = s.project(base_value, BASE_YEAR, target_year)
        rows.append(
            {
                "scenario": s.name,
                "cagr_pct": 100 * s.cagr,
                "pax_2030_m": value / 1e6,
                "growth_vs_base_year_pct": 100 * (value / base_value - 1),
                "rationale": s.rationale,
            }
        )
    return pd.DataFrame(rows)


def scenario_paths(target_year: int = TARGET_YEAR) -> pd.DataFrame:
    base_value = float(_annual_international()[BASE_YEAR])
    return pd.concat(
        [s.path(base_value, BASE_YEAR, target_year) for s in scenarios()], ignore_index=True
    )


def fig_scenarios(target_year: int = TARGET_YEAR) -> go.Figure:
    paths = scenario_paths(target_year)
    history = _annual_international()
    hist = history.loc[: BASE_YEAR]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(hist.index),
            y=[v / 1e6 for v in hist.to_numpy()],
            mode="lines",
            name="Actual",
            line=dict(color=charts.INK, width=2.5),
            hovertemplate="%{x}: %{y:.1f}M<extra></extra>",
        )
    )

    styles = {
        "Bear": dict(color=charts.LIGHT, dash="dot"),
        "Base": dict(color=charts.RED, dash="solid"),
        "Bull": dict(color=charts.GREY, dash="dash"),
    }
    for name, style in styles.items():
        p = paths[paths["scenario"] == name]
        fig.add_trace(
            go.Scatter(
                x=p["year"],
                y=p["pax_m"],
                mode="lines",
                name=name,
                line=dict(color=style["color"], width=2.5 if name == "Base" else 1.8, dash=style["dash"]),
                hovertemplate=name + " %{x}: %{y:.1f}M<extra></extra>",
            )
        )

    table = scenario_table(target_year).set_index("scenario")
    for name in ("Bear", "Base", "Bull"):
        fig.add_annotation(
            x=target_year,
            y=table.loc[name, "pax_2030_m"],
            text=f"<b>{name}</b> {table.loc[name, 'pax_2030_m']:.0f}M",
            xanchor="left",
            xshift=8,
            showarrow=False,
            font=dict(size=12, color=charts.RED if name == "Base" else charts.GREY),
        )

    fig.update_layout(showlegend=False)
    fig.update_xaxes(range=[int(history.index.min()) - 0.5, target_year + 2.5])

    spread = table.loc["Bull", "pax_2030_m"] - table.loc["Bear", "pax_2030_m"]
    return charts.finish(
        fig,
        title=(
            f"Even the bear case adds {table.loc['Bear', 'pax_2030_m'] - hist[BASE_YEAR] / 1e6:.0f}M "
            f"international passengers by {target_year}"
        ),
        subtitle=(
            f"India international sector passengers, millions. Growth rates anchored on "
            f"observed history, not chosen for symmetry. Spread {spread:.0f}M. "
            "Fuel and FX act on unit economics, not on these paths, and are charted separately"
        ),
        source=SOURCE,
    )


# --------------------------------------------------------------------------
# fuel and FX levers
#
# These were absent for most of this project's life, and the module docstring
# above records why: they were said to need yields that are still gated. That was
# half right. They do not need a YIELD, they need a UNIT COST decomposition, and
# IndiGo publishes exactly that. The levers below rest on verified rows and
# reconcile to the published CASK to the paisa.
#
# They do NOT move passenger counts. Fuel and FX change what a passenger is
# worth, not how many there are, so they act on unit economics rather than on the
# demand paths above. Folding them into the demand scenarios would imply a price
# elasticity nobody here has measured.
# --------------------------------------------------------------------------

SOURCE_FILINGS = (
    "IndiGo Q4 and FY2026 results press release; IOCL aviation fuel prices; FBIL USD/INR "
    "reference rate. All rows verified in data/manual/assumptions.csv"
)


def unit_economics() -> pd.DataFrame:
    """Split IndiGo's FY2026 CASK into fuel, dollar-linked and rupee costs.

    Each part is a difference of two verified rows, never a guess:

        fuel            CASK          minus CASK ex fuel
        forex non-fuel  CASK ex fuel  minus CASK ex fuel ex forex
        rupee non-fuel  CASK ex fuel ex forex

    The three sum to the published CASK by construction, and a test pins it.
    """
    cask = assumption("indigo_cask_inr_per_ask_fy2026")
    exfuel = assumption("indigo_cask_exfuel_inr_per_ask_fy2026")
    core = assumption("indigo_cask_exfuel_exforex_fy2026_inr_per_ask")
    rows = [
        ("Fuel", cask - exfuel, "USD priced on international sectors, rupee priced domestically"),
        ("Non-fuel, dollar linked", exfuel - core, "Leases and maintenance denominated in USD"),
        ("Non-fuel, rupee", core, "Wages, airport charges and domestic services"),
    ]
    df = pd.DataFrame(rows, columns=["component", "inr_per_ask", "note"])
    df["share_pct"] = 100 * df["inr_per_ask"] / cask
    return df


def cask_bridge() -> pd.DataFrame:
    """FY2025 to FY2026 CASK, split into fuel, real inflation and currency.

    The headline: currency added more than the entire net increase, because fuel
    fell. IndiGo's unit costs did not deteriorate operationally by anything like
    the headline number suggests. That is the same correction as the retraction in
    `docs/methodology.md`, made at the unit-cost line instead of the margin line.
    """
    cask25 = assumption("indigo_cask_fy2025_inr_per_ask")
    cask26 = assumption("indigo_cask_inr_per_ask_fy2026")
    exfuel25 = assumption("indigo_cask_exfuel_fy2025_inr_per_ask")
    exfuel26 = assumption("indigo_cask_exfuel_inr_per_ask_fy2026")
    core25 = assumption("indigo_cask_exfuel_exforex_fy2025_inr_per_ask")
    core26 = assumption("indigo_cask_exfuel_exforex_fy2026_inr_per_ask")

    return pd.DataFrame(
        [
            ("FY2025 CASK", cask25, "absolute"),
            ("Fuel", (cask26 - exfuel26) - (cask25 - exfuel25), "relative"),
            ("Real non-fuel", core26 - core25, "relative"),
            ("Currency", (exfuel26 - core26) - (exfuel25 - core25), "relative"),
            ("FY2026 CASK", cask26, "total"),
        ],
        columns=["step", "inr_per_ask", "measure"],
    )


def dollar_exposure() -> dict:
    """How much of unit cost moves with the rupee, reported as a band.

    The band is not hedging, it is the honest range:

      floor    only the dollar-linked non-fuel costs, correct if every litre of
               fuel is bought at the rupee domestic price
      ceiling  those plus ALL fuel, correct if every litre is bought at the USD
               international price

    Neither end is right for the system, because IndiGo buys both: domestic
    sectors take rupee-priced ATF, international sectors take the USD price
    (1,690.81 per kilolitre at Delhi against 104,927 rupees domestic, a 54 per
    cent gap). DGCA publishes no fuel split by sector type and no free source
    does, so the split is unknown and the band is reported rather than a midpoint
    that would look precise and be invented.
    """
    u = unit_economics().set_index("component")["inr_per_ask"]
    cask = assumption("indigo_cask_inr_per_ask_fy2026")
    floor = float(u["Non-fuel, dollar linked"])
    ceiling = floor + float(u["Fuel"])
    return {
        "floor_inr_per_ask": round(floor, 4),
        "ceiling_inr_per_ask": round(ceiling, 4),
        "floor_pct_of_cask": round(100 * floor / cask, 1),
        "ceiling_pct_of_cask": round(100 * ceiling / cask, 1),
    }


def cost_under_shock(atf_pct: float = 0.0, inr_depreciation_pct: float = 0.0) -> pd.DataFrame:
    """CASK after a fuel move and a rupee move, at both ends of the exposure band.

    `inr_depreciation_pct` is a WEAKENING of the rupee, so positive values raise
    dollar-denominated costs.
    """
    u = unit_economics().set_index("component")["inr_per_ask"]
    fuel = float(u["Fuel"]) * (1 + atf_pct / 100)
    fx_nonfuel = float(u["Non-fuel, dollar linked"]) * (1 + inr_depreciation_pct / 100)
    rupee = float(u["Non-fuel, rupee"])
    return pd.DataFrame(
        [
            ("Floor, fuel bought in rupees", fuel + fx_nonfuel + rupee),
            (
                "Ceiling, fuel bought in dollars",
                fuel * (1 + inr_depreciation_pct / 100) + fx_nonfuel + rupee,
            ),
        ],
        columns=["fuel_pricing_basis", "cask_inr_per_ask"],
    )


def fuel_fx_sensitivity(
    moves: tuple[float, ...] = (-20.0, -10.0, 0.0, 10.0, 20.0),
) -> pd.DataFrame:
    """CASK against RASK under fuel and rupee moves.

    RASK is FY2026 actual and is held flat, deliberately. Letting revenue rise
    with costs would assume a pass-through this repo has not measured, and would
    quietly turn a cost sensitivity into a margin forecast.
    """
    rask = assumption("indigo_rask_inr_per_ask_fy2026")
    rows = []
    for m in moves:
        fuel_only = float(cost_under_shock(atf_pct=m).iloc[0]["cask_inr_per_ask"])
        fx_ceiling = float(cost_under_shock(inr_depreciation_pct=m).iloc[1]["cask_inr_per_ask"])
        rows.append(
            {
                "move_pct": m,
                "cask_fuel_shock": round(fuel_only, 3),
                "cask_fx_shock_ceiling": round(fx_ceiling, 3),
                "rask_actual": rask,
                "fuel_shock_spread": round(rask - fuel_only, 3),
                "fx_shock_spread": round(rask - fx_ceiling, 3),
            }
        )
    return pd.DataFrame(rows)


def fig_cask_bridge() -> go.Figure:
    df = cask_bridge()
    fig = charts.waterfall(df, x="step", y="inr_per_ask", measure="measure", value_fmt="+.2f")
    fx = float(df.loc[df["step"] == "Currency", "inr_per_ask"].iloc[0])
    net = float(
        df.loc[df["step"] == "FY2026 CASK", "inr_per_ask"].iloc[0]
        - df.loc[df["step"] == "FY2025 CASK", "inr_per_ask"].iloc[0]
    )
    real = float(df.loc[df["step"] == "Real non-fuel", "inr_per_ask"].iloc[0])
    return charts.finish(
        fig,
        title=(
            f"Currency added {fx:+.2f} to IndiGo's unit cost, more than the entire "
            f"{net:+.2f} increase, because fuel fell"
        ),
        subtitle=(
            f"Rupees per available seat kilometre, FY2025 to FY2026. Real non-fuel cost "
            f"inflation was {real:+.2f}. Reading the headline CASK rise as an operating "
            "deterioration repeats, at the unit cost line, the margin error retracted in "
            "the methodology"
        ),
        source=SOURCE_FILINGS,
    )


def fig_fuel_fx_sensitivity() -> go.Figure:
    df = fuel_fx_sensitivity()
    rask = assumption("indigo_rask_inr_per_ask_fy2026")
    fig = go.Figure()
    for col, name, color in (
        ("cask_fuel_shock", "Fuel price move", charts.GREY),
        ("cask_fx_shock_ceiling", "Rupee move, fuel in dollars", charts.RED),
    ):
        fig.add_trace(
            go.Scatter(
                x=df["move_pct"],
                y=df[col],
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=2.5),
                marker=dict(size=7, color=color),
                hovertemplate=f"<b>{name}</b><br>%{{x:+.0f}}%: CASK %{{y:.2f}}<extra></extra>",
            )
        )
    fig.add_hline(
        y=rask,
        line=dict(color=charts.INK, width=1, dash="dot"),
        annotation_text=f"RASK {rask:.2f}, FY2026 actual",
        annotation_position="top left",
    )
    fig.update_xaxes(title_text="Move in fuel price or rupee (%)", ticksuffix="%")
    fig.update_yaxes(title_text="CASK (INR per ASK)")
    return charts.finish(
        fig,
        title=(
            "A rupee move costs more than the same fuel move, and every path starts "
            "above breakeven"
        ),
        subtitle=(
            "CASK against FY2026 actual RASK, held flat because pass-through has not been "
            "measured here. FY2026 already opens with CASK 5.00 against RASK 4.99, so every "
            "line starts loss-making at the operating level before any shock is applied"
        ),
        source=SOURCE_FILINGS,
    )


FIGURES = {
    "scenarios": fig_scenarios,
    "cask_bridge": fig_cask_bridge,
    "fuel_fx_sensitivity": fig_fuel_fx_sensitivity,
}


def build_all() -> list[str]:
    written = []
    for name, builder in FIGURES.items():
        charts.export(builder(), name)
        written.append(name)
    return written


if __name__ == "__main__":
    print(scenario_table().to_string(index=False))
    print()
    print(unit_economics().to_string(index=False))
    print()
    print(cask_bridge().to_string(index=False))
    print()
    print("dollar exposure:", dollar_exposure())
    print()
    print(fuel_fx_sensitivity().to_string(index=False))
    for _n in build_all():
        print("wrote", _n)
