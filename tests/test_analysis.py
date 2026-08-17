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
PUBLISHING_MODULES = (bm, pp, fg, ms, opt, sc)


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
    assert abs(start["pax_m"].iloc[0] - 72.2) < 1.0


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
    """Sector share is computed from DGCA; the O-D share can never be verified."""
    g = opt.connect_gap()
    assert g["gap_pts"] == pytest.approx(g["sector_share_pct"] - g["od_share_pct"], abs=0.05)
    assert 8 < g["gap_pts"] < 15, "the connect gap has moved outside the range the case argues"


def test_the_od_share_cannot_reach_a_published_figure_through_the_gate():
    """`gulf_od_share_pct` must stay refused unless a caller opts in explicitly.

    It was carried as a hard number on the live page with no row here at all,
    which is how it escaped the gate for the life of the project. Now it is gated,
    and this asserts the gate bites. INVERT THIS, do not delete it, if IATA ever
    publishes a free origin-destination table.
    """
    from src import data_pipeline as dp

    with pytest.raises(dp.UnverifiedAssumption):
        dp.assumption("gulf_od_share_pct")
    assert dp.assumption("gulf_od_share_pct", allow_unverified=True) > 0


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
