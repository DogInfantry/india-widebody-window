"""Belly freight by corridor, and why it is not the argument it looks like.

DGCA has published freight alongside passengers in every file this project reads,
and nothing has ever read it. Wide-body belly cargo is real money and the corridor
economics in `options.py` ignore it entirely, so this closes a gap that has been
open since the pipeline was written.

**The obvious version of this analysis is wrong, and it is worth saying so before
the numbers rather than after.** The tempting claim is that cargo reinforces the
long-haul case, because wide-bodies have holds and long sectors fill them. The
data does not support it:

    correlation between sector length and freight per passenger:  -0.10

That is nothing. North America is the longest corridor on the map at 11,755 km and
carries **18.4 kg** per passenger, less than Africa. East Asia is barely half its
length and carries **129.8 kg**. Belly freight tracks what two economies trade,
not how far apart they are, and any chart here that implied otherwise would be
selling a story the source contradicts.

**What the data does support**, which is narrower and more useful:

  Europe carries 3.7x the Gulf's freight per passenger, 64.8 kg against 17.5.
  That supports the Europe-first recommendation on a dimension nothing else in
  the case uses, and it does so without appealing to distance at all.

  East Asia is the outlier worth naming. 129.8 kg per passenger on a corridor
  carrying only 2.0M passengers: the thinnest passenger market in the set with
  the densest freight. Nothing in this case currently looks at it.

**Physical units only. There is no revenue leg here, on purpose.** Converting
tonne-kilometres to money needs a yield per freight tonne kilometre, and no Indian
carrier publishes one. The corridor economics in `options.py` currently rest on
verified rows alone, and that is the strongest property they have; bolting a
modelled cargo yield onto them would trade a hard exhibit for a softer one to
strengthen a secondary point. If a citable FTK yield ever surfaces, this module is
where it goes.

One caveat on the measure itself. DGCA reports freight against the same
India-to-first-foreign-point sector as passengers, so a tonne routed through Dubai
to Frankfurt is Gulf freight here, exactly as the passenger would be. The connect
distortion the whole case turns on applies to this table too, and if anything it
flatters the Gulf.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import charts
from .benchmarking import INTL_COUNTRY_YEAR, load_dgca_intl_country
from .profit_pools import EXCLUDED_REGIONS, corridor_stage_lengths

SOURCE = (
    "Freight and passengers from DGCA international country statistics via "
    "github.com/Vonter/india-aviation-traffic (ODbL); corridor reference distances are great "
    "circle from OurAirports (CC0). Physical units only, no revenue assumption"
)


def corridor_freight(year: int = INTL_COUNTRY_YEAR) -> pd.DataFrame:
    """Freight, passengers and their ratio by corridor. Nothing modelled.

    `freight_to_india` and `freight_from_india` are summed for the same reason
    `pax_total` is: DGCA reports both directions and the corridor is the unit of
    analysis, not the direction.
    """
    df = load_dgca_intl_country()
    df = df[df["year"] == year]

    grouped = (
        df.assign(freight_t=df["freight_to_india"] + df["freight_from_india"])
        .groupby("region", as_index=False)
        .agg(pax=("pax_total", "sum"), freight_t=("freight_t", "sum"))
    )
    grouped = grouped[~grouped["region"].isin(EXCLUDED_REGIONS)]

    out = grouped.merge(corridor_stage_lengths(), on="region", how="inner")
    out = out[out["pax"] > 0].copy()

    out["kg_per_pax"] = 1000 * out["freight_t"] / out["pax"]
    # Freight and revenue tonne kilometres, so cargo and passengers can be
    # compared on the one unit the rest of this repo already uses for capacity.
    out["ftk_bn"] = out["freight_t"] * out["stage_km"] / 1e9
    out["rpk_bn"] = out["pax"] * out["stage_km"] / 1e9
    out["ftk_per_100_rpk"] = 100 * out["ftk_bn"] / out["rpk_bn"]
    return out.sort_values("stage_km").reset_index(drop=True)


def distance_correlation(year: int = INTL_COUNTRY_YEAR) -> float:
    """Pearson correlation of sector length against freight per passenger.

    Its own function because it is the module's central caveat rather than a
    detail, and a test asserts it stays near zero. If this ever climbs, the
    prose above is wrong and has to be rewritten rather than quietly left.
    """
    df = corridor_freight(year)
    return float(df["stage_km"].corr(df["kg_per_pax"]))


def summary(year: int = INTL_COUNTRY_YEAR) -> dict:
    df = corridor_freight(year).set_index("region")
    gulf, europe = df.loc["Gulf"], df.loc["Europe"]
    densest = df["kg_per_pax"].idxmax()
    return {
        "year": year,
        "europe_kg_per_pax": round(float(europe["kg_per_pax"]), 1),
        "gulf_kg_per_pax": round(float(gulf["kg_per_pax"]), 1),
        "europe_vs_gulf": round(float(europe["kg_per_pax"] / gulf["kg_per_pax"]), 1),
        "densest_corridor": densest,
        "densest_kg_per_pax": round(float(df.loc[densest, "kg_per_pax"]), 1),
        "densest_pax_m": round(float(df.loc[densest, "pax"]) / 1e6, 1),
        "distance_correlation": round(distance_correlation(year), 2),
        "total_freight_kt": round(float(df["freight_t"].sum()) / 1e3),
        "system_ftk_per_100_rpk": round(
            float(100 * df["ftk_bn"].sum() / df["rpk_bn"].sum()), 1
        ),
    }


def fig_cargo_asymmetry(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    df = corridor_freight(year)
    s = summary(year)

    # Ordered by sector length, shortest first, so the ABSENCE of a distance
    # relationship is something the reader sees rather than something the
    # subtitle asserts. A ranking by freight would hide exactly the thing this
    # chart exists to show.
    labels = [f"{r}<br><span style='font-size:11px'>{d:,.0f} km</span>"
              for r, d in zip(df["region"], df["stage_km"])]
    plotted = df.assign(corridor=labels)

    fig = charts.bar(
        plotted,
        category="corridor",
        value="kg_per_pax",
        highlight=[l for l, r in zip(labels, df["region"]) if r == "Europe"],
        orientation="h",
        value_fmt=".0f",
        sort=False,
    )
    fig.update_xaxes(title_text="Freight carried per passenger (kg)")
    fig.update_yaxes(title_text="", autorange="reversed")

    return charts.finish(
        fig,
        title=(
            f"Europe carries {s['europe_vs_gulf']:.1f} times the Gulf's freight per "
            f"passenger, and distance does not explain it"
        ),
        subtitle=(
            f"Corridors ordered by sector length, shortest at the top. The correlation "
            f"between the two is {s['distance_correlation']:+.2f}, so belly freight tracks what "
            f"two economies trade rather than how far apart they are: {s['densest_corridor']} is "
            f"the densest at {s['densest_kg_per_pax']:.0f} kg on only "
            f"{s['densest_pax_m']:.1f}M passengers, while North America is the longest corridor "
            "and near the bottom. Physical units, no revenue assumption. DGCA counts freight on "
            "the same first-foreign-point sector as passengers, so connecting tonnage flatters "
            "the Gulf here exactly as it does elsewhere"
        ),
        source=SOURCE,
    )


FIGURES = {
    "cargo_asymmetry": fig_cargo_asymmetry,
}


def build_all() -> list[str]:
    written = []
    for name, builder in FIGURES.items():
        charts.export(builder(), name)
        written.append(name)
    return written


if __name__ == "__main__":
    print(corridor_freight()[
        ["region", "stage_km", "pax", "freight_t", "kg_per_pax", "ftk_bn", "ftk_per_100_rpk"]
    ].round(1).to_string(index=False))
    print()
    for _k, _v in summary().items():
        print(f"  {_k}: {_v}")
    print()
    for _n in build_all():
        print("wrote", _n)
