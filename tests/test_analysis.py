"""Gates on the analysis layer and the chart builders.

Two jobs. First, the numbers the case argues from must keep coming out right.
Second, the house rules in charts.py must actually hold, because a rule that
lives only in a docstring is a rule that quietly stops being true.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src import benchmarking as bm
from src import charts
from src import market_sizing as ms


# --------------------------------------------------------------------------
# the numbers the case rests on
# --------------------------------------------------------------------------


def test_stage_length_gap_holds():
    d = bm.carrier_operating_summary(2025, international=True).set_index("airline")
    indigo, ai = d.loc["IndiGo"], d.loc["Air India"]

    assert indigo["pax"] > ai["pax"], "IndiGo should carry more international passengers"
    assert indigo["stage_length_km"] < ai["stage_length_km"] / 1.9, (
        "the stage length gap is the case; if it closes, the argument changes"
    )
    assert 2_500 < indigo["stage_length_km"] < 2_800
    assert 5_100 < ai["stage_length_km"] < 5_500


def test_shares_sum_to_one_hundred():
    for frame in (
        bm.carrier_operating_summary(2025),
        bm.carrier_operating_summary(2025, international=True),
        bm.who_carries_india(),
        bm.corridor_scale(),
    ):
        assert abs(frame["share_pct"].sum() - 100.0) < 0.01


def test_load_factors_are_percentages():
    d = bm.carrier_operating_summary(2025)
    assert d["load_factor_pct"].between(20, 100).all(), (
        "a load factor outside 20 to 100 means the units broke again"
    )


def test_indian_carriers_are_a_minority_of_india_international():
    d = bm.who_carries_india().set_index("carrier_group")
    assert d.loc["Indian", "share_pct"] < 50, "the premise of the case has changed"
    assert d.loc["Gulf", "share_pct"] > 20


def test_gulf_dwarfs_direct_europe():
    d = bm.corridor_scale().set_index("region")
    assert d.loc["Gulf", "pax_total"] > 3 * d.loc["Europe", "pax_total"]


def test_gateway_flows_are_well_formed():
    f = bm.gateway_flows()
    assert not f.empty
    assert set(f["destination"]) <= {"Gulf hub", "Everywhere else, direct"}
    assert (f["pax"] > 0).all()
    assert f["gateway"].nunique() <= 6
    # Kerala's Gulf labour corridor should be visible without being looked for.
    kochi = f[f["gateway"] == "KOCHI"].set_index("destination")["pax"]
    assert kochi["Gulf hub"] > kochi["Everywhere else, direct"]


# --------------------------------------------------------------------------
# the house rules in charts.py
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def built():
    return {name: builder() for name, builder in bm.FIGURES.items()}


def test_every_figure_states_a_takeaway_not_a_topic(built):
    """Titles must be sentences making a claim, not noun phrases naming a topic."""
    banned_starts = ("market share", "breakdown", "overview", "analysis of", "distribution")
    for name, fig in built.items():
        title = fig.layout.title.text or ""
        assert title, f"{name} has no title"
        headline = title.split("<br>")[0]
        assert len(headline.split()) >= 5, f"{name} title is too short to be a takeaway: {headline}"
        assert not headline.lower().startswith(banned_starts), f"{name} title names a topic"


def test_every_figure_carries_a_source(built):
    for name, fig in built.items():
        texts = [a.text or "" for a in fig.layout.annotations]
        assert any("Source:" in t for t in texts), f"{name} ships without provenance"


def _red_elements(fig) -> int:
    """Count the visually distinct things drawn in red.

    Counting red *properties* is wrong: a highlighted slope series carries a red
    line and red markers, which is one element wearing two red attributes. What
    the house rule cares about is how many things the eye is pulled to. So a
    trace using red anywhere counts once, except for a categorical colour list
    (a bar chart), where each red bar is its own element.
    """
    total = 0
    for trace in fig.data:
        color = getattr(getattr(trace, "marker", None), "color", None)
        if isinstance(color, (list, tuple)):
            total += sum(1 for c in color if c == charts.RED)
            continue
        line_color = getattr(getattr(trace, "line", None), "color", None)
        if color == charts.RED or line_color == charts.RED:
            total += 1
    return total


def test_one_red_element_per_chart(built):
    """The signal colour is spent once. Everything else is muted."""
    for name, fig in built.items():
        if name == "gateway_flows":
            continue  # sankey colours nodes and links together, checked separately
        reds = _red_elements(fig)
        assert reds <= 1, f"{name} spends the red on {reds} elements"


def test_the_red_rule_can_actually_fail():
    """A guard that cannot fail is not a guard.

    Highlighting two carriers must trip the rule, otherwise the test above is
    passing for the wrong reason.
    """
    df = pd.DataFrame({"k": ["a", "b", "c"], "v": [3.0, 2.0, 1.0]})
    greedy = charts.bar(df, category="k", value="v", highlight=["a", "b"])
    assert _red_elements(greedy) == 2


def test_modeled_badge_appears_only_when_asked():
    frame = pd.DataFrame({"k": ["a", "b"], "v": [1.0, 2.0]})
    title = "A claim long enough to count as a takeaway sentence"

    plain = charts.finish(
        charts.bar(frame, category="k", value="v"), title=title, source="test"
    )
    assert not any("MODELLED" in (a.text or "") for a in plain.layout.annotations)

    flagged = charts.finish(
        charts.bar(frame, category="k", value="v"), title=title, source="test", modeled=True
    )
    assert any("MODELLED" in (a.text or "") for a in flagged.layout.annotations)


# --------------------------------------------------------------------------
# the mekko fixes, since they were the point of adapting it
# --------------------------------------------------------------------------


def test_mekko_preaggregates_repeated_rows():
    """The Vizro original silently took element zero of a duplicated pair.

    Two rows for the same (category, subcategory) must sum, not be truncated.
    """
    split = pd.DataFrame(
        {
            "region": ["Gulf", "Gulf", "Europe", "Europe"],
            "carrier": ["Indian", "Indian", "Indian", "Foreign"],
            "pax": [10.0, 10.0, 5.0, 5.0],
        }
    )
    fig = charts.mekko(split, category="region", subcategory="carrier", values="pax")
    gulf_total = next(cd[1] for tr in fig.data for cd in tr.customdata if cd[0] == "Gulf")
    assert gulf_total == 20.0, "duplicate rows were truncated instead of summed"


def test_mekko_widths_are_normalised():
    df = pd.DataFrame(
        {"region": ["Gulf", "Europe"], "carrier": ["Indian", "Indian"], "pax": [75.0, 25.0]}
    )
    fig = charts.mekko(df, category="region", subcategory="carrier", values="pax")
    widths = list(fig.data[0].width)
    assert abs(sum(widths) - 1.0) < 1e-9
    assert abs(max(widths) - 0.75) < 1e-9


def test_mekko_rejects_empty_input():
    with pytest.raises(ValueError):
        charts.mekko(
            pd.DataFrame(columns=["a", "b", "c"]), category="a", subcategory="b", values="c"
        )


# --------------------------------------------------------------------------
# market sizing
# --------------------------------------------------------------------------


def test_trend_uses_the_slower_growth_rate():
    """The recovery CAGR is a rebound off a suppressed base, not a trend.

    Using it would roughly double the 2030 answer, so the choice is guarded.
    """
    e = ms.estimate_trend()
    a = e.assumptions
    assert a["rate_used"] == min(a["pre_covid_cagr"], a["post_covid_cagr"])
    assert a["post_covid_cagr"] > a["pre_covid_cagr"], (
        "if the recovery is no longer the faster rate, revisit which one to use"
    )


def test_income_elasticity_is_economically_plausible():
    slope, _, n = ms._propensity_curve()
    assert 0.5 < slope < 2.0, f"income elasticity of {slope:.2f} is not credible for air travel"
    assert n > 100, "too few peer observations to fit a curve on"


def test_capacity_method_is_blocked_while_inputs_are_unverified():
    """The gate must hold. An unverified fleet count cannot produce a sizing leg."""
    e = ms.estimate_capacity()
    assert not e.available
    assert e.blocked_reason and "DRAFT_UNVERIFIED" in e.blocked_reason


def test_band_is_a_range_not_an_average():
    tri = ms.triangulate()
    lo, hi = tri.band
    values = [e.value_m for e in tri.available]
    assert lo == min(values) and hi == max(values)
    assert tri.is_provisional, "capacity is still blocked, so the band must say provisional"
    # every estimate must exceed the base year, or growth has been modelled backwards
    assert all(v > tri.base_m for v in values)


def test_sizing_estimates_are_in_a_sane_range():
    tri = ms.triangulate()
    for e in tri.available:
        assert 80 < e.value_m < 200, f"{e.method} gives {e.value_m:.0f}M, which is not credible"


def test_sizing_figure_declares_it_is_provisional():
    fig = ms.fig_triangulation()
    text = (fig.layout.title.text or "").lower()
    assert "withheld" in text or "provisional" in text, (
        "a band missing a method must say so on the chart, not only in the logs"
    )


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------


def test_exported_json_is_loadable(tmp_path, monkeypatch):
    monkeypatch.setattr(charts, "CHART_DIR", tmp_path)
    path = charts.export(bm.fig_stage_length_gap(), "probe")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "data" in payload and "layout" in payload
    assert payload["data"], "figure exported with no traces"
