"""The delivery layer must not quietly get thinner than the analysis behind it.

**Why this file exists.** The Next.js app shipped with 11 exhibits against the
static site's 18, no narrative steps at all, and the client named nowhere, and
none of that failed anything. Every Python test passed, the build was green, and
the page rendered. The failure was invisible because the two surfaces had no
shared vocabulary to be counted against each other.

These tests give them one. `docs/index.html` keys every exhibit with a
`data-chart` id; `web/lib/exhibits.tsx` keys the same exhibits the same way. A
dropped exhibit is now an assertion failure rather than something a person has
to notice.

**Deliberately a text check, not a render check.** Rendering React from pytest
would mean a Node toolchain in CI for the sake of counting, and the failures
worth catching here (an exhibit vanished, the client is unnamed, a driver-tree
leaf points nowhere) are all visible in the source. `npm run build` already
catches everything that is a type or render error.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
REGISTRY = WEB / "lib" / "exhibits.tsx"
INDEX = ROOT / "docs" / "index.html"


@pytest.fixture(scope="module")
def registry() -> str:
    return REGISTRY.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def registry_ids(registry: str) -> list[str]:
    """The keys of EXHIBITS, in declaration order."""
    body = registry.split("export const EXHIBITS", 1)[1]
    body = body.split("/** Render one registry entry", 1)[0]
    return re.findall(r"^  ([a-z_]+): \{$", body, flags=re.M)


@pytest.fixture(scope="module")
def static_chart_ids() -> list[str]:
    return sorted(set(re.findall(r'data-chart="([^"]+)"', INDEX.read_text(encoding="utf-8"))))


def test_every_static_site_exhibit_has_an_app_counterpart(registry_ids, static_chart_ids):
    """Parity, counted rather than claimed.

    This is the test that would have failed on the day the app shipped. Eight
    exhibits were dropped, including the Sankey, the Mekko and the slope, which
    are the three most distinctive forms in the project.
    """
    missing = [c for c in static_chart_ids if c not in registry_ids]
    assert not missing, (
        f"{missing} are exhibits on docs/index.html with no counterpart in "
        "web/lib/exhibits.tsx. Either port them or record why not."
    )


def test_every_registered_exhibit_actually_renders_something(registry):
    """A registry entry with no chart is a promise the page does not keep."""
    assert "chart: null" not in registry
    assert registry.count("chart:") >= 20


def test_every_exhibit_carries_a_source_line(registry, registry_ids):
    """An exhibit without a source is an assertion.

    Counting rather than parsing: every entry declares exactly one `source`, so
    the counts must match or an entry is missing one.
    """
    assert registry.count("    source:") == len(registry_ids)


def test_the_tab_vocabulary_is_fixed_and_capped():
    """One grammar everywhere, four tabs maximum, never nested.

    The vocabulary lives in the component rather than in each page, so the way
    this drifts is someone adding a fifth name to it.
    """
    component = (WEB / "components" / "Exhibit.tsx").read_text(encoding="utf-8")
    vocab = re.search(r"TAB_VOCABULARY = \[(.*?)\] as const", component, re.S)
    assert vocab, "TAB_VOCABULARY is gone; the one-grammar rule has no anchor"
    names = re.findall(r'"([^"]+)"', vocab.group(1))
    assert names == ["Exhibit", "Evidence", "How it was computed", "What would break it"]
    assert len(names) <= 4


def test_no_page_builds_its_own_exhibit_disclosure(registry_ids):
    """Pages name an exhibit id. They do not reinvent the grammar.

    `/frameworks` still uses the raw `Exhibit` component for its framework
    diagrams, which is allowed: those are lists and tables rather than registry
    charts. What is not allowed is a page inventing a second disclosure pattern.
    """
    for page in (WEB / "app").rglob("page.tsx"):
        source = page.read_text(encoding="utf-8")
        assert "<details" not in source, (
            f"{page.relative_to(WEB)} builds its own disclosure. Use the Exhibit component."
        )


def test_the_client_is_named_above_the_fold():
    """The whole reason for this session's work.

    The analysis was IndiGo-anchored from the first commit and the delivery never
    said so, which is why it read as sector research. The frame is rendered from
    the export, so this checks the page reaches for it.
    """
    landing = (WEB / "app" / "page.tsx").read_text(encoding="utf-8")
    header = landing.split("</header>", 1)[0]
    for token in ("brief.client", "brief.decision", "brief.timeframe"):
        assert token in header, f"{token} is not rendered above the fold on the landing page"


def test_the_inverted_spread_reaches_every_surface_that_should_carry_it():
    """RASK against CASK, read from the export on each surface, never typed."""
    for page in ("page.tsx", "company/page.tsx", "deck/page.tsx"):
        source = (WEB / "app" / page).read_text(encoding="utf-8")
        assert "spread.rask" in source and "spread.cask" in source, (
            f"app/{page} does not state the inverted spread from the export"
        )
        assert "4.99" not in source, f"app/{page} types a figure that should be read"


def test_no_driver_tree_leaf_points_at_a_missing_exhibit(registry_ids):
    """A tree whose leaves dangle is decoration, which is what it was built not to be."""
    tree = (WEB / "components" / "DriverTree.tsx").read_text(encoding="utf-8")
    routes = {p.parent.name or "/" for p in (WEB / "app").rglob("page.tsx")}
    routes = {"/" if r == "app" else f"/{r}" for r in routes}

    for href in re.findall(r'href: "([^"]+)"', tree):
        route, _, anchor = href.partition("#")
        route = route or "/"
        assert route in routes, f"driver tree points at {route}, which is not a route"
        assert anchor.startswith("exhibit-")
        exhibit = anchor.removeprefix("exhibit-")
        assert exhibit in registry_ids, f"driver tree points at {exhibit}, not in the registry"

        rendered = (WEB / "app" / (route.strip("/") or ".") / "page.tsx").read_text(encoding="utf-8")
        assert (
            f'id="{exhibit}"' in rendered or "EXHIBIT" in rendered or "story" in rendered
        ), f"{route} does not render {exhibit}"


def test_the_app_reads_the_narrative_rather_than_restating_it(registry):
    """The Evidence tab comes from docs/index.html, parsed, not retyped.

    Gotcha 43 says index.html holds the prose and every other surface re-lays it
    out. That rule was written for the report and the deck; this makes the React
    surface obey it too, instead of becoming a fourth place the words live.
    """
    assert "story.find((s) => s.chart === id)" in registry


def test_docs_is_byte_unchanged():
    """Nothing was erased. The mirror keeps working and the PDFs stay valid."""
    diff = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", "docs/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert not diff.stdout.strip(), (
        "docs/ has uncommitted changes. The static site is the reproducible "
        f"mirror and must stay byte-identical:\n{diff.stdout}"
    )


def _deck_slides() -> list[str]:
    deck = (WEB / "app" / "deck" / "page.tsx").read_text(encoding="utf-8")
    slides = deck.split("const SLIDES: Slide[] = [", 1)[1].split("\nconst CONTENT_KINDS", 1)[0]
    return slides.split("\n  {\n")[1:]


def test_the_deck_sources_every_slide_that_shows_a_number():
    """A slide carrying a figure must say where it came from.

    The agenda and the section dividers are exempt and should be: they cite
    nothing, and inventing a source line for a list of section names would be
    provenance theatre. The rule is that anything showing an exhibit or an
    interpolated value carries a source.
    """
    for entry in _deck_slides():
        title = re.search(r"title: [`\"](.{0,60})", entry)
        shows_figures = "exhibit:" in entry or "${" in entry
        if 'kind: "divider"' in entry or not shows_figures:
            continue
        assert "source:" in entry, f"deck slide {title and title.group(1)!r} has no source line"


def test_every_deck_slide_a_presenter_speaks_to_has_a_note():
    """A deck with no notes is a deck only its author can give."""
    for entry in _deck_slides():
        title = re.search(r"title: [`\"](.{0,60})", entry)
        if 'kind: "divider"' in entry:
            continue
        assert "notes:" in entry, f"deck slide {title and title.group(1)!r} has no presenter note"


def test_the_deck_has_a_five_minute_path_and_it_is_actually_short():
    """One deck, two paths, so the short version cannot go stale on its own.

    Counted the way the component filters it: dividers declare `short` so the
    section structure survives an edit, but they are dropped from the short path
    at render, and counting the declaration instead of the effective path would
    let the short deck grow by four slides without failing.
    """
    entries = _deck_slides()
    short = [e for e in entries if "short: true," in e and 'kind: "divider"' not in e]
    assert short, "the deck declares no short path"
    assert len(short) <= 12, (
        f"{len(short)} slides in the five-minute path, which is not five minutes"
    )
    assert len(short) < len(entries), "the short path is the whole deck"
