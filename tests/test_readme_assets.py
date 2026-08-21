"""The front page is a surface, so it inherits the guards every surface gets.

`scripts/make_readme_charts.py` draws four charts from `web/public/data/*.json`
and commits the SVG, because GitHub renders no JavaScript and the Plotly exports
the site reads are useless to it.

**The reason this committed asset is guarded and the other two are not.**
`scripts/make_social_card.py` ends its docstring with "re-run it only if the hero
numbers change", and `scripts/make_basemap.py` says much the same. That is a
manual step nothing checks, and this repo has found that exact shape of failure
four separate times: the exhibit count drifted to 20 against 26 because a subset
check is not a count, the pivot count drifted twice across seven hand-written
surfaces, a bucket bug misfiled 5.0M passengers a year while 72 tests passed, and
a published type-check command never type-checked anything. A basemap is a
coastline and does not move. A chart of the headline numbers moves every time the
headline does, and the README is where a recruiter looks first.

So this file asks the three questions that matter:

    drift          the committed SVG is what the current data produces
    determinism    building twice gives the same bytes, so drift means drift
    structure      the README actually shows them, in a themed pair, with alt text

The structure test is the one that catches the quiet failure. A `<picture>` whose
dark `<source>` is missing looks perfect to whoever wrote it in light mode and
renders a chart in the wrong ink for every reader in dark mode. An `<img>` with no
`alt` is invisible to a screen reader and to the answer engines this README is
partly written for, and nothing else in the repo would ever say so.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / ".github" / "assets"
README = ROOT / "README.md"


def _module():
    """`scripts/` is not a package, so load the generator by path."""
    spec = importlib.util.spec_from_file_location(
        "make_readme_charts", ROOT / "scripts" / "make_readme_charts.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def built() -> dict[str, str]:
    return _module().build()


def test_the_committed_charts_are_what_the_current_data_draws(built):
    """The guard. A moved number fails the build instead of ageing on the front page."""
    stale = []
    for filename, markup in built.items():
        path = ASSETS / filename
        if not path.exists():
            stale.append(f"{filename}: never committed")
        elif path.read_text(encoding="utf-8") != markup:
            stale.append(f"{filename}: differs from what the data now draws")

    assert not stale, (
        "The committed README charts no longer match the data they were drawn from:\n  "
        + "\n  ".join(stale)
        + "\n\nRun `python scripts/make_readme_charts.py` and commit the result. If a "
        "headline number moved, sweep the README prose in the same commit and add the "
        "old value to `must_not_appear` in tests/test_narrative.py."
    )


def test_the_build_is_deterministic():
    """Two builds, same bytes. Otherwise the drift test cries wolf and gets deleted."""
    first, second = _module().build(), _module().build()
    assert first == second, "the generator is not deterministic, so the drift guard is noise"


def test_the_guard_can_actually_fail(built):
    """A guard that cannot fail is worth less than none, because it is trusted.

    Mirrors `test_the_guard_can_actually_fail` in `tests/test_narrative.py` and
    the same idea in `test_the_red_rule_can_actually_fail`. This is gotcha 72:
    the published type-check command printed tsc's help and exited 0, and was
    reported as clean several times.
    """
    assert len(built) == 8, "four charts in two themes, so eight files"
    for filename, markup in built.items():
        assert markup.startswith("<svg "), f"{filename} is not an SVG"
        assert markup.count("<text") >= 6, f"{filename} drew almost nothing"
    assert built["answer_headroom-light.svg"] != built["answer_headroom-dark.svg"], (
        "the two themes produced identical bytes, so the dark variant is not themed"
    )


def test_every_chart_the_readme_shows_is_a_themed_pair_with_alt_text():
    """A missing dark `<source>` looks perfect to whoever wrote it in light mode."""
    readme = README.read_text(encoding="utf-8")
    blocks = re.findall(r"<picture>(.*?)</picture>", readme, flags=re.S)
    assert blocks, "the README shows no charts at all"

    problems = []
    for block in blocks:
        src = re.search(r'<img[^>]*\bsrc="([^"]+)"', block)
        alt = re.search(r'<img[^>]*\balt="([^"]*)"', block)
        dark = re.search(r'<source[^>]*prefers-color-scheme:\s*dark[^>]*srcset="([^"]+)"', block)

        if not src:
            problems.append("a <picture> with no <img> fallback")
            continue
        light_path = ROOT / src.group(1)
        if not light_path.exists():
            problems.append(f"{src.group(1)} is referenced but not committed")
        if not dark:
            problems.append(f"{src.group(1)} has no prefers-color-scheme dark <source>")
        elif not (ROOT / dark.group(1)).exists():
            problems.append(f"{dark.group(1)} is the dark variant and is not committed")
        # 40 characters is roughly "the finding and its unit". Alt text is the
        # only version of these charts a screen reader or a retrieval model ever
        # sees, so "chart of corridors" is a failure, not a shortcut.
        if not alt or len(alt.group(1).strip()) < 40:
            problems.append(f"{src.group(1)} has alt text too short to carry the finding")

    assert not problems, "README chart markup:\n  " + "\n  ".join(problems)


def test_no_committed_chart_is_orphaned():
    """An SVG nobody shows is an SVG nobody notices going stale."""
    readme = README.read_text(encoding="utf-8")
    orphans = sorted(
        p.name for p in ASSETS.glob("*.svg")
        if f".github/assets/{p.name}" not in readme
    )
    assert not orphans, (
        f"{orphans} are committed under .github/assets but the README never shows them. "
        "Show them or delete them."
    )


def test_the_readme_engagement_card_matches_the_site_hero():
    """The README is a hand-written surface, so it gets a parity check like the rest.

    `docs/index.html` carries the engagement in a `<dl class="brief">`: client,
    decision, opponent, horizon. The README now states the same four rows, and a
    hand-written restatement of a fact held somewhere else is exactly the thing
    that drifted eight times in this repository before anything counted it.

    Extra rows in the README are allowed. Dropping one, or contradicting one, is
    not. That is the same asymmetry the exhibit parity test uses: the delivery
    surface may say more than the analysis surface, never less.
    """
    index = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    pairs = re.findall(r"<dt>([^<]+)</dt><dd>([^<]+)</dd>", index)
    assert len(pairs) == 4, f"docs/index.html hero brief has {len(pairs)} rows, expected 4"

    flat = re.sub(r"\s+", " ", readme)
    missing = [
        f"{term}: {definition}"
        for term, definition in pairs
        if f"| **{term}** | {definition} |" not in flat
    ]
    assert not missing, (
        "the README engagement card has drifted from the hero brief in "
        "docs/index.html, which is where the engagement is actually stated:\n  "
        + "\n  ".join(missing)
    )
