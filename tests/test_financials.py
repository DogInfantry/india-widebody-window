"""The client's own numbers, and the two ways this module could publish a lie.

`src/financials.py` reads gated rows and does arithmetic over them. That makes
most of it hard to get wrong. Two things are easy to get wrong, and both have
already happened once in this repo in some form:

1. **Publishing one FY2026 margin without the other.** The 17.8% reported figure
   and the 27.3% ex-forex figure tell opposite stories and both are true. Gotcha
   19 exists because the retraction in `docs/methodology.md` was for treating a
   non-operating collapse as an operating one, and quoting only the ex-forex
   number is the same mistake pointing the other way.

2. **Confusing the forex LEVEL with the forex CONTRIBUTION.** FY2026 CASK
   ex-fuel minus FY2026 CASK ex-fuel ex-forex is 0.52. The year-on-year currency
   contribution is 0.41. The first version of this module computed the former
   and its own docstring quoted the latter.
"""

from __future__ import annotations

import pytest

from src import financials as fin
from src import scenario as sc
from src.data_pipeline import USABLE_STATUSES, load_manual_assumptions


def test_the_spread_is_inverted_and_the_currency_dwarfs_it():
    """The sharpest number in the project, and the thing that explains it.

    If this flips, IndiGo covers its unit cost again and the client page's
    headline is wrong. That is a finding, not a failure, but it must not happen
    silently.
    """
    s = fin.unit_spread()
    assert s.rask == pytest.approx(4.99)
    assert s.cask == pytest.approx(5.00)
    assert s.inverted, "RASK no longer sits below CASK. The client page headline has moved."
    assert s.spread == pytest.approx(-0.01, abs=1e-9)
    # The whole point of stating the currency line beside the inversion.
    assert s.currency_vs_gap > 10


def test_the_currency_contribution_is_the_bridge_step_not_the_level():
    """0.41, never 0.52. Eleven paise apart, and only one of them is the answer."""
    bridge = sc.cask_bridge().set_index("step")
    assert fin.unit_spread().currency_contribution == pytest.approx(
        bridge.loc["Currency", "inr_per_ask"]
    )
    assert fin.unit_spread().currency_contribution == pytest.approx(0.41)


def test_both_fy2026_margins_are_returned_together():
    """Neither margin can be read out of this module without the other."""
    ladder = fin.margin_ladder()
    fy26 = ladder[ladder["year"] == "FY2026"]
    assert set(fy26["basis"]) == {"As reported", "Excluding forex"}

    reported = float(fy26.loc[fy26["basis"] == "As reported", "margin_pct"].iloc[0])
    exforex = float(fy26.loc[fy26["basis"] == "Excluding forex", "margin_pct"].iloc[0])
    assert reported == pytest.approx(17.8)
    assert exforex == pytest.approx(27.3, abs=0.05)
    # The gap is the finding. If they converge, the note explaining them is stale.
    assert exforex - reported > 5


def test_the_cost_stack_closes_on_the_published_bridge():
    """Three bases, and the middle one reconciles to the CASK bridge exactly.

    Non-fuel cost rose 0.52. Genuine inflation was 0.11. The residual IS the
    currency step, and if it stops being so, one of the two sources moved.
    """
    stack = fin.cost_stack().set_index("basis")
    exfuel = float(stack.loc["CASK ex-fuel", "change"])
    real = float(stack.loc["CASK ex-fuel ex-forex", "change"])
    bridge = sc.cask_bridge().set_index("step")
    assert exfuel - real == pytest.approx(bridge.loc["Currency", "inr_per_ask"], abs=1e-9)


def test_capital_scale_names_no_aircraft_price():
    """Scale without a price, because no aircraft price has cleared the gate.

    A list price is not a transaction price and transaction prices are
    confidential. If a price ever enters this function it has to enter through
    `assumptions.csv` first, and this test is what makes that a decision rather
    than a slip.
    """
    cap = fin.capital_scale()
    assert cap["aircraft"] == 60
    assert cap["seats"] == pytest.approx(60 * 315)
    assert "price" not in " ".join(cap).lower()
    assert "cost" not in " ".join(cap).lower()
    # It is roughly a year of EBITDAR, which is the order-of-magnitude claim the
    # page makes. A wide band, because the claim is deliberately coarse.
    assert 0.5 < cap["multiple_of_fy2026_ebitdar"] < 2.0


def test_the_block_hour_reconciliation_holds_on_both_bases():
    """The like-for-like figure is the headline, and it is the one that holds.

    **The scheduled-only reconciliation used to be the published headline at
    0.31%, and the September 2026 refresh proved that was the wrong choice.**
    DGCA moved 4,381 hours from Scheduled International to Non-Scheduled
    International, the quantity did not change at all, and the figure went to
    0.58% purely because the classification boundary moved.

    The all-services basis is what IndiGo's own total covers, so it is the
    like-for-like comparison, and it did not budge: 1,619,570.6 against
    1,619,570, which is 0.64 hours in 1.6 million. That is the published figure
    now. The scheduled-only number is still computed and still reported beside
    it, with a band wide enough to survive a reclassification rather than an
    assertion that pins it.
    """
    ops = fin.operations()
    # Deliberately wide. This basis depends on DGCA's scheduled boundary, which
    # moves, and pinning it to two decimals is what broke CI in September 2026.
    assert 0.0 < ops["reconciliation_pct"] < 2.0
    assert ops["reconciliation_all_services_pct"] < 0.01
    assert ops["non_scheduled_intl_hours"] > 0


def test_air_india_yield_stays_empty():
    """Unlisted, files nothing. A proxy here would be a number with no source."""
    rows = fin.competitive_position().set_index("carrier")
    assert rows.loc["Air India", "yield_inr_per_rpk"] != rows.loc["Air India", "yield_inr_per_rpk"]
    assert rows.loc["Emirates", "yield_vs_indigo"] > 1.5


def test_every_row_this_module_reads_has_cleared_the_gate():
    """No `allow_unverified=True` anywhere in the client page's inputs.

    Two places in the repo read an unverifiable row on purpose, and both are
    named in CLAUDE.md. This module must not become a third: the client page is
    the one surface where a number with no primary source would look most like a
    fact.
    """
    source = (fin.__file__ and open(fin.__file__, encoding="utf-8").read()) or ""
    assert "allow_unverified" not in source

    rows = load_manual_assumptions()
    statuses = dict(zip(rows["key"], rows["status"]))
    for key in statuses:
        if f'assumption("{key}")' in source:
            assert statuses[key] in USABLE_STATUSES, f"{key} is read but has not cleared"
