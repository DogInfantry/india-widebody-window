"""Data quality gates for the pipeline.

These are not decorative. Each one guards a specific way the DGCA data has
already tried to produce a wrong headline number:

- two-digit years that sort and join wrongly
- `Total *` pseudo-airlines that double count every passenger
- distance columns published in thousands, which put a 5 km average stage
  length on a chart before it was caught

The figure assertions below are the numbers recorded in PROJECT_STATE.md. If the
pipeline stops reproducing them, the pipeline changed, and that needs a reason.
"""

from __future__ import annotations

import pytest

from src import data_pipeline as dp


@pytest.fixture(scope="module")
def intl_country():
    return dp.load_dgca_intl_country()


@pytest.fixture(scope="module")
def intl_carrier():
    return dp.load_dgca_intl_carrier()


@pytest.fixture(scope="module")
def dom_carrier():
    return dp.load_dgca_domestic_carrier()


# --------------------------------------------------------------------------
# the suite must not depend on a third party being up
# --------------------------------------------------------------------------


def test_loaders_work_with_no_network(monkeypatch):
    """Every loader must read the committed parquet without touching the network.

    This guards a real CI failure. Before it, every loader fetched, so the suite
    silently depended on DGCA, Eurostat and the World Bank all being reachable.
    It passed locally only because data/raw/ held a same-day cache. In CI, where
    that cache is gitignored and absent, the World Bank returned an intermittent
    400 and the build went red for reasons that had nothing to do with the code.

    A red build meaning "a third party hiccuped" is a build people learn to
    ignore, which is worse than no build at all.
    """

    def explode(*args, **kwargs):
        raise AssertionError("a loader tried to reach the network during tests")

    monkeypatch.setattr(dp.requests, "get", explode)

    for name, fn in dp.loaders().items():
        df = fn()
        assert len(df) > 0, f"{name} came back empty from parquet"


# --------------------------------------------------------------------------
# schema and shape
# --------------------------------------------------------------------------


def test_intl_country_shape(intl_country):
    assert len(intl_country) > 2_000
    for col in ("year", "quarter", "country", "pax_total", "region", "is_gulf"):
        assert col in intl_country.columns
    assert intl_country[["year", "quarter", "country", "pax_total"]].notna().all().all()


def test_intl_city_shape():
    df = dp.load_dgca_intl_city()
    assert len(df) > 15_000
    assert (df["pax_total"] >= 0).all()


def test_dom_city_shape():
    df = dp.load_dgca_domestic_city()
    assert len(df) > 60_000
    assert df["month"].between(1, 12).all()


def test_airports_have_coordinates():
    df = dp.load_ourairports()
    assert len(df) > 4_000
    assert df[["latitude_deg", "longitude_deg"]].notna().all().all()


# --------------------------------------------------------------------------
# trap 1: two-digit years
# --------------------------------------------------------------------------


def test_years_are_four_digit(intl_country, intl_carrier, dom_carrier):
    for df in (intl_country, intl_carrier, dom_carrier):
        assert df["year"].min() >= 2000, "two-digit year leaked through _norm_year"
        assert df["year"].max() <= 2100


def test_norm_year_is_idempotent():
    import pandas as pd

    assert dp._norm_year(pd.Series([2015, 2024])).tolist() == [2015, 2024]
    assert dp._norm_year(pd.Series([15, 24])).tolist() == [2015, 2024]


# --------------------------------------------------------------------------
# trap 2: Total pseudo-airlines
# --------------------------------------------------------------------------


def test_no_total_pseudo_airlines(intl_carrier, dom_carrier):
    for df in (intl_carrier, dom_carrier):
        names = df["airline"].astype(str).str.lower()
        assert not names.str.startswith("total").any(), (
            "a 'Total *' row survived; every market share downstream is now halved"
        )


# --------------------------------------------------------------------------
# trap 3: distance columns published in thousands
# --------------------------------------------------------------------------


def test_stage_length_is_physically_plausible(dom_carrier):
    """A scheduled flight covers hundreds to thousands of km, not single digits."""
    s = dom_carrier[dom_carrier["service_type"] == "ScheduledDomestic"]
    stage = s["rpk"].sum() / s["pax"].sum()
    assert 500 < stage < 2_000, f"domestic stage length {stage:.1f} km is not plausible"

    i = dom_carrier[dom_carrier["service_type"] == "ScheduledInternational"]
    stage_i = i["rpk"].sum() / i["pax"].sum()
    assert 1_500 < stage_i < 8_000, f"international stage length {stage_i:.1f} km is not plausible"


def test_computed_load_factor_matches_published(dom_carrier):
    """rpk/ask must agree with DGCA's own load_factor column.

    This validates the ratio independently of the scale fix, so a future unit
    change cannot quietly break one without breaking the other.
    """
    s = dom_carrier[
        (dom_carrier["service_type"] == "ScheduledDomestic") & (dom_carrier["year"] == 2025)
    ]
    g = s.groupby("airline").agg(
        rpk=("rpk", "sum"), ask=("ask", "sum"), lf_pub=("load_factor", "mean")
    )
    g = g[g["ask"] > 0]
    delta = (100 * g["rpk"] / g["ask"] - g["lf_pub"]).abs()
    assert delta.max() < 2.0, f"load factor mismatch up to {delta.max():.2f}pp"


# --------------------------------------------------------------------------
# headline figures (see PROJECT_STATE.md)
# --------------------------------------------------------------------------


def test_gulf_share_2024(intl_country):
    y = intl_country[intl_country["year"] == 2024]
    share = 100 * y[y["is_gulf"]]["pax_total"].sum() / y["pax_total"].sum()
    assert 50.0 <= share <= 53.0, f"Gulf share {share:.1f}% is outside the verified band"


def test_india_international_total_2024(intl_country):
    total = intl_country[intl_country["year"] == 2024]["pax_total"].sum()
    assert 70e6 < total < 75e6, f"2024 international sector pax {total/1e6:.1f}M off expectation"


def test_indian_carrier_share_2024(intl_carrier):
    y = intl_carrier[intl_carrier["year"] == 2024]
    g = y.groupby("carrier_group")["pax_total"].sum()
    indian = 100 * g.get("Indian", 0) / g.sum()
    assert 43.0 <= indian <= 48.0, f"Indian carrier share {indian:.1f}% off expectation"
    assert g.get("Gulf", 0) > 0, "no Gulf carriers matched; check GULF_CARRIERS spellings"


def test_indigo_domestic_share_2025(dom_carrier):
    s = dom_carrier[
        (dom_carrier["service_type"] == "ScheduledDomestic") & (dom_carrier["year"] == 2025)
    ]
    g = s.groupby("airline")["pax"].sum()
    share = 100 * g["IndiGo"] / g.sum()
    assert 62.0 <= share <= 66.0, f"IndiGo domestic share {share:.1f}% off expectation"


def test_the_stage_length_gap(dom_carrier):
    """The core finding: IndiGo flies short-haul international, Air India long-haul.

    This gap is what the wide-body orders are meant to close, so it is the one
    number the whole case rests on.
    """
    i = dom_carrier[
        (dom_carrier["service_type"] == "ScheduledInternational") & (dom_carrier["year"] == 2025)
    ]
    g = i.groupby("airline").agg(pax=("pax", "sum"), rpk=("rpk", "sum"))
    stage = g["rpk"] / g["pax"]
    assert 2_500 < stage["IndiGo"] < 2_800, f"IndiGo stage {stage['IndiGo']:.0f} km off expectation"
    assert 5_100 < stage["Air India"] < 5_500, (
        f"Air India stage {stage['Air India']:.0f} km off expectation"
    )
    assert stage["Air India"] > 1.9 * stage["IndiGo"], "the stage length gap has vanished"


# --------------------------------------------------------------------------
# both-ends reconciliation
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def eurostat():
    return dp.load_eurostat_avia_par()


def test_eurostat_returns_india_routes(eurostat):
    assert len(eurostat) > 20, "Eurostat returned almost nothing; check the API contract"
    assert (eurostat["pax"] > 0).all()
    assert eurostat["partner_icao"].str.startswith("V").all(), (
        "partner airports should all be Indian ICAO codes, which begin with V"
    )


def test_dgca_and_eurostat_agree_on_the_same_routes(eurostat, intl_country):
    """Two independent agencies measuring the same routes from opposite ends.

    This is the strongest available check on the DGCA spine, because Eurostat has
    no knowledge of the Indian data and vice versa. Italy is excluded: the two
    disagree there on exactly one route, Rome to Delhi, and that dispute is
    tracked in dp.DISPUTED_ROUTES rather than averaged away.
    """
    cc_to_name = {
        "CH": "SWITZERLAND",
        "DE": "GERMANY",
        "DK": "DENMARK",
        "FI": "FINLAND",
        "FR": "FRANCE",
        "NL": "NETHERLANDS",
        "PL": "POLAND",
    }
    e24 = eurostat[eurostat["year"] == 2024]
    d24 = intl_country[intl_country["year"] == 2024]

    euro_total = e24[e24["reporter_country"].isin(cc_to_name)]["pax"].sum()
    dgca_total = d24[d24["country"].isin(cc_to_name.values())]["pax_total"].sum()

    assert euro_total > 0 and dgca_total > 0
    gap = abs(euro_total - dgca_total) / dgca_total
    assert gap < 0.05, (
        f"DGCA and Eurostat diverge by {gap:.1%} across {len(cc_to_name)} countries; "
        "one of the two sources has changed"
    )


def test_rome_delhi_stays_quarantined():
    """The one route the agencies disagree on must not silently rejoin the analysis."""
    assert ("ROME", "DELHI") in dp.DISPUTED_ROUTES


def test_the_2019_uk_anomaly_is_corrected(intl_country):
    """A corrupt DGCA observation must not creep back into the growth rates.

    2019 Q3 United Kingdom was published at 1,162,094 against a 2015-18 Q3
    median of 654,870. The same event inflated the London to Chennai city row to
    17x its decade-long baseline. Because the pre-covid CAGR is fitted from 2015
    to 2019, an inflated endpoint feeds the trend sizing and all three demand
    scenarios, so this is not cosmetic.
    """
    uk = intl_country[
        (intl_country["country"] == "UNITED KINGDOM") & (intl_country["quarter"] == 3)
    ].set_index("year")["pax_total"]

    baseline = uk.loc[[2015, 2016, 2017, 2018]].median()
    assert uk[2019] < 1.3 * baseline, (
        f"2019 Q3 UK is {uk[2019]:,.0f} against a {baseline:,.0f} baseline; "
        "the anomaly correction is not being applied"
    )
    assert intl_country["anomaly_corrected"].sum() == len(dp.COUNTRY_ANOMALIES)


def test_correcting_the_anomaly_reconciles_dgca_to_eurostat():
    """The correction is justified by independent agreement, not by taste.

    Uncorrected, DGCA and Eurostat disagree on the UK by 25.8%. Corrected, they
    agree to 2.5%, which is the same level as every other route both cover. That
    second source is the whole reason this row is treated as wrong rather than
    merely surprising.
    """
    city = dp.load_dgca_intl_city()
    london_2019 = city[
        (city["year"] == 2019) & ((city["city1"] == "LONDON") | (city["city2"] == "LONDON"))
    ]["pax_total"].sum()

    eurostat_heathrow_2019 = 2_199_330  # avia_par_uk, PAS_CRD, India pairs
    gap = abs(london_2019 - eurostat_heathrow_2019) / eurostat_heathrow_2019
    assert gap < 0.06, f"DGCA London and Eurostat Heathrow diverge by {gap:.1%} after correction"


def test_anomaly_corrections_preserve_direction_split():
    """Scaling must keep the to/from ratio, which is real information."""
    city = dp.load_dgca_intl_city()
    row = city[city["anomaly_corrected"]]
    assert len(row) == len(dp.CITY_ANOMALIES)
    r = row.iloc[0]
    assert r["pax_to_city2"] > 0 and r["pax_from_city2"] > 0
    assert abs(r["pax_to_city2"] + r["pax_from_city2"] - r["pax_total"]) <= 1


# --------------------------------------------------------------------------
# provenance contract
# --------------------------------------------------------------------------


def test_manual_assumptions_carry_provenance():
    """Every hand-entered number must be citable and carry a lifecycle status."""
    df = dp.load_manual_assumptions()
    required = {"key", "value", "source_name", "pull_date", "reliability", "status", "note"}
    assert required <= set(df.columns)
    if len(df):
        assert df["key"].notna().all() and df["key"].is_unique
        assert df["reliability"].isin(["H", "M", "L"]).all()
        assert df["status"].isin(dp.ASSUMPTION_STATUSES).all()
        # A row that claims a value must say where it came from.
        valued = df[df["value"].notna()]
        assert valued["source_name"].notna().all(), "a numeric assumption has no source"
        assert valued["pull_date"].notna().all(), "a numeric assumption has no pull date"


def test_unverified_assumptions_cannot_reach_a_chart():
    """The gate that makes verification structural rather than a promise.

    Every row is currently DRAFT_UNVERIFIED or NOT_AVAILABLE, so every call must
    raise. When a row is verified by a human this test keeps guarding the rest.
    """
    df = dp.load_manual_assumptions()
    if not len(df):
        pytest.skip("no assumptions recorded yet")

    for key in df.loc[df["status"] != "VERIFIED", "key"]:
        with pytest.raises((dp.UnverifiedAssumption, KeyError)):
            dp.assumption(key)

    # Verified rows, once they exist, must actually return a number.
    for key in df.loc[df["status"] == "VERIFIED", "key"]:
        assert isinstance(dp.assumption(key), float)


def test_unknown_status_is_rejected(tmp_path, monkeypatch):
    """A typo in the status column must fail loudly, not silently pass the gate."""
    import pandas as pd

    bad = tmp_path / "assumptions.csv"
    pd.DataFrame(
        [
            {
                "key": "x",
                "value": 1.0,
                "unit": "u",
                "source_name": "s",
                "source_url": "http://example.invalid",
                "pull_date": "2026-08-15",
                "page_ref": "p1",
                "reliability": "H",
                "status": "verifed",  # deliberate typo
                "note": "n",
            }
        ]
    ).to_csv(bad, index=False)
    monkeypatch.setattr(dp, "MANUAL", tmp_path)
    with pytest.raises(ValueError, match="unknown status"):
        dp.load_manual_assumptions()
