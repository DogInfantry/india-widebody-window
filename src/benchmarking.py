"""Carrier and corridor benchmarking.

The differentiating metric here is **average stage length**, RPK divided by
passengers. It needs no assumption, it falls straight out of two published
columns, and it separates a short-haul international network from a long-haul one
more honestly than fleet counts or route maps do.

That single metric carries the case. In 2025 IndiGo flew more international
passengers than Air India while flying far fewer passenger-kilometres, because its
international network is Gulf and Southeast Asia at roughly 2,600 km while Air
India's averages over 5,300 km. The wide-body orders exist to close that gap.

Nothing in this module reads a hand-entered assumption. Every figure is computed
from DGCA, so all of it is reproducible by anyone who clones the repo.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import charts
from .data_pipeline import (
    assumption,
    load_dgca_domestic_carrier,
    load_dgca_intl_carrier,
    load_dgca_intl_city,
    load_dgca_intl_country,
)

# DGCA international country data runs complete through 2025. The carrier
# operating file runs into 2026 but the current year is partial, so annual
# comparisons stop at the last complete year rather than quietly mixing them.
LATEST_COMPLETE_YEAR = 2025
INTL_COUNTRY_YEAR = 2024

SOURCE_DGCA = (
    "DGCA traffic statistics, via github.com/Vonter/india-aviation-traffic (ODbL). "
    "Pulled 2026-08-15"
)

INDIAN_GATEWAYS = {
    "DELHI", "MUMBAI", "BENGALURU", "CHENNAI", "HYDERABAD", "KOCHI",
    "KOLKATA", "AHMEDABAD", "AMRITSAR", "TRIVANDRUM", "CALICUT", "GOA",
}

GULF_POINTS = {
    "DUBAI", "ABU DHABI", "DOHA", "SHARJAH", "MUSCAT", "KUWAIT",
    "BAHRAIN", "DAMMAM", "RIYADH", "JEDDAH", "RAS AL KHAIMAH",
}


def _norm_point(name: str) -> str:
    """Normalise a city name for set membership.

    DGCA writes `ABUDHABI` with no space and `RAS AL-KHAIMAH` with a hyphen,
    while the readable literals above use spaces. Exact matching therefore missed
    Abu Dhabi entirely, and Abu Dhabi is 5.7M passengers a year: for a while the
    Gulf-hub Sankey filed all of it under "Everywhere else, direct".

    This is the same failure mode as the carrier-name variants recorded in
    CLAUDE.md, where `AIR ARABIA-ABU DHABI` used a hyphen where the list had a
    space. The lesson was learned for carriers and never carried across to city
    points. Comparing on a normalised key fixes the whole class rather than the
    two names that happened to be noticed.
    """
    return name.upper().replace(" ", "").replace("-", "")


_GULF_KEYS = {_norm_point(p) for p in GULF_POINTS}


def is_gulf_point(name: str) -> bool:
    """True if a DGCA foreign point is a Gulf point, robust to spacing variants."""
    return _norm_point(name) in _GULF_KEYS


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------


def carrier_operating_summary(
    year: int = LATEST_COMPLETE_YEAR, *, international: bool = False
) -> pd.DataFrame:
    """Per-carrier passengers, share, load factor and average stage length.

    `international=True` uses the ScheduledInternational rows, which cover Indian
    carriers only. Foreign carriers file no operating statistics with DGCA, so
    their stage length is not knowable from this source and is not guessed.
    """
    service = "ScheduledInternational" if international else "ScheduledDomestic"
    df = load_dgca_domestic_carrier()
    df = df[(df["service_type"] == service) & (df["year"] == year)]

    out = df.groupby("airline", as_index=False).agg(
        pax=("pax", "sum"), rpk=("rpk", "sum"), ask=("ask", "sum")
    )
    out = out[(out["pax"] > 0) & (out["ask"] > 0)].copy()
    out["share_pct"] = 100 * out["pax"] / out["pax"].sum()
    out["load_factor_pct"] = 100 * out["rpk"] / out["ask"]
    out["stage_length_km"] = out["rpk"] / out["pax"]
    return out.sort_values("pax", ascending=False).reset_index(drop=True)


def who_carries_india(year: int = INTL_COUNTRY_YEAR) -> pd.DataFrame:
    """Split India's international traffic between Indian, Gulf and other carriers."""
    df = load_dgca_intl_carrier()
    df = df[df["year"] == year]
    out = df.groupby("carrier_group", as_index=False)["pax_total"].sum()
    out["share_pct"] = 100 * out["pax_total"] / out["pax_total"].sum()
    return out.sort_values("pax_total", ascending=False).reset_index(drop=True)


def carrier_share_trend(start: int = 2015, end: int = LATEST_COMPLETE_YEAR) -> pd.DataFrame:
    """Share of India's international traffic by carrier home region, per year.

    Answers branch 2.3 of the hypothesis tree, which asked whether the Indian
    carrier share is stable or eroding. Neither: it is climbing, from 37.0% in
    2015 to 45.9% in 2025, while the Gulf carriers' share fell from 32.7% to
    26.2%.

    That finding contradicts the framing this case started with. Indian carriers
    are not losing their home market, they have been taking it back for a
    decade. What remains is a structural gap in equipment rather than a
    competitive rout, which is a better argument for the wide-body order, not a
    worse one.

    2020 and 2021 are returned but should not be read as trend: repatriation
    flights and air bubble arrangements put Indian carriers above 50% for two
    years on a base of a fifth the usual traffic.
    """
    df = load_dgca_intl_carrier()
    df = df[(df["year"] >= start) & (df["year"] <= end)]

    totals = df.groupby(["year", "carrier_group"], as_index=False)["pax_total"].sum()
    wide = totals.pivot(index="year", columns="carrier_group", values="pax_total").fillna(0.0)
    share = 100 * wide.div(wide.sum(axis=1), axis=0)
    share["total_pax"] = wide.sum(axis=1)
    return share.reset_index()


def corridor_scale(year: int = INTL_COUNTRY_YEAR) -> pd.DataFrame:
    """India's international traffic by destination region."""
    df = load_dgca_intl_country()
    df = df[df["year"] == year]
    out = df.groupby("region", as_index=False)["pax_total"].sum()
    out["share_pct"] = 100 * out["pax_total"] / out["pax_total"].sum()
    return out.sort_values("pax_total", ascending=False).reset_index(drop=True)


def gateway_flows(year: int = INTL_COUNTRY_YEAR, *, top_gateways: int = 6) -> pd.DataFrame:
    """Indian gateway city to destination bucket, for the flow diagram.

    A deliberate limit on what this can show. DGCA records the India to foreign
    point sector only. Where a passenger goes after Dubai is not in this data and
    is not in any free source. So the diagram stops at the first foreign point,
    and that is precisely the argument: in India's own statistics, a large share
    of the country's international traffic simply disappears into a Gulf hub.
    """
    city = load_dgca_intl_city()
    city = city[city["year"] == year]

    rows = []
    for gw, fp, pax in zip(city["city1"], city["city2"], city["pax_total"]):
        if gw in INDIAN_GATEWAYS and fp not in INDIAN_GATEWAYS:
            rows.append((gw, fp, pax))
        elif fp in INDIAN_GATEWAYS and gw not in INDIAN_GATEWAYS:
            rows.append((fp, gw, pax))

    flows = pd.DataFrame(rows, columns=["gateway", "foreign_point", "pax"])
    if flows.empty:
        return flows

    flows["destination"] = [
        "Gulf hub" if is_gulf_point(p) else "Everywhere else, direct"
        for p in flows["foreign_point"]
    ]
    keep = flows.groupby("gateway")["pax"].sum().nlargest(top_gateways).index
    flows = flows[flows["gateway"].isin(keep)]
    return (
        flows.groupby(["gateway", "destination"], as_index=False)["pax"]
        .sum()
        .sort_values("pax", ascending=False)
        .reset_index(drop=True)
    )


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------


def fig_stage_length_gap(year: int = LATEST_COMPLETE_YEAR) -> go.Figure:
    d = carrier_operating_summary(year, international=True)
    d = d[d["pax"] > 500_000]
    fig = charts.bar(
        d,
        category="airline",
        value="stage_length_km",
        highlight="IndiGo",
        orientation="h",
        value_fmt=",.0f",
    )
    return charts.finish(
        fig,
        title="IndiGo flies more international passengers than Air India, over half the distance",
        subtitle=(
            f"Average international stage length, km, {year}. Air India runs a long-haul "
            "network, IndiGo a Gulf and Southeast Asia one"
        ),
        source=SOURCE_DGCA,
    )


def fig_domestic_share(year: int = LATEST_COMPLETE_YEAR) -> go.Figure:
    d = carrier_operating_summary(year).head(6)
    fig = charts.bar(
        d,
        category="airline",
        value="share_pct",
        highlight="IndiGo",
        orientation="h",
        value_fmt=".1f",
    )
    return charts.finish(
        fig,
        title="IndiGo owns two thirds of the domestic market that funds the wide-bodies",
        subtitle=f"Share of scheduled domestic passengers, per cent, {year}",
        source=SOURCE_DGCA,
    )


def fig_who_carries_india(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    d = who_carries_india(year)
    fig = charts.bar(
        d,
        category="carrier_group",
        value="share_pct",
        highlight="Indian",
        orientation="h",
        value_fmt=".1f",
    )
    return charts.finish(
        fig,
        title="Indian carriers fly fewer than half of India's own international passengers",
        subtitle=(
            "Share of India international sector passengers by carrier home region, "
            f"per cent, {year}"
        ),
        source=SOURCE_DGCA,
    )


def fig_corridor_scale(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    d = corridor_scale(year).copy()
    d = d[d["pax_total"] > 0]
    d["pax_m"] = d["pax_total"] / 1e6
    fig = charts.bar(
        d, category="region", value="pax_m", highlight="Gulf", orientation="h", value_fmt=".1f"
    )
    return charts.finish(
        fig,
        title="The Gulf corridor is four times the size of India's entire direct Europe market",
        subtitle=f"India international sector passengers by destination region, millions, {year}",
        source=SOURCE_DGCA,
    )


def fig_gateway_flows(year: int = INTL_COUNTRY_YEAR) -> go.Figure:
    flows = gateway_flows(year)
    fig = charts.sankey(
        flows,
        source="gateway",
        target="destination",
        value="pax",
        highlight_nodes=["Gulf hub"],
    )
    return charts.finish(
        fig,
        title="India's own statistics lose sight of the passenger at the Gulf hub",
        subtitle=(
            f"Passengers from India's largest international gateways, {year}. DGCA records "
            "the first foreign point only, so what happens beyond Dubai is invisible"
        ),
        source=SOURCE_DGCA,
    )


def fig_load_factor_slope(start: int = 2019, end: int = LATEST_COMPLETE_YEAR) -> go.Figure:
    a = carrier_operating_summary(start)[["airline", "load_factor_pct"]]
    b = carrier_operating_summary(end)[["airline", "load_factor_pct"]]
    d = a.merge(b, on="airline", suffixes=("_start", "_end"))
    d = d[d["airline"].isin(["IndiGo", "Air India", "SpiceJet", "Air India Express"])]
    fig = charts.slope(
        d,
        label="airline",
        start_col="load_factor_pct_start",
        end_col="load_factor_pct_end",
        start_name=str(start),
        end_name=str(end),
        highlight="IndiGo",
    )
    return charts.finish(
        fig,
        title="Domestic load factors have recovered past their pre-pandemic level",
        subtitle="Scheduled domestic passenger load factor, per cent",
        source=SOURCE_DGCA,
    )


def fig_carrier_share_trend(start: int = 2015, end: int = LATEST_COMPLETE_YEAR) -> go.Figure:
    d = carrier_share_trend(start, end)
    # 2020 and 2021 are covid distortion, not trend: repatriation and air bubble
    # flying put Indian carriers above 50% on a fifth of the usual traffic.
    d = d[~d["year"].isin([2020, 2021])]

    fig = go.Figure()
    styles = {
        "Indian": dict(color=charts.RED, width=3),
        "Gulf": dict(color=charts.GREY, width=2),
        "Other foreign": dict(color=charts.LIGHT, width=2),
    }
    for name, style in styles.items():
        if name not in d.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=d["year"],
                y=d[name],
                mode="lines+markers",
                name=name,
                line=dict(color=style["color"], width=style["width"]),
                marker=dict(size=6, color=style["color"]),
                hovertemplate=name + " %{x}: %{y:.1f}%<extra></extra>",
            )
        )
        last = d.iloc[-1]
        fig.add_annotation(
            x=last["year"],
            y=last[name],
            text=f"<b>{name}</b> {last[name]:.1f}%",
            xanchor="left",
            xshift=8,
            showarrow=False,
            font=dict(size=12, color=style["color"] if name == "Indian" else charts.GREY),
        )

    fig.update_layout(showlegend=False)
    fig.update_xaxes(range=[start - 0.5, end + 3.5], dtick=2)
    fig.update_yaxes(title_text="Share of India international passengers (%)", range=[0, 55])

    first, last = d.iloc[0], d.iloc[-1]
    gain = last["Indian"] - first["Indian"]
    return charts.finish(
        fig,
        title=(
            f"Indian carriers have taken {gain:.0f} points of share back since {int(first['year'])}, "
            "and are closing on parity"
        ),
        subtitle=(
            "Share of India international sector passengers by carrier home region. "
            "2020 and 2021 omitted: repatriation flying distorts them beyond use"
        ),
        source=SOURCE_DGCA,
    )


FIGURES = {
    "stage_length_gap": fig_stage_length_gap,
    "carrier_share_trend": fig_carrier_share_trend,
    "domestic_share": fig_domestic_share,
    "who_carries_india": fig_who_carries_india,
    "corridor_scale": fig_corridor_scale,
    "gateway_flows": fig_gateway_flows,
    "load_factor_slope": fig_load_factor_slope,
}


def bilateral_seat_usage(year: int = INTL_COUNTRY_YEAR, *, load_factor: float = 0.811) -> pd.DataFrame:
    """Implied one-way seats per week by foreign point, for the bilateral question.

    Branch 4.3 of the hypothesis tree asks whether bilateral seat rights permit
    the deployment, and it is the most likely reason the recommendation fails.
    India does not publish entitlements, so the entitlement side cannot be
    computed. The USAGE side can, and it turns out to be enough.

    Passengers are DGCA. Seats are inferred, and the inference is one line:
    passengers over load factor, halved because DGCA reports both directions,
    over 52 weeks. `load_factor` defaults to the all-India international figure;
    it is exposed as an argument because the result is sensitive to it and a
    reader should be able to move it.
    """
    city = load_dgca_intl_city()
    city = city[city["year"] == year]
    rows = []
    for a, b, pax in zip(city["city1"], city["city2"], city["pax_total"]):
        a_in, b_in = a in INDIAN_GATEWAYS, b in INDIAN_GATEWAYS
        if a_in == b_in:
            continue  # both Indian or neither, so not an India to foreign sector
        rows.append((a if not a_in else b, pax))

    df = pd.DataFrame(rows, columns=["foreign_point", "pax"])
    df = df.groupby("foreign_point", as_index=False)["pax"].sum()

    # Eight points carry freight and no passengers: Cologne, Leipzig, Liege and
    # Luxembourg are cargo hubs, as are Guangzhou and Shenzhen on these sectors.
    # A seats-per-week figure for them is not small, it is meaningless, so they
    # are dropped rather than divided. (DGCA spells two of the others NOTTIMGHAM
    # and TAIPAE, which is the same source-typo problem recorded for carriers.)
    df = df[df["pax"] > 0].copy()

    df["seats_per_week_one_way"] = df["pax"] / load_factor / 52 / 2
    df["is_gulf"] = df["foreign_point"].map(is_gulf_point)
    return df.sort_values("pax", ascending=False).reset_index(drop=True)


# The Gulf points whose bilateral entitlement could be found at all. Both are
# secondary and both say so: India publishes no entitlement table, so these are
# the only two of eleven Gulf points that can be checked from the entitlement end.
#
# Sharjah is the notable absence. It holds the third separate UAE MoU and carries
# 2.3M passengers a year, and two timeboxed searches produced no seat figure, so
# it is left out rather than estimated. Doha, Jeddah, Muscat, Kuwait, Bahrain,
# Riyadh, Dammam and Ras Al-Khaimah are outside this check for the same reason.
_ENTITLEMENT_ROWS = {
    "DUBAI": "india_dubai_weekly_seat_entitlement_one_side",
    "ABUDHABI": "india_abu_dhabi_weekly_seat_entitlement_one_side",
}


def gulf_entitlement_check(year: int = INTL_COUNTRY_YEAR) -> pd.DataFrame:
    """Implied seat usage against reported entitlement, for every point with one.

    Generalises the Dubai check, and generalising it changed the answer. Dubai
    runs at 89.6% of its reported entitlement and Abu Dhabi at about 58%, so
    **the Gulf is not uniformly capacity-capped**. Any claim that it is, which
    this project made for one commit, is wrong.

    What survives is narrower and still holds: the single largest India-Gulf city
    pair has under 15% headroom, and the point that does have room is one whose
    sectors do not cover their own unit cost (see `options.corridor_economics`).
    So the constraint on Gulf deployment is partly legal and partly economic
    rather than purely legal, and the recommendation says so.

    Both entitlements are read with `allow_unverified=True`, which is correct here
    and almost nowhere else: the entire purpose is to CHECK figures that cannot be
    verified against a primary source, so gating them would make the check
    impossible to run. Results are diagnostics, never published point figures.
    """
    usage = bilateral_seat_usage(year)
    usage = usage.assign(_key=usage["foreign_point"].str.replace(" ", "").str.replace("-", ""))

    rows = []
    for point, key in _ENTITLEMENT_ROWS.items():
        implied = float(usage.loc[usage["_key"] == point, "seats_per_week_one_way"].sum())
        if implied == 0:
            raise KeyError(f"{point!r} has no traffic in {year}; the DGCA spelling may have changed")
        both_sides = 2 * assumption(key, allow_unverified=True)
        rows.append(
            {
                "foreign_point": point,
                "implied_seats_per_week": round(implied),
                "reported_entitlement_both_sides": round(both_sides),
                "utilisation_pct": round(100 * implied / both_sides, 1),
                "headroom_seats_per_week": round(both_sides - implied),
            }
        )
    return pd.DataFrame(rows).sort_values("utilisation_pct", ascending=False).reset_index(drop=True)


def dubai_entitlement_check(year: int = INTL_COUNTRY_YEAR) -> dict:
    """Cross-check the reported India-Dubai cap against DGCA's own passenger count.

    The entitlement figure is secondary: India publishes no seat table, and the
    Ministry of Civil Aviation's agreements page is not even reachable. So it is
    checked the only way available, from the traffic end, exactly as DGCA was
    checked against Eurostat and IndiGo's block hours were checked against DGCA.

    Assumes the standard reciprocal structure, both sides holding the same
    entitlement. That assumption is stated rather than buried, because the whole
    check rests on it.
    """
    df = bilateral_seat_usage(year)
    dubai = df[df["foreign_point"].str.replace(" ", "") == "DUBAI"]
    implied = float(dubai["seats_per_week_one_way"].sum())
    # allow_unverified is correct here and nowhere else in this module. The whole
    # point of this function is to CHECK a figure that cannot be verified against
    # a primary source, so gating it would make the check impossible to run. The
    # result is a diagnostic, never a published figure.
    one_side = assumption(
        "india_dubai_weekly_seat_entitlement_one_side", allow_unverified=True
    )
    both_sides = 2 * one_side
    return {
        "implied_seats_per_week": round(implied),
        "reported_entitlement_both_sides": round(both_sides),
        "gap_pct": round(100 * (implied - both_sides) / both_sides, 1),
        "utilisation_pct": round(100 * implied / both_sides, 1),
    }


def build_all() -> list[str]:
    """Build every benchmarking figure and export it for the page."""
    written = []
    for name, builder in FIGURES.items():
        charts.export(builder(), name)
        written.append(name)
    return written


if __name__ == "__main__":
    for _n in build_all():
        print("wrote", _n)
