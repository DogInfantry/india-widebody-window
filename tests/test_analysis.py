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
from src import cargo as cg
from src import charts
from src import fleet_gap as fg
from src import market_sizing as ms
from src import options as opt
from src import profit_pools as pp
from src import scenario as sc


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


# Every module that publishes figures belongs here. A new analysis module whose
# charts are not in this tuple ships with NO house-rule coverage at all, and
# nothing else in the suite would notice: the export test only checks that the
# files exist, not that they obey the palette or carry a takeaway. That is how a
# module gets added and quietly skips every rule the repo claims to enforce.
PUBLISHING_MODULES = (bm, pp, fg, ms, opt, sc, cg)


@pytest.fixture(scope="module")
def built():
    """Every figure that publishes through a FIGURES map.

    The house rules are properties of the chart template, not of one module, so
    the fixture spans modules. Profit pools especially: it is the most heavily
    modelled module in the repo, which makes it the one most worth holding to the
    same title and palette discipline as everything else.
    """
    return {
        name: builder()
        for module in PUBLISHING_MODULES
        for name, builder in module.FIGURES.items()
    }


def test_every_publishing_module_is_covered_by_the_house_rules():
    """The fixture above must not fall behind the codebase.

    Written because it already had. `market_sizing` and `scenario` publish
    figures and were never in the fixture, so for the whole life of the project
    their charts were exempt from the one-red and takeaway-title rules that every
    other chart was held to. Discovering that by reading the fixture is luck;
    this makes it a failure.
    """
    import importlib
    import pkgutil

    import src

    publishing = set()
    for mod in pkgutil.iter_modules(src.__path__):
        module = importlib.import_module(f"src.{mod.name}")
        if isinstance(getattr(module, "FIGURES", None), dict):
            publishing.add(mod.name)

    covered = {m.__name__.rsplit(".", 1)[-1] for m in PUBLISHING_MODULES}
    missing = publishing - covered
    assert not missing, (
        f"these modules publish figures but are not in PUBLISHING_MODULES, so their "
        f"charts are exempt from every house rule: {sorted(missing)}"
    )


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


def test_capacity_leg_runs_now_that_every_input_is_verified():
    """All four capacity inputs are cleared, so the leg must produce a number.

    This test used to assert the opposite. It was inverted deliberately when the
    last input (utilisation) was sourced: the gate opening is the event worth
    guarding, because a silent regression to blocked would quietly drop a whole
    leg out of the band and nobody would see a failure.
    """
    e = ms.estimate_capacity()
    assert e.available, f"capacity leg went back to blocked: {e.blocked_reason}"
    assert e.blocked_reason is None
    # sanity, not a golden value: the leg must clear the base year and stay in
    # the same order of magnitude as the other two legs.
    assert 80 < e.value_m < 200


def test_widebody_seats_are_fleet_weighted_not_one_type_for_every_tail():
    """Counting all 140 aircraft at A350-900 seating understates the order book.

    The A350-1000 and the 777-9 are materially larger, so the weighted mean must
    land above the A350-900 figure. Guards against a revert to the flat count,
    which is an easy and invisible regression: it still produces a plausible
    number.
    """
    from src import data_pipeline as dp

    e = ms.estimate_capacity()
    mean_seats = e.assumptions["mean_seats_per_widebody"]
    assert mean_seats > dp.assumption("widebody_seats_a350_900"), (
        "weighted mean is at or below the A350-900 count, so the mix is not being applied"
    )
    # every variant in the table must contribute, or a row has silently dropped
    assert set(e.assumptions["widebody_seats_by_variant"]) == {
        row[1] for row in ms._ORDER_BOOK
    }


def test_order_book_variant_table_reconciles_to_the_assumption_rows():
    """The mix and the headline counts are maintained separately, so they drift.

    This is the guard that catches it. Perturbing the table must block the leg
    rather than quietly resize the fleet.
    """
    from src import data_pipeline as dp

    booked = sum(row[2] for row in ms._ORDER_BOOK)
    dp_total = dp.assumption("air_india_widebody_on_order") + dp.assumption(
        "indigo_a350_on_order"
    )
    assert booked == dp_total

    original = ms._ORDER_BOOK
    try:
        ms._ORDER_BOOK = original[:-1]  # drop the 777-9 line
        blocked = ms.estimate_capacity()
        assert not blocked.available
        assert "order book mismatch" in blocked.blocked_reason
    finally:
        ms._ORDER_BOOK = original
    assert ms.estimate_capacity().available, "guard did not restore cleanly"


def test_capacity_assumptions_reach_the_chart_face():
    """Stated assumptions belong on the chart, not in a footnote or the logs."""
    text = ms.fig_triangulation().layout.title.text.lower()
    assert "owned fleet" in text, "utilisation basis is missing from the chart face"
    assert "variant assumed" in text, "assumed variants are missing from the chart face"


def test_assumption_gate_still_bites_on_unverified_rows():
    """The gate itself must keep working after the capacity rows were cleared.

    Clearing rows is exactly when a broken gate stops being visible, so this
    pins the mechanism to a row that is still, and may permanently remain,
    unverifiable: Air India files no results, so its yield has no primary source.
    """
    from src import data_pipeline as dp

    with pytest.raises(dp.UnverifiedAssumption):
        dp.assumption("air_india_yield_inr_per_rpk")


def test_band_is_a_range_not_an_average():
    tri = ms.triangulate()
    lo, hi = tri.band
    values = [e.value_m for e in tri.available]
    assert lo == min(values) and hi == max(values)
    assert not tri.is_provisional, "all three legs are live, so the band is no longer provisional"
    assert len(values) == 3, "the band must now carry all three methods"
    # every estimate must exceed the base year, or growth has been modelled backwards
    assert all(v > tri.base_m for v in values)


def test_sizing_estimates_are_in_a_sane_range():
    tri = ms.triangulate()
    for e in tri.available:
        assert 80 < e.value_m < 200, f"{e.method} gives {e.value_m:.0f}M, which is not credible"


def test_sizing_figure_no_longer_claims_to_be_provisional():
    """The inverse of the old test, and the reason it had to be inverted.

    A chart that still says provisional after the missing leg landed is lying in
    the safe direction, which is still lying. The provisional wording must
    disappear exactly when the third method starts contributing.
    """
    fig = ms.fig_triangulation()
    text = (fig.layout.title.text or "").lower()
    assert not ms.triangulate().is_provisional
    assert "withheld" not in text and "provisional" not in text, (
        f"band is complete but the chart still hedges: {text}"
    )


# --------------------------------------------------------------------------
# scenarios
# --------------------------------------------------------------------------


def test_scenarios_are_strictly_ordered():
    """Bear < Base < Bull.

    Guards a bug that already happened: the bear rate was rolled over a window
    as long as the block it searched, so exactly one stretch qualified and the
    bear case came out identical to the base by construction.
    """
    rates = {s.name: s.cagr for s in sc.scenarios()}
    assert rates["Bear"] < rates["Base"] < rates["Bull"], rates
    assert rates["Bear"] != rates["Base"], "bear collapsed onto base again"


def test_bull_is_capped_by_physical_capacity():
    rates = {s.name: s.cagr for s in sc.scenarios()}
    assert rates["Bull"] <= sc.BULL_CAP + 1e-9


def test_every_scenario_grows_from_the_base_year():
    t = sc.scenario_table().set_index("scenario")
    assert (t["growth_vs_base_year_pct"] > 0).all()
    assert t.loc["Bull", "pax_2030_m"] > t.loc["Base", "pax_2030_m"] > t.loc["Bear", "pax_2030_m"]


def test_scenario_paths_start_at_the_observed_base():
    paths = sc.scenario_paths()
    start = paths[paths["year"] == ms.BASE_YEAR]
    assert start["pax_m"].nunique() == 1, "all scenarios must start from the same actual value"

    # Compared against the observed series rather than a literal. The literal was
    # 72.2, which pinned the test to a data vintage instead of to the property it
    # is named for, and it was the only thing in the suite that broke when the
    # base year moved from 2024 to 2025.
    observed = float(ms._annual_international()[ms.BASE_YEAR]) / 1e6
    assert abs(start["pax_m"].iloc[0] - observed) < 0.01


def test_scenario_figure_points_at_the_levers_it_does_not_carry():
    """Inverted when the fuel and FX levers were built.

    This asserted the chart admits the levers are missing. They are no longer
    missing, but they still do not belong on the demand paths, so the chart must
    now say where they DID go instead of claiming they are absent. A chart that
    keeps apologising for something already delivered is as stale as one that
    hides a gap.
    """
    text = (sc.fig_scenarios().layout.title.text or "").lower()
    assert "fuel" in text and "separately" in text
    assert "gated" not in text, "the demand chart still claims the levers are blocked"


def test_all_three_lever_families_are_built():
    """The plan promised demand, fuel and FX. Pin that all three now exist."""
    assert {"scenarios", "cask_bridge", "fuel_fx_sensitivity"} <= set(sc.FIGURES)


# --------------------------------------------------------------------------
# export
# --------------------------------------------------------------------------


def test_exported_json_is_loadable(tmp_path, monkeypatch):
    monkeypatch.setattr(charts, "CHART_DIR", tmp_path)
    path = charts.export(bm.fig_stage_length_gap(), "probe")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "data" in payload and "layout" in payload
    assert payload["data"], "figure exported with no traces"


# --------------------------------------------------------------------------
# profit pools, the most heavily modelled module in the repo
# --------------------------------------------------------------------------


def test_gulf_share_falls_when_weighted_by_distance():
    """The finding the module exists for. If it inverts, the case changed."""
    gap = pp.gulf_share_gap()
    assert gap["pax_share_pct"] > 50, "Gulf should still be over half of passengers"
    assert gap["revenue_share_pct"] < gap["pax_share_pct"], (
        "distance weighting must reduce the Gulf's share, or the stage lengths are wrong"
    )
    assert gap["gap_pts"] > 10, "the gap is the argument; under 10 points it stops carrying it"


def test_reference_distances_are_physically_sane():
    """Great circle from Delhi, so these are checkable against an atlas."""
    d = pp.corridor_stage_lengths().set_index("region")["stage_km"]
    assert 2_000 < d["Gulf"] < 2_500, f"Delhi to Dubai came out at {d['Gulf']} km"
    assert 11_000 < d["North America"] < 12_500, f"Delhi to New York at {d['North America']} km"
    assert d["Gulf"] < d["Southeast Asia"] < d["Europe"] < d["North America"]


def test_modelled_margins_are_anchored_to_the_verified_ebitdar_margin():
    """The anchor must survive the margin model, or the model is unanchored."""
    from src import data_pipeline as dp

    df = pp.profit_pool()
    anchor = 100 * (
        dp.assumption("indigo_operating_profit_fy2026_inr_cr")
        / dp.assumption("indigo_revenue_fy2026_inr_cr")
    )
    weighted = (df["margin_pct"] * df["revenue_inr_cr"]).sum() / df["revenue_inr_cr"].sum()
    assert abs(weighted - anchor) < 1e-6, (
        f"revenue-weighted margin {weighted:.3f} drifted from the anchor {anchor:.3f}"
    )
    assert (df["margin_pct"] > 0).all(), "a negative modelled margin needs an argument, not a knob"


def test_the_finding_survives_the_margin_knob():
    """A conclusion that only holds at one setting of a modelled parameter is not a
    conclusion. The Gulf's profit share must stay well under its passenger share
    across the whole plausible range."""
    s = pp.sensitivity()
    assert len(s) == 3
    assert (s["gulf_profit_share_pct"] < 40).all(), (
        "Gulf profit share should stay far below its 52 percent passenger share"
    )
    # turning the knob must actually move something, or it is not the knob
    assert s["gulf_profit_share_pct"].nunique() > 1


def test_sensitivity_restores_the_module_constant():
    """sensitivity() mutates a module global. It must put it back."""
    before = pp.MARGIN_STAGE_SENSITIVITY
    pp.sensitivity()
    assert pp.MARGIN_STAGE_SENSITIVITY == before


def test_profit_pool_charts_carry_the_modelled_badge():
    """House rule: modelled numbers are labelled on the chart face."""
    for name, builder in pp.FIGURES.items():
        fig = builder()
        assert any("MODELLED" in (a.text or "") for a in fig.layout.annotations), (
            f"{name} carries modelled numbers without the badge"
        )


def test_excluded_residual_region_is_not_silently_dropped():
    """'Other' is excluded deliberately; the module must say so, not just omit it."""
    assert "Other" in pp.EXCLUDED_REGIONS
    assert "Other" not in set(pp.profit_pool()["region"])
    assert "Excludes" in pp.gulf_share_gap()["note"]


def test_every_chart_the_page_asks_for_has_been_exported():
    """The page and the pipeline are a contract, and nothing enforced it.

    `docs/index.html` names charts by `data-chart`; `scripts/refresh.py` writes
    them. A step referencing a chart nobody builds renders as an empty box on the
    live site, which is exactly the failure a reader would notice first and a test
    run would not.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    wanted = set(re.findall(r'data-chart="([^"]+)"', html))
    assert wanted, "no data-chart attributes found, the selector has changed"

    have = {p.stem for p in (root / "docs" / "assets" / "charts").glob("*.json")}
    assert wanted <= have, f"page asks for charts that were never exported: {sorted(wanted - have)}"


# --------------------------------------------------------------------------
# fuel and FX levers
# --------------------------------------------------------------------------


def test_unit_cost_decomposition_reconciles_to_published_cask():
    """Three parts, each a difference of verified rows, must sum to the total."""
    from src import data_pipeline as dp

    u = sc.unit_economics()
    assert abs(u["inr_per_ask"].sum() - dp.assumption("indigo_cask_inr_per_ask_fy2026")) < 1e-9
    assert abs(u["share_pct"].sum() - 100) < 1e-9
    assert (u["inr_per_ask"] > 0).all()


def test_cask_bridge_closes_exactly():
    """A bridge that does not close is a bar chart with arrows on it."""
    from src import data_pipeline as dp

    b = sc.cask_bridge().set_index("step")["inr_per_ask"]
    walked = b["FY2025 CASK"] + b["Fuel"] + b["Real non-fuel"] + b["Currency"]
    assert abs(walked - b["FY2026 CASK"]) < 1e-9, f"bridge lands at {walked}, not {b['FY2026 CASK']}"
    assert abs(b["FY2025 CASK"] - dp.assumption("indigo_cask_fy2025_inr_per_ask")) < 1e-9


def test_currency_exceeds_the_net_cask_increase():
    """The finding. Fuel fell, so currency is larger than the whole net rise."""
    b = sc.cask_bridge().set_index("step")["inr_per_ask"]
    net = b["FY2026 CASK"] - b["FY2025 CASK"]
    assert b["Fuel"] < 0, "fuel is supposed to have fallen; if it rose the story changes"
    assert b["Currency"] > net > 0
    assert abs(b["Real non-fuel"]) < abs(b["Currency"]), (
        "real cost inflation should be small against the currency effect"
    )


def test_dollar_exposure_is_a_band_not_a_point():
    """DGCA publishes no fuel split by sector type, so a midpoint would be invented."""
    e = sc.dollar_exposure()
    assert e["floor_inr_per_ask"] < e["ceiling_inr_per_ask"]
    assert 0 < e["floor_pct_of_cask"] < e["ceiling_pct_of_cask"] < 100


def test_fx_bites_harder_than_fuel_at_the_same_move():
    """Titles claim it, so it has to hold. More of unit cost is dollar linked at
    the ceiling than is fuel, so an equal percentage move in the rupee costs more."""
    s = sc.fuel_fx_sensitivity().set_index("move_pct")
    assert s.loc[10.0, "cask_fx_shock_ceiling"] > s.loc[10.0, "cask_fuel_shock"]
    assert s.loc[-10.0, "cask_fx_shock_ceiling"] < s.loc[-10.0, "cask_fuel_shock"]


def test_unshocked_case_reproduces_actual_cask():
    """A zero shock must return the published number, or the lever has an offset."""
    from src import data_pipeline as dp

    z = sc.cost_under_shock()
    cask = dp.assumption("indigo_cask_inr_per_ask_fy2026")
    assert (z["cask_inr_per_ask"].sub(cask).abs() < 1e-9).all()


def test_fy2026_opens_below_breakeven():
    """CASK 5.00 against RASK 4.99. If this inverts, several titles are wrong."""
    from src import data_pipeline as dp

    assert dp.assumption("indigo_cask_inr_per_ask_fy2026") > dp.assumption(
        "indigo_rask_inr_per_ask_fy2026"
    )


# --------------------------------------------------------------------------
# Gulf point matching, and the bilateral constraint
# --------------------------------------------------------------------------


def test_every_gulf_point_literal_matches_a_real_dgca_name():
    """The bug this test exists for hid 5.0M passengers in a published chart.

    GULF_POINTS held "ABU DHABI" and "RAS AL KHAIMAH"; DGCA writes "ABUDHABI"
    and "RAS AL-KHAIMAH". Exact matching missed both, so the Gulf-hub Sankey
    understated the corridor by 20%. Nothing failed, because a wrong bucket is
    still a valid bucket. This asserts every literal actually resolves.
    """
    from src import data_pipeline as dp

    city = dp.load_dgca_intl_city()
    city = city[city["year"] == bm.INTL_COUNTRY_YEAR]
    points = set(city["city1"]) | set(city["city2"])
    keys = {bm._norm_point(p) for p in points}

    unmatched = [g for g in bm.GULF_POINTS if bm._norm_point(g) not in keys]
    assert not unmatched, f"GULF_POINTS entries that match no DGCA city: {unmatched}"


def test_gulf_matching_survives_spacing_and_hyphen_variants():
    for variant in ("ABUDHABI", "ABU DHABI", "abu dhabi", "RAS AL-KHAIMAH", "RAS AL KHAIMAH"):
        assert bm.is_gulf_point(variant), f"{variant} should be a Gulf point"
    for other in ("LONDON", "SINGAPORE", "NEW YORK"):
        assert not bm.is_gulf_point(other)


def test_abu_dhabi_is_counted_as_a_gulf_hub():
    """Regression pin for the specific 5.7M that was misfiled."""
    flows = bm.gateway_flows()
    gulf = flows[flows["destination"] == "Gulf hub"]["pax"].sum()
    assert gulf > 24_000_000, "Gulf hub flow collapsed, Abu Dhabi may be misfiled again"


def test_bilateral_seat_usage_excludes_foreign_to_foreign_sectors():
    """A sector with neither end in India is not an India bilateral."""
    d = bm.bilateral_seat_usage()
    assert not d.empty
    assert (d["seats_per_week_one_way"] > 0).all()
    assert "DUBAI" in set(d["foreign_point"])
    # no Indian gateway should appear as a foreign point
    assert not (set(d["foreign_point"]) & bm.INDIAN_GATEWAYS)


def test_dubai_runs_close_to_its_reported_bilateral_entitlement():
    """The corroboration, and the answer to hypothesis branch 4.3.

    India publishes no entitlement table, so the reported cap is secondary. It is
    checked from the traffic end instead. If these two diverge badly, either the
    reported figure is wrong or the seat inference is.
    """
    c = bm.dubai_entitlement_check()
    assert 70 < c["utilisation_pct"] < 110, (
        f"implied usage is {c['utilisation_pct']}% of the reported entitlement, "
        "which is too far off to corroborate either number"
    )


# --------------------------------------------------------------------------
# fleet gap: what the order book can fly against what the market asks for
# --------------------------------------------------------------------------


def test_baseline_is_measured_not_modelled():
    """Every field on the baseline must reproduce from DGCA columns directly."""
    b = fg.baseline()
    ops = fg._international_operating(b.year)

    assert b.pax == pytest.approx(ops["pax"].sum())
    assert b.ask == pytest.approx(ops["ask"].sum())
    assert b.stage_km == pytest.approx(ops["rpk"].sum() / ops["pax"].sum())
    # sanity, not tautology: these are the published findings
    assert 3_000 < b.stage_km < 4_000
    assert 0.75 < b.load_factor < 0.90


def test_block_speed_is_computed_and_rises_with_stage_length():
    """Block speed comes from aircraft_km over aircraft_hours, never assumed.

    Taxi, climb and descent are a larger share of a short sector, so a long-haul
    network must block faster than a short-haul one. Air India averages 5,316 km
    and IndiGo 2,643 km, so Air India must come out faster. If this inverts, the
    two columns are not measuring what this module thinks they are.
    """
    ops = fg._international_operating(fg.LATEST_COMPLETE_YEAR).set_index("airline")
    ai, indigo = ops.loc["Air India"], ops.loc["IndiGo"]

    assert ai["stage_km"] > indigo["stage_km"]
    assert ai["block_speed_kmh"] > indigo["block_speed_kmh"]
    # a jet transport blocks somewhere in this range or a column is misread
    for airline, row in ops.iterrows():
        assert 500 < row["block_speed_kmh"] < 950, f"{airline} blocks at {row['block_speed_kmh']:.0f} km/h"


def test_order_book_ask_reconciles_to_the_capacity_sizing_leg():
    """Two modules, two routes, one quantity. They must not drift apart.

    `market_sizing.estimate_capacity` multiplies seats by cycles per year and a
    load factor to get passengers. `fleet_gap.order_book_ask` multiplies the same
    seats by block speed and utilisation to get kilometres. Cycles times sector
    length IS kilometres, so the two are the same number wearing different units:

        ask == (added_pax / load_factor) * block_hours * block_speed

    This is the drift guard. If someone changes the seat table, the utilisation
    row or the block-hours constant in one module only, this fails rather than
    the site quietly carrying two different capacity stories.

    Tolerance is 1e-4 rather than exact for one reason worth naming: the sizing
    leg publishes `observed_intl_load_factor` rounded to four decimal places, and
    the reconciliation runs back through that published figure deliberately, so
    it checks what the module actually reports rather than an internal it happens
    to share. The residual is that rounding and nothing else, about 0.002%.
    """
    cap = ms.estimate_capacity()
    assert cap.available, f"capacity leg is blocked: {cap.blocked_reason}"

    base_pax = float(ms._annual_international()[ms.BASE_YEAR])
    added_pax = cap.value_m * 1e6 - base_pax

    book = fg.order_book_ask()
    implied = (
        added_pax
        / cap.assumptions["observed_intl_load_factor"]
        * cap.assumptions["assumed_block_hours"]
        * book["block_speed_kmh"]
    )
    assert book["ask"] == pytest.approx(implied, rel=1e-4)


def test_the_sizing_leg_assumes_a_long_haul_sector_without_saying_so():
    """Surfaced by the reconciliation above, and worth pinning.

    7.5 block hours at the wide-body block speed is a sector of roughly 5,200 km,
    which is Air India's network, not IndiGo's 2,643 km one. The capacity leg has
    always assumed these aircraft fly long-haul. That is a defensible assumption
    and it is now an explicit one.
    """
    book = fg.order_book_ask()
    assert 4_500 < book["implied_sector_km"] < 6_000
    assert book["implied_sector_km"] > fg.baseline().stage_km


def test_order_book_seats_come_from_the_shared_variant_table():
    """One seat total in the repo, not two."""
    seats, _ = ms._widebody_seats()
    assert fg.order_book_ask()["seats"] == pytest.approx(seats)


def test_demand_path_is_calibrated_to_the_observed_baseline():
    """The model must start from what happened, not from where the curve says.

    Without the calibration the first modelled year lands about 2.6% below the
    observed 36.4M, which would show a capacity surplus before a single aircraft
    arrived. An artefact of anchoring, not a finding.
    """
    b = fg.baseline()
    path = fg.indian_carrier_pax_path().set_index("year")
    assert path.loc[b.year, "pax"] == pytest.approx(b.pax, rel=1e-9)
    # and the gap must therefore open at exactly zero
    first = fg.gap_path().iloc[0]
    assert first["year"] == b.year
    assert first["gap_bn"] == pytest.approx(0.0, abs=1e-6)


def test_the_order_book_exceeds_what_holding_share_requires():
    """The finding this module exists to produce.

    If this ever falls below 1.0 the recommendation changes completely: the
    aircraft would be needed just to carry existing traffic, and the argument
    about flying it further would be unnecessary.
    """
    s = fg.absorption_summary()
    assert s["book_vs_growth_ratio"] > 1.0, (
        "the order book no longer exceeds the capacity needed to hold share, "
        "so the case for lengthening the network is no longer the binding one"
    )
    assert s["surplus_bn"] > 0
    assert s["stage_uplift_pct"] > 0
    assert s["share_pct_to_absorb"] > 100 * fg.current_share()


def test_absorption_frontier_trades_share_against_sector_length():
    """Carry more of the market, or carry it further. The curve must slope down."""
    df = fg.absorption_frontier()
    assert df["required_stage_km"].is_monotonic_decreasing
    # the frontier is the ASK identity, so every point must reproduce it
    base = fg.baseline()
    available = base.ask + fg.order_book_ask()["ask"]
    for _, row in df.iterrows():
        assert fg.ask_required(
            row["pax_m"] * 1e6, row["required_stage_km"], base.load_factor
        ) == pytest.approx(available, rel=1e-9)


def test_delivery_slip_only_moves_when_capacity_lands():
    """Later deliveries must never mean more capacity in any year."""
    band = fg.gap_band()
    wide = band.pivot(index="year", columns="first_delivery_year", values="ask_available_bn")
    starts = sorted(wide.columns)
    for earlier, later in zip(starts, starts[1:]):
        assert (wide[earlier] >= wide[later] - 1e-9).all(), (
            f"deliveries from {later} produce more capacity than from {earlier}"
        )
    # and the total book delivered is identical, only the timing differs
    assert band.groupby("first_delivery_year")["ask_needed_bn"].nunique().nunique() == 1


def test_the_gap_is_worst_in_the_bridge_years():
    """The shape that motivates phasing: a gap opens, then deliveries close it."""
    path = fg.gap_path(first_delivery_year=2028).set_index("year")
    peak_year = int(path["gap_bn"].idxmax())
    assert 2026 <= peak_year <= 2028, f"gap peaks in {peak_year}, not the bridge era"
    # it must actually close by the target year, or the order book is undersized
    assert path["gap_bn"].iloc[-1] < path["gap_bn"].max()


def test_delivery_start_year_is_never_asserted_as_fact():
    """No primary source gives one, so the module must not carry one as a default fact.

    The Airbus release confirming the 60 firm A350s states no delivery schedule,
    and one attempt to source it found nothing. It may appear as a scenario input
    and must be visible as such on the chart.
    """
    text = (fg.fig_fleet_gap().layout.title.text or "").lower()
    assert "scenario input" in text or "never asserted" in text


def test_fleet_gap_and_the_sizing_leg_do_not_contradict_each_other():
    """Two statements that look opposed, pinned so they stay reconciled.

    Branch 4.2 of the hypothesis tree says the order book does not overshoot
    demand. This module says it is roughly twice what holding share requires.
    Both hold because they divide by different denominators: the whole market's
    growth in one case, Indian carriers' share of that growth in the other.

    If the ratio between them ever stops tracking the carrier share, one of the
    two has silently changed basis.
    """
    cap = ms.estimate_capacity()
    base_pax = float(ms._annual_international()[ms.BASE_YEAR])
    book_pax = cap.value_m * 1e6 - base_pax

    # the whole market's growth to the trend case
    trend = ms.estimate_trend()
    market_growth = trend.value_m * 1e6 - base_pax
    assert book_pax < market_growth, "the book now overshoots the whole market, 4.2 has changed"

    # and the same book against one carrier group's share of that growth
    s = fg.absorption_summary()
    assert s["book_vs_growth_ratio"] > 1.0

    # the two ratios must differ by roughly the carrier share, which is what makes
    # them consistent rather than contradictory
    assert (book_pax / market_growth) < 1.0
    assert (book_pax / market_growth) / fg.current_share() > 1.0


# --------------------------------------------------------------------------
# options: which way to add capacity, and what each needs to be true
# --------------------------------------------------------------------------


def test_unit_cost_falls_with_sector_length():
    """The shape the whole module rests on. If this inverts, the elasticity sign is wrong."""
    stages = [1_000, 2_500, 5_000, 10_000]
    casks = [opt.cask_at_stage(d) for d in stages]
    assert casks == sorted(casks, reverse=True)
    # and it must pass through the published figure at the published sector
    ref = opt.reference()
    assert opt.cask_at_stage(ref.stage_km) == pytest.approx(ref.cask)


def test_the_cost_reference_is_the_system_network_not_the_international_one():
    """CASK is a system figure, so its sector length must be the system one.

    Anchoring at IndiGo's 2,643 km international stage would price its domestic
    flying as long-haul and shift every corridor's cost down with it.
    """
    ref = opt.reference()
    intl = bm.carrier_operating_summary(2025, international=True).set_index("airline")
    assert ref.stage_km < intl.loc["IndiGo", "stage_length_km"]
    assert 900 < ref.stage_km < 1_500


def test_the_gulf_has_the_least_yield_headroom():
    """The finding, and it cuts against the headline recommendation.

    Short sectors keep unit cost high, so the Gulf can absorb the least yield
    erosion of any corridor. That does not overturn "Gulf first", but it does mean
    the Gulf case rests on volume, bilateral position and the connect premium
    rather than on unit economics, and the write-up has to say so.
    """
    df = opt.corridor_economics().set_index("region")
    assert df["yield_headroom_pct"].idxmin() == "Gulf"
    assert df.loc["Gulf", "yield_headroom_pct"] < df.loc["Europe", "yield_headroom_pct"]
    assert df.loc["Gulf", "yield_headroom_pct"] < df.loc["North America", "yield_headroom_pct"]


def test_the_finding_survives_the_one_knob():
    """Turning the elasticity across its plausible range must not flip the ordering.

    Mirrors the equivalent guard on the profit pool's margin knob. If the answer
    only holds at one exponent, it is the exponent talking, not the data.
    """
    s = opt.sensitivity()
    assert s["gulf_is_tightest"].all(), (
        "the Gulf stops being the tightest corridor somewhere in the plausible "
        "elasticity range, so the finding is an artefact of the knob"
    )
    # headroom must widen with distance at every setting
    for e in s["elasticity"]:
        df = opt.corridor_economics(elasticity=float(e))
        assert df.sort_values("stage_km")["yield_headroom_pct"].is_monotonic_increasing


def test_sensitivity_does_not_mutate_the_module_constant():
    """The knob is passed as an argument, never swapped in and out of a global.

    `profit_pools.sensitivity` mutates a module global and restores it in a
    finally block, which works but is one exception away from leaving the repo in
    a state where every later figure is built on the wrong number. This one takes
    a parameter instead, and this test pins that difference.
    """
    before = opt.CASK_STAGE_ELASTICITY
    opt.sensitivity()
    assert opt.CASK_STAGE_ELASTICITY == before


def test_narrowbody_reach_excludes_north_america_and_includes_europe():
    """Computed from the verified A321XLR range against computed stage lengths."""
    df = opt.corridor_economics().set_index("region")
    assert not df.loc["North America", "reachable_by_narrowbody"]
    assert not df.loc["Oceania", "reachable_by_narrowbody"]
    assert df.loc["Europe", "reachable_by_narrowbody"]
    assert df.loc["Gulf", "reachable_by_narrowbody"]


def test_value_at_stake_is_a_band_never_a_point():
    """Bounded by the only two yields this project has verified.

    The width of the band must be exactly the ratio of those two yields and
    nothing else, which is what makes it a bound rather than an estimate.
    Tolerance is 1e-4 because the reported figures are rounded to whole crore.
    """
    from src import data_pipeline as dp

    v = opt.value_at_stake()
    assert v["revenue_ceiling_inr_cr"] > v["revenue_floor_inr_cr"]
    lo = dp.assumption("indigo_yield_inr_per_rpk_fy2026")
    hi = dp.assumption("gulf_carrier_yield_inr_per_rpk")
    assert hi > lo, "the band has inverted, so one of the two yields has changed basis"
    assert v["revenue_ceiling_inr_cr"] / v["revenue_floor_inr_cr"] == pytest.approx(hi / lo, rel=1e-4)


def test_the_connect_gap_is_the_difference_between_two_measures():
    """Sector share is computed from DGCA; the Gulf six O-D share is not published."""
    g = opt.connect_gap()
    assert g["gap_pts"] == pytest.approx(g["sector_share_pct"] - g["od_share_pct"], abs=0.05)
    assert 8 < g["gap_pts"] < 15, "the connect gap has moved outside the range the case argues"


def test_the_od_share_cannot_reach_a_published_figure_through_the_gate():
    """`gulf_od_share_pct` must stay refused unless a caller opts in explicitly.

    It was carried as a hard number on the live page with no row here at all,
    which is how it escaped the gate for the life of the project.

    **INVERTED 2026-08-19, rather than deleted.** The old docstring said to invert
    this "if IATA ever publishes a free origin-destination table". IATA does, and
    did all along: `Aviation in India` is free and machine readable and its
    section 3.2 gives the region and country split. So the half of this test that
    guarded a claim about IATA is now the second assertion, which requires those
    published figures to CLEAR the gate.

    The first assertion survives, for a narrower and now correct reason: IATA's
    region "Middle East" is wider than this repo's Gulf six, so no published
    figure is this row's quantity. The gate still has to bite on the row itself.
    """
    from src import data_pipeline as dp

    with pytest.raises(dp.UnverifiedAssumption):
        dp.assumption("gulf_od_share_pct")
    assert dp.assumption("gulf_od_share_pct", allow_unverified=True) > 0

    # The inversion: what IATA does publish must pass the gate with no opt-in.
    for key in (
        "iata_india_od_middle_east_share_pct",
        "iata_india_od_uae_share_pct",
        "iata_india_od_middle_east_pax_m",
        "iata_india_od_uae_pax_m",
    ):
        assert dp.assumption(key) > 0, f"{key} should clear the gate on its own"


def test_dgca_and_iata_agree_on_departures_and_disagree_on_destinations():
    """The Gulf equivalent of the DGCA-to-Eurostat check, and the shape is the finding.

    Two agencies, opposite methodologies, one controlled comparison. They agree
    closely on how many passengers leave India and disagree sharply on where
    those passengers are going. The disagreement is the connecting traffic, which
    is the spine of the recommendation, and until now it was modelled off a figure
    that circulated in trade press without a primary table.

    Direction and year are controlled, per IATA's own footnote 5: DGCA is read on
    `pax_from_india` rather than `pax_total`, and on 2024 rather than
    INTL_COUNTRY_YEAR. The third difference IATA names, segment counting against
    O-D journeys, is the quantity being measured and so is left in.
    """
    r = opt.od_reconciliation()

    # They agree on the total. Anything much wider and the comparison is unsound.
    assert r["total_divergence_pct"] < 6.0, (
        "DGCA and IATA no longer agree on how many passengers leave India, so the "
        "destination comparison below cannot be trusted"
    )

    # They disagree on the destination, and the sign must be this way round:
    # sector counting attributes the connecting passenger to the hub.
    assert r["uae_dgca_share_pct"] > r["uae_iata_share_pct"]
    assert r["uae_leak_m"] > 0
    assert r["gulf_leak_m_lower_bound"] > 0


def test_the_measured_gulf_leak_corroborates_the_modelled_connect_gap():
    """The project's most load-bearing modelled number, checked against measurement.

    `connect_gap` models 8.5M connecting passengers from a trade-press O-D share.
    `od_reconciliation` measures a LOWER bound of the same quantity from two
    published sources. Doubling the measured one-way bound for direction should
    land under the modelled figure and not far under it: much below and the model
    is inflated, above and the model is impossible.

    This is the check `docs/recommendation.md` said could not be run.
    """
    modelled = opt.connect_gap()["connecting_pax_m"]
    measured_lower_bound = opt.od_reconciliation()["gulf_leak_m_lower_bound"] * 2

    assert measured_lower_bound <= modelled * 1.05, (
        f"measured lower bound {measured_lower_bound:.2f}M exceeds the modelled "
        f"{modelled:.2f}M, so the model understates a floor it cannot understate"
    )
    assert measured_lower_bound > modelled * 0.75, (
        f"measured lower bound {measured_lower_bound:.2f}M has fallen well below the "
        f"modelled {modelled:.2f}M; the model may be inflated"
    )


def test_options_and_profit_pools_agree_on_the_corridor_ordering():
    """Two unrelated models, one shape. That is the point of building both.

    `profit_pools` models margin rising with stage length off an EBITDAR anchor.
    `options` derives cost headroom from published unit costs and a cost
    elasticity. They share no input beyond the corridor stage lengths, so
    agreeing on the ordering is corroboration rather than arithmetic.
    """
    pool = pp.profit_pool().set_index("region")["margin_pct"]
    head = opt.corridor_economics().set_index("region")["yield_headroom_pct"]
    common = sorted(set(pool.index) & set(head.index))
    assert len(common) >= 6

    assert pool.loc[common].rank().corr(head.loc[common].rank()) > 0.95, (
        "the two corridor models have stopped agreeing, so one of them has changed basis"
    )


def test_the_print_report_covers_every_chart_the_page_carries():
    """`report.html` must not fall behind `index.html`.

    The report holds no prose of its own: it fetches index.html at load and
    rebuilds the same steps linearly, so the two cannot drift on content. What
    CAN drift is the scaffolding, so this pins the contract that matters: the
    report exists, it reads the same source, and every chart the page asks for is
    exported and therefore renderable in both.
    """
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    report = root / "docs" / "report.html"
    assert report.exists(), "report.html is gone, so there is no printable edition"

    text = report.read_text(encoding="utf-8")
    assert 'fetch("index.html")' in text, (
        "report.html no longer reads index.html, so the narrative is now duplicated "
        "and free to drift"
    )
    assert "assets/charts/" in text

    html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    wanted = set(re.findall(r'data-chart="([^"]+)"', html))
    have = {p.stem for p in (root / "docs" / "assets" / "charts").glob("*.json")}
    assert wanted <= have

    css = (root / "docs" / "assets" / "style.css").read_text(encoding="utf-8")
    assert "@media print" in css, "the print stylesheet is gone, so Save as PDF loses its layout"


def test_the_absorption_frontier_carries_a_working_scenario_selector():
    """Interactivity without JavaScript, and without breaking the palette rule.

    The site is static and figures ship as JSON, so a Plotly `restyle` button
    carries its own state and needs nothing at runtime. It restyles one trace
    rather than toggling three, because three scenario lines would be three red
    elements in the figure even with two hidden, and a house rule that can be
    dodged by hiding things is not a rule.
    """
    fig = fg.fig_absorption_frontier()
    menus = fig.layout.updatemenus
    assert menus, "the scenario selector is gone"

    labels = [b.label.strip() for b in menus[0].buttons]
    assert {"Base demand", "Bear demand", "Bull demand"} == set(labels)
    assert labels[0] == "Base demand", "the default case must be the one shown first"

    # every button must actually carry a different frontier
    series = [tuple(b.args[0]["y"][0]) for b in menus[0].buttons]
    assert len(set(series)) == len(series), "two scenario buttons draw the same line"

    # weaker demand needs a longer sector to absorb the same aircraft
    by_label = dict(zip(labels, series))
    assert by_label["Bear demand"][0] > by_label["Base demand"][0] > by_label["Bull demand"][0]

    # and the figure must still spend the red exactly once
    reds = sum(
        1
        for t in fig.data
        if getattr(getattr(t, "line", None), "color", None) == charts.RED
    )
    assert reds == 1, f"the selector introduced {reds} red traces"


def test_the_order_book_is_only_right_sized_under_the_bull_case():
    """A sensitivity worth pinning, because it is what the selector exists to show.

    Under bull demand the market grows into the aircraft at close to today's
    sector length. Under bear it does not, by a wide margin. The recommendation
    to lengthen the network is therefore load-bearing in exactly the cases where
    demand disappoints, which is the opposite of a convenient finding.
    """
    bear = fg.absorption_summary(scenario_name="Bear")
    base = fg.absorption_summary(scenario_name="Base")
    bull = fg.absorption_summary(scenario_name="Bull")

    assert bear["stage_uplift_pct"] > base["stage_uplift_pct"] > bull["stage_uplift_pct"]
    assert bull["stage_uplift_pct"] < 10, (
        "the bull case no longer absorbs the book at close to today's network, "
        "so the scenario selector no longer shows what it was built to show"
    )
    assert bear["stage_uplift_pct"] > 25


# --------------------------------------------------------------------------
# bilateral entitlements beyond Dubai
# --------------------------------------------------------------------------


def test_the_gulf_is_not_uniformly_capacity_capped():
    """The correction. Dubai is nearly full; Abu Dhabi is not.

    The recommendation originally leaned on "there is no room in the Gulf".
    Generalising the Dubai check to the second point showed that was an
    overstatement: only the largest city pair is close to its entitlement.
    """
    df = bm.gulf_entitlement_check().set_index("foreign_point")
    assert {"DUBAI", "ABUDHABI"} <= set(df.index)

    assert df.loc["DUBAI", "utilisation_pct"] > 85, "Dubai is no longer close to its cap"
    assert df.loc["ABUDHABI", "utilisation_pct"] < 80, (
        "Abu Dhabi has filled up, which would restore the simpler 'no room' argument"
    )
    assert df.loc["DUBAI", "utilisation_pct"] > df.loc["ABUDHABI", "utilisation_pct"]
    assert (df["headroom_seats_per_week"] > 0).all()


def test_the_two_entitlement_checks_do_not_drift():
    """`dubai_entitlement_check` predates the general one and must still agree."""
    single = bm.dubai_entitlement_check()
    general = bm.gulf_entitlement_check().set_index("foreign_point").loc["DUBAI"]

    assert single["implied_seats_per_week"] == general["implied_seats_per_week"]
    assert single["reported_entitlement_both_sides"] == general["reported_entitlement_both_sides"]
    assert single["utilisation_pct"] == general["utilisation_pct"]


def test_remaining_gulf_entitlement_barely_dents_the_order_book():
    """Why the recommendation survives the correction above.

    Abu Dhabi has real headroom. Flown at the Gulf's own sector length it still
    absorbs only a few per cent of the aircraft on order, so the constraint on
    Gulf deployment is economic first and legal second. If this ever exceeded
    about a quarter, the "fly them somewhere else" argument would need rebuilding.
    """
    h = fg.gulf_headroom_against_order_book()
    assert 0 < h["pct_of_order_book_absorbed"] < 25, (
        f"remaining Gulf entitlement now absorbs {h['pct_of_order_book_absorbed']}% of the "
        "order book, so the capacity argument needs revisiting"
    )
    assert h["headroom_ask_bn"] < h["order_book_ask_bn"]


def test_the_headroom_calculation_uses_the_published_bilateral_year():
    """A year-mixing bug, caught once and pinned.

    The first version defaulted to `fleet_gap.LATEST_COMPLETE_YEAR` (2025) while
    every published bilateral figure is computed on `INTL_COUNTRY_YEAR` (2024).
    It silently priced one year's traffic against another year's headline.
    """
    assert fg.gulf_headroom_against_order_book()["year"] == bm.INTL_COUNTRY_YEAR


def test_the_abu_dhabi_entitlement_stays_gated():
    """Secondary, like the Dubai row, and readable only on purpose.

    India publishes no entitlement table for any Gulf point. INVERT THIS, do not
    delete it, if the Ministry of Civil Aviation ever publishes one.
    """
    from src import data_pipeline as dp

    key = "india_abu_dhabi_weekly_seat_entitlement_one_side"
    with pytest.raises(dp.UnverifiedAssumption):
        dp.assumption(key)
    assert dp.assumption(key, allow_unverified=True) == 50_000


# --------------------------------------------------------------------------
# the other two surfaces, and the assets that make the link shareable
# --------------------------------------------------------------------------


def _docs():
    from pathlib import Path

    return Path(__file__).resolve().parent.parent / "docs"


def test_the_deck_reads_the_page_rather_than_repeating_it():
    """Three surfaces, one narrative.

    `index.html` holds the prose. `report.html` and `deck.html` both fetch it and
    re-lay it out, so none of the three can drift on content. If either stops
    reading index.html it has become a second copy of the argument, which is the
    thing this arrangement exists to prevent.
    """
    deck = _docs() / "deck.html"
    assert deck.exists(), "the deck is gone"
    text = deck.read_text(encoding="utf-8")
    assert 'fetch("index.html")' in text
    assert "scroll-snap" not in text, "slide layout belongs in style.css, not inline"

    # the deck must not carry step prose of its own
    assert text.count("<h2") == 0, "the deck has grown its own headings, so it can now drift"


def test_every_page_is_shareable():
    """A link with no preview card is a bare URL in every feed and inbox.

    The site had no og:, twitter: or favicon tags at all, which for a piece whose
    whole purpose is being sent to people was the largest cosmetic gap on it.
    """
    docs = _docs()
    card = docs / "assets" / "social-card.png"
    icon = docs / "assets" / "favicon.svg"
    assert card.exists() and card.stat().st_size > 10_000, "the social card is missing or empty"
    assert icon.exists(), "the favicon is missing"

    for name in ("index.html", "report.html"):
        text = (docs / name).read_text(encoding="utf-8")
        for tag in ('property="og:title"', 'property="og:image"', 'name="twitter:card"',
                    'property="og:description"', 'rel="icon"'):
            assert tag in text, f"{name} is missing {tag}"
        assert "social-card.png" in text
        # an image with no alt text is useless to the readers who most need it
        assert 'property="og:image:alt"' in text, f"{name} ships a preview image with no alt text"


def test_charts_carry_a_text_alternative():
    """Seventeen SVGs with no text alternative is a page a screen reader cannot use.

    The label and the table are both built at runtime from the figure Plotly
    actually rendered, so neither can disagree with the chart. This pins the
    scaffolding they need.
    """
    index = (_docs() / "index.html").read_text(encoding="utf-8")
    assert 'role="img"' in index and "aria-label" in index
    assert 'id="chart-data-body"' in index, "the data-table container is gone"

    js = (_docs() / "assets" / "scrolly.js").read_text(encoding="utf-8")
    assert "_fullData" in js, (
        "the table must be built from Plotly's decoded data, not the raw JSON: "
        "exported arrays are often binary encoded and have no length"
    )
    assert "setAttribute(\"aria-label\"" in js


# --------------------------------------------------------------------------
# belly cargo
# --------------------------------------------------------------------------


def test_freight_does_not_track_sector_length():
    """The module's central caveat, and the reason it exists as a test.

    The tempting reading is that cargo reinforces the long-haul case because
    long aircraft carry freight. It does not: North America is the longest
    corridor on the map and carries less freight per passenger than Africa.

    If this correlation ever becomes real, the prose in `src/cargo.py` and the
    chart subtitle are both wrong and must be rewritten rather than left. That
    is why the bound is asserted rather than the sign.
    """
    r = cg.distance_correlation()
    assert abs(r) < 0.35, (
        f"sector length now explains freight per passenger (r={r:+.2f}), so the "
        "module's central claim that it does not is no longer true"
    )


def test_europe_carries_far_more_freight_per_passenger_than_the_gulf():
    """The finding that supports Europe-first from a direction nothing else uses."""
    s = cg.summary()
    assert s["europe_vs_gulf"] > 2.5, (
        "Europe no longer carries materially more freight per passenger than the "
        "Gulf, so the cargo leg of the recommendation has gone"
    )
    assert s["europe_kg_per_pax"] > s["gulf_kg_per_pax"]


def test_the_densest_freight_corridor_is_not_the_biggest_passenger_one():
    """East Asia: thinnest passenger market in the set, densest freight.

    Worth pinning because it is the one thing in this module that points at a
    corridor the case does not otherwise examine.
    """
    df = cg.corridor_freight().set_index("region")
    densest = df["kg_per_pax"].idxmax()
    assert densest != "Gulf", "the Gulf is now the densest freight corridor, which reverses the finding"
    assert df.loc[densest, "pax"] < df["pax"].max() / 2


def test_cargo_reconciles_to_the_source_table():
    """Nothing in this module is modelled, so it must add back up to DGCA."""
    df = cg.corridor_freight()
    raw = bm.load_dgca_intl_country()
    raw = raw[raw["year"] == bm.INTL_COUNTRY_YEAR]
    total = float((raw["freight_to_india"] + raw["freight_from_india"]).sum())
    # corridor_freight drops the excluded regions, so it is a subset, never more
    assert 0 < df["freight_t"].sum() <= total + 1
    assert (df["kg_per_pax"] > 0).all()
    assert (df["ftk_bn"] > 0).all()


def test_the_cargo_chart_carries_no_modelled_badge():
    """It has nothing to model. If a revenue leg is ever added, this must flip."""
    fig = cg.fig_cargo_asymmetry()
    texts = [a.text or "" for a in fig.layout.annotations]
    assert not any("MODELLED" in t for t in texts), (
        "the cargo chart is now labelled modelled, so something unverifiable "
        "entered it; check whether a freight yield was introduced"
    )
