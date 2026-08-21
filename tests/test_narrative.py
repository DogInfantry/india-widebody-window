"""The prose must agree with the code.

`tests/test_pipeline.py` guards the data dictionary against drifting from
`assumptions.csv`, and it has fired correctly every time it was needed. Nothing
guarded the narrative, and the narrative is where the drift actually happened:
prose was reconciled to the modules **by hand three separate times** in one
session, after the recommendation changed, after the Abu Dhabi bilateral
corrected an overclaim, and after the headline year moved to 2025.

Three figures still survived all of that, and the reason is worth recording
because it shapes how this file works: every one of them was missed by a
string-replacement sweep because the phrase wrapped across a line break.

    docs/pivot_log.md        Abu Dhabi "at about\\n   58%"   should have been 70%
    docs/methodology.md      "larger than 5%"                should have been 4%
    docs/recommendation.md   "somewhat larger than 5%"       should have been 4%

So this file does not match line by line. It flattens the whole corpus, strips
tags, collapses whitespace, and then asks two questions per claim. The second is
the one that catches drift:

    must_appear      at least one accepted phrasing is present.
                     Catches a figure being dropped entirely.
    must_not_appear  no SUPERSEDED phrasing is present.
                     Catches a figure that was right once and quietly stopped
                     being right. "58%" was a real number for exactly one commit.

**When a headline number moves, update `must_not_appear` as well as the prose.**
Adding the old value there is what makes the next drift a failing build instead
of an audit finding. That is recorded as a working agreement in `CLAUDE.md`.

Deliberately partial. About fifteen claims, the ones the argument turns on, not
every number in the repo. A guard that fails on incidental prose gets deleted the
second time it cries wolf, and then it guards nothing.

**The limit worth knowing.** `must_appear` is satisfied by ONE occurrence anywhere
in the corpus, so a correct statement in one file will mask a stale one in
another. `must_not_appear` is what actually finds those, and it only finds
phrasings someone thought to write down. Two figures reached the live site past
this guard's first version because the prose said "72 million" and "33 million"
where the patterns said "72.2M" and nothing at all. **When a number moves, grep
the corpus for how the prose actually words it, not for how the module prints
it**, and add every wording found to `must_not_appear`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from src import benchmarking as bm
from src import data_pipeline as dp
from src import fleet_gap as fg
from src import market_sizing as ms
from src import options as opt
from src import scenario as sc
from src import profit_pools as pp

ROOT = Path(__file__).resolve().parent.parent

# Everything a reader can reach. `data/data_dictionary.md` is deliberately out:
# it documents provenance rather than making the argument, and it carries
# historical values on purpose.
CORPUS_FILES = (
    ["README.md", "CLAUDE.md", "ROADMAP.md"]
    + [f"docs/{p.name}" for p in sorted((ROOT / "docs").glob("*.md"))]
    + [f"docs/{p.name}" for p in sorted((ROOT / "docs").glob("*.html"))]
    # The delivery layer carries prose too, and for the whole life of the app it
    # was exempt from this guard: a superseded figure typed into a React page
    # would have been published and nothing here would have noticed. The same
    # exemption once let `market_sizing` and `scenario` skip the chart house
    # rules for the life of the project, which is gotcha 39.
    + [
        str(q.relative_to(ROOT)).replace("\\", "/")
        for q in sorted((ROOT / "web").rglob("*.tsx"))
        if "node_modules" not in q.parts and ".next" not in q.parts
    ]
)


def _flatten(path: Path) -> str:
    """One published file, flattened so line wrapping cannot hide a figure.

    Factored out of the corpus fixture because the paired-margin guard has to
    know WHICH file it found a violation in, and a single flattened blob cannot
    say.
    """
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"<!--\s*narrative-guard:\s*ignore.*?-->.*?<!--\s*/narrative-guard\s*-->",
        " ",
        text,
        flags=re.S,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def corpus() -> str:
    """Every published word, flattened so line wrapping cannot hide a figure."""
    parts = []
    for rel in CORPUS_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Passages that record superseded figures ON PURPOSE, such as the data
        # vintage table in the methodology, opt out explicitly. Without this the
        # guard cannot tell "published as history" from "published as fact", and
        # the honest thing to do is let the author say which it is, visibly, in
        # the source where a reader will also see it.
        text = re.sub(
            r"<!--\s*narrative-guard:\s*ignore.*?-->.*?<!--\s*/narrative-guard\s*-->",
            " ",
            text,
            flags=re.S,
        )
        text = re.sub(r"<[^>]+>", " ", text)  # strip HTML tags
        parts.append(text)
    return re.sub(r"\s+", " ", " ".join(parts))


@dataclass(frozen=True)
class Claim:
    name: str
    compute: object
    fmt: str
    must_appear: tuple[str, ...]
    # Values this claim used to hold. Each one was correct once.
    must_not_appear: tuple[str, ...] = field(default=())


def _gulf(field_name: str):
    return lambda: float(
        bm.gulf_entitlement_check().set_index("foreign_point").loc["ABUDHABI", field_name]
    )


CLAIMS: tuple[Claim, ...] = (
    Claim(
        "India international sector passengers",
        lambda: bm.load_dgca_intl_country().pipe(
            lambda d: d[d.year == bm.INTL_COUNTRY_YEAR]["pax_total"].sum() / 1e6
        ),
        "{:.0f}M",
        must_appear=("78.0M", "78M", "78 million"),
        # "72 million", with no decimal, is how the sizing step phrased it and is
        # why this figure survived on the live site after four sweeps. Superseded
        # patterns have to cover every phrasing the prose actually uses, not the
        # one the module prints.
        must_not_appear=("72.2M", "72.2 million", "72 million", "from 72M"),
    ),
    Claim(
        "Gulf share of international sectors",
        lambda: float(bm.corridor_scale().set_index("region").loc["Gulf", "share_pct"]),
        "{:.1f}%",
        must_appear=("50.9%", "51 per cent"),
        must_not_appear=("51.2%",),
    ),
    Claim(
        "Gulf corridor passengers",
        lambda: float(bm.corridor_scale().set_index("region").loc["Gulf", "pax_total"]) / 1e6,
        "{:.1f}M",
        must_appear=("39.7M",),
        must_not_appear=("36.9M",),
    ),
    Claim(
        "Indian carrier share",
        lambda: float(bm.who_carries_india().set_index("carrier_group").loc["Indian", "share_pct"]),
        "{:.1f}%",
        must_appear=("45.9%", "46 per cent"),
        must_not_appear=("45.3%",),
    ),
    Claim(
        "2030 sizing band",
        lambda: ms.triangulate().band[0],
        "{:.0f}M",
        must_appear=("96M to 109M", "96 to 109", "96 and 109 million"),
        must_not_appear=("91M to 108M", "91 to 108", "91 and 108 million"),
    ),
    Claim(
        "connecting passengers",
        lambda: opt.connect_gap()["connecting_pax_m"],
        "{:.1f}M",
        must_appear=("8.5M", "eight and a half"),
        must_not_appear=("8.07M", "8.1M"),
    ),
    Claim(
        "value at stake, floor",
        lambda: opt.value_at_stake()["revenue_floor_inr_cr"],
        "{:,.0f}",
        must_appear=("28,900", "28,916"),
        must_not_appear=("27,486", "27,500"),
    ),
    Claim(
        "value at stake, ceiling",
        lambda: opt.value_at_stake()["revenue_ceiling_inr_cr"],
        "{:,.0f}",
        must_appear=("56,700", "56,712"),
        must_not_appear=("53,906", "53,900"),
    ),
    Claim(
        "Dubai bilateral utilisation",
        lambda: float(
            bm.gulf_entitlement_check().set_index("foreign_point").loc["DUBAI", "utilisation_pct"]
        ),
        "{:.1f}%",
        must_appear=("88.8%", "88.8 per cent"),
        must_not_appear=("89.6%", "89.6 per cent"),
    ),
    Claim(
        "Abu Dhabi bilateral utilisation",
        _gulf("utilisation_pct"),
        "{:.0f}%",
        must_appear=("70%", "70.1%"),
        # 58% was correct for exactly one commit. This is the entry that would
        # have caught the drift the audit found by hand.
        must_not_appear=("about 58%", "at about 58%", "nearer 58%"),
    ),
    Claim(
        "Gulf headroom against the order book",
        lambda: fg.gulf_headroom_against_order_book()["pct_of_order_book_absorbed"],
        "{:.0f}%",
        must_appear=("4% of the order book", "four per cent"),
        must_not_appear=("5% of the order book", "five per cent of the order book"),
    ),
    Claim(
        "sector uplift needed to absorb the book",
        lambda: fg.absorption_summary()["stage_uplift_pct"],
        "{:.0f}%",
        must_appear=("27%", "a quarter"),
        # No must_not_appear. The obvious candidate, "a third", also matches
        # "a third to two thirds of IndiGo's revenue", which is current and
        # correct. A guard that fires on unrelated prose gets deleted.
    ),
    Claim(
        "share needed to absorb the book",
        lambda: fg.absorption_summary()["share_pct_to_absorb"],
        "{:.0f}%",
        must_appear=("58%", "58 per cent"),
    ),
    Claim(
        "order book ASK uplift",
        lambda: 100 * fg.order_book_ask()["ask"] / fg.baseline().ask,
        "{:.0f}%",
        must_appear=("78%", "78 per cent"),
    ),
    Claim(
        "scenario spread",
        lambda: (
            sc.scenario_table().set_index("scenario").loc["Bull", "pax_2030_m"]
            - sc.scenario_table().set_index("scenario").loc["Bear", "pax_2030_m"]
        ),
        "{:.0f}M",
        must_appear=("27 million passengers", "27M"),
        # Found on the LIVE site after five sweeps and after this guard's first
        # version passed, because "33 million" matched no pattern anyone had
        # thought to write down. The lesson is in the docstring.
        must_not_appear=("33 million passengers",),
    ),
    Claim(
        # Counted from the pivot log itself, never typed. This drifted TWICE
        # without failing anything: pivot 7 was added and six other files kept
        # saying six, then pivot 8 was added and CLAUDE.md alone said seven. The
        # app was right the whole time because `web/app/methodology` renders
        # `pivots.length`; every hand-written surface was wrong, including the
        # OpenGraph description that shows in a link preview.
        "documented changes of mind",
        lambda: sum(
            ln.startswith("## Pivot ")
            for ln in (ROOT / "docs" / "pivot_log.md").read_text(encoding="utf-8").splitlines()
        ),
        "{:.0f}",
        must_appear=("Ten documented changes of mind", "ten documented changes of mind"),
        must_not_appear=(
            "six documented changes of mind",
            "Six documented changes of mind",
            "Seven documented changes of mind",
            "seven documented changes of mind",
            "Eight documented changes of mind",
            "eight documented changes of mind",
            "Six times, evidence turned",
            "Eight times, evidence turned",
            "Six changes of mind",
            "Eight changes of mind",
            "the six times evidence turned",
            "the six times it was wrong",
            "the eight times evidence turned",
            "the eight times it was wrong",
            # README phrased the count two more ways, and neither matched any
            # pattern above, so it published "five others" and "four of the six"
            # for two pivots while line 70 of the same file correctly said ten.
            # A blacklist only finds the wordings somebody thought to write down.
            "and five others",
            "Four of the six were caught",
            "four of the six were caught",
        ),
    ),
    Claim(
        # The README told readers the verified capacity leg "came in at 90.7M".
        # It came in at 96.5M. Nothing failed, because the sizing BAND was
        # guarded and its individual legs were not, and this is the leg the
        # prose actually argues from: it is the low end, so it is the one that
        # made the recommendation harder to argue.
        "capacity leg of the 2030 sizing",
        lambda: ms.estimate_capacity().value_m,
        "{:.1f}M",
        must_appear=("96.5M",),
        must_not_appear=("90.7M",),
    ),
    Claim(
        "IndiGo domestic load factor",
        lambda: float(
            bm.carrier_operating_summary(bm.LATEST_COMPLETE_YEAR)
            .set_index("airline")
            .loc["IndiGo", "load_factor_pct"]
        ),
        "{:.1f}%",
        must_appear=("86.1%",),
        # The stronger claim the data contradicts. IndiGo went 87.8 to 86.1 and
        # SpiceJet 92.7 to 86.2 measured 2019 against 2025, so "every major
        # carrier" is false for the two largest. The narrow claim, that everyone
        # clears 80%, is true and is what the prose says now.
        must_not_appear=(
            "recovered past their pre-pandemic level",
            "recovered past its pre-pandemic level",
        ),
    ),
    Claim(
        "FY2026 EBITDAR margin, as reported",
        lambda: dp.assumption("indigo_ebitdar_margin_fy2026_reported_pct"),
        "{:.1f}%",
        must_appear=("17.8%", "17.8 per cent"),
    ),
    Claim(
        "Gulf passenger against revenue share",
        lambda: float(pp.profit_pool().set_index("region").loc["Gulf", "revenue_share_pct"]),
        "{:.0f}%",
        must_appear=("31%", "31 per cent"),
    ),
)


@pytest.mark.parametrize("claim", CLAIMS, ids=lambda c: c.name)
def test_the_prose_states_the_number_the_code_computes(claim, corpus):
    """At least one accepted phrasing of the current value must be published."""
    value = claim.compute()
    found = [p for p in claim.must_appear if p in corpus]
    assert found, (
        f"{claim.name} computes to {claim.fmt.format(value)} but none of "
        f"{list(claim.must_appear)} appears anywhere in the written IP. Either the "
        "figure was dropped or its phrasing changed; add the new wording to must_appear."
    )


@pytest.mark.parametrize(
    "claim", [c for c in CLAIMS if c.must_not_appear], ids=lambda c: c.name
)
def test_no_superseded_figure_is_still_published(claim, corpus):
    """The guard that matters. A number that was right once must not linger.

    This is the assertion that catches the failure this file exists for: prose
    that was correct at the time, was never swept when the number moved, and
    reads as current to everyone who finds it.
    """
    stale = [p for p in claim.must_not_appear if p in corpus]
    assert not stale, (
        f"{claim.name} now computes to {claim.fmt.format(claim.compute())}, but the "
        f"superseded value(s) {stale} are still in the written IP. Find and update "
        "them. If a figure legitimately appears as history, quote it inside a "
        "sentence that says so and narrow the must_not_appear pattern."
    )


def test_neither_fy2026_margin_is_ever_published_alone(corpus):
    """27.3% and 17.8% travel together or not at all.

    This project published a margin claim and had to retract it: an asserted
    operating-margin halving that came from a convention IndiGo does not publish.
    The retraction is in `docs/methodology.md` and must stay there.

    **The symmetric error is just as easy and would be worse**, because it
    flatters. IndiGo REPORTED 17.8% for FY2026; 27.3% is ex-forex. Quoting only
    the ex-forex figure treats an operating improvement as the whole story, which
    is the same mistake pointing the other way. Gotcha 19 says state both; this
    is what makes the build fail if a surface does not.

    **Run per file, and the exception list is empty.** It was not: when this
    guard was first written `docs/methodology.md` quoted 27.3% inside the
    retraction passage with no 17.8% beside it, and it was listed here rather
    than exempted by a looser rule so that it stayed visible. The passage now
    carries both rows and the entry is gone, which is the invert-the-gate
    discipline this project runs on. Leave the list empty; add to it only to
    make an existing violation visible, never to let a new one through.
    """
    known_open: set[str] = set()
    window = 900  # characters, generous: the corpus is flattened so lines merge
    offenders = {}

    for rel in CORPUS_FILES:
        text = _flatten(ROOT / rel)
        for match in re.finditer(r"27\.3", text):
            near = text[max(0, match.start() - window) : match.end() + window]
            if "17.8" not in near:
                offenders[rel] = near[:300]
                break

    new = set(offenders) - known_open
    assert not new, (
        "27.3% (FY2026 EBITDAR margin excluding forex) is published without "
        "17.8% (as reported) anywhere near it, in: "
        f"{sorted(new)}. Both must appear, and which is which must be stated. "
        "See gotcha 19 in CLAUDE.md.\n"
        + "\n".join(f"  {f}: ...{c}..." for f, c in offenders.items() if f in new)
    )
    closed = known_open - set(offenders)
    assert not closed, (
        f"{sorted(closed)} no longer violates the paired-margin rule. Remove it "
        "from `known_open` so the guard covers it from now on."
    )


def test_the_withdrawn_iata_claim_does_not_reappear():
    """IATA does publish a free O-D table, and this repo said for months that it did not.

    `data/manual/assumptions.csv` recorded "IATA sells O-D data and publishes no
    free table; there is no primary document to check against", and the
    value-at-stake chart told every reader on the live site that "The O-D share
    cannot be verified at all, because IATA sells that data". Both were wrong.
    IATA's `Aviation in India` is a free, public, machine readable PDF and its
    section 3.2 publishes India's departing international O-D by region and by
    country.

    What IATA sells is DDS, the route level product. The repo conflated the two
    and, because the claim was an argument for NOT looking, nothing ever tested
    it. That is the expensive kind of wrong: an unfalsifiable excuse embedded in
    the provenance layer.

    **This guard reaches past CORPUS_FILES on purpose.** The false sentence lived
    in `src/options.py` and was published through the exported chart JSON, and
    neither is in the narrative corpus. That is gotcha 39 in yet another costume:
    a surface carrying prose while exempt from the rule that governs prose.
    """
    withdrawn = (
        "IATA sells that data",
        "publishes no free table",
        "cannot be verified at all",
        "no free table",
    )

    targets = [ROOT / rel for rel in CORPUS_FILES]
    targets += sorted((ROOT / "src").glob("*.py"))
    targets += sorted((ROOT / "docs" / "assets" / "charts").glob("*.json"))

    # A retraction has to be able to quote the wording it retracts, or the record
    # cannot say what was withdrawn. Same opt-out the corpus fixture honours, in
    # the HTML comment form and in a `#` form for Python.
    ignore = re.compile(
        r"(<!--\s*narrative-guard:\s*ignore.*?-->.*?<!--\s*/narrative-guard\s*-->)"
        r"|(#\s*narrative-guard:\s*ignore.*?#\s*/narrative-guard)",
        re.S,
    )

    offenders = {}
    for path in targets:
        if not path.exists():
            continue
        text = ignore.sub(" ", path.read_text(encoding="utf-8", errors="ignore"))
        hit = [phrase for phrase in withdrawn if phrase in text]
        if hit:
            offenders[str(path.relative_to(ROOT)).replace("\\", "/")] = hit

    assert not offenders, (
        "The withdrawn IATA claim is published again. IATA's Aviation in India is "
        "free and publishes India's O-D split by region and country; what is sold "
        "is the route level DDS product. Offending files: "
        f"{offenders}"
    )


def test_the_gulf_second_source_claim_is_always_qualified_by_route_level():
    """"The Gulf has no equivalent open source" is only true at ROUTE level now.

    The withdrawn-IATA guard forbids specific phrasings and that is not enough.
    `web/app/methodology/page.tsx` carried the same belief in different words,
    "the Gulf, which carries half the traffic, has no equivalent open source",
    survived the whole 2026-08-19 correction pass, and was still published after
    eight other surfaces had been fixed. A phrase blacklist catches the sentence
    somebody wrote down, not the belief behind it.

    So this one is shaped like the paired-margin guard instead: the claim may
    appear, because at route level it is still true and load-bearing, but it must
    appear NEAR the qualifier that makes it true. IATA covers the Gulf at country
    level; no GCC authority publishes routes.
    """
    window = 400
    claims = ("no equivalent open source", "has no second agency")
    offenders = {}

    targets = [ROOT / rel for rel in CORPUS_FILES]
    targets += sorted((ROOT / "src").glob("*.py"))

    for path in targets:
        if not path.exists():
            continue
        text = _flatten(path)
        for claim in claims:
            for match in re.finditer(re.escape(claim), text):
                near = text[max(0, match.start() - window) : match.end() + window]
                if "route" not in near.lower():
                    offenders[str(path.relative_to(ROOT)).replace("\\", "/")] = near[:220]
                    break

    assert not offenders, (
        "A surface claims the Gulf has no second agency without qualifying it to "
        "ROUTE level. IATA covers the Gulf at country level since pivot 9; only "
        f"route-level cover is still Europe-only. Offenders: {offenders}"
    )


def test_the_guard_can_actually_fail(corpus):
    """A guard that cannot fail is not a guard.

    Mirrors `test_the_red_rule_can_actually_fail`. If the corpus fixture ever
    silently returns nothing, every assertion above passes for the wrong reason.
    """
    assert len(corpus) > 50_000, "the corpus looks empty, so the checks above prove nothing"
    assert "Wide-Body" in corpus
    probe = Claim("probe", lambda: 0.0, "{:.0f}", must_appear=("a phrase that is not present",))
    assert not [p for p in probe.must_appear if p in corpus]


def test_the_brief_does_not_reuse_the_decision_list_class():
    """A grid container silently voids every forced page break inside it.

    `docs/brief.html` shipped as `<body class="brief">`, and `.brief` was already
    taken by the decision list in `index.html`, where it is a grid. That made the
    brief's body a grid container and its two `.brief-page` sections grid items,
    and Chrome does not honour `page-break-after` between grid items. Both
    spellings of the break property were present, both correct, both inert. The
    printed PDF put the two audiences in side-by-side columns across both sheets.

    Nothing failed. The PDF existed, was the right size, and held every word. The
    only way to see it was to read the rendered layout, which is why this file
    now asserts the class rather than the output.
    """
    brief = (ROOT / "docs" / "brief.html").read_text(encoding="utf-8")
    css = (ROOT / "docs" / "assets" / "style.css").read_text(encoding="utf-8")

    assert 'class="brief"' not in brief, (
        "docs/brief.html is using the decision-list class again. That makes its body a "
        "grid container and Chrome will ignore the page breaks, without failing anything."
    )
    assert 'class="brief-doc"' in brief
    assert ".brief-doc {" in css, "the brief's own class is not defined in style.css"
    assert "page-break-after: always" in css
