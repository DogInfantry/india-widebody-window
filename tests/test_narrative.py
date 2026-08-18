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

    **Run per file, with one named exception.** `docs/methodology.md` quotes
    27.3% inside the retraction passage without 17.8% beside it. That is a real
    violation, it predates this guard, and it is listed rather than exempted by
    a looser rule so it stays visible. Fixing it means editing the passage and
    deleting the entry below, which is the invert-the-gate discipline this
    project already runs on: when a gate opens, remove the exception rather than
    relax the test.
    """
    known_open = {"docs/methodology.md"}
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
