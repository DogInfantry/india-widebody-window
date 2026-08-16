"""Base, bull and bear paths for India's international market to 2030.

Scope note, stated because the plan promised more than this module delivers.
The original design had three levers: demand, fuel and FX. Only **demand** is
built. Fuel and FX both price into revenue, and revenue depends on yields that
are still gated behind `dp.assumption()`. Building levers that raise on every
call would be inventory, not progress, so they are absent rather than stubbed.

What is here is real. Demand scenarios need nothing but passenger counts, all of
which are measured.

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
            "Fuel and FX levers are absent, not stubbed: both need yields that are still gated"
        ),
        source=SOURCE,
    )


def build_all() -> list[str]:
    charts.export(fig_scenarios(), "scenarios")
    return ["scenarios"]


if __name__ == "__main__":
    print(scenario_table().to_string(index=False))
    for _n in build_all():
        print("wrote", _n)
