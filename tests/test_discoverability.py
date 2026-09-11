"""The surfaces machines read, and the guards they inherit on the way in.

`llms.txt` and the JSON-LD arrived together and were guarded on arrival, which is
the lesson `web/` taught the hard way: a new delivery surface inherits ZERO guards
unless it is added to them, and `web/` sat outside the narrative corpus and outside
any parity count for its whole life. `robots.txt` and `sitemap.xml` are two more
such surfaces, so they get their tests in the same commit rather than two sessions
later.

**The sitemap is walked against the real route list, never trusted.** A sitemap
that silently misses a route is exactly the shape this repo has found four times
over: the exhibit count that drifted to 20 against 26 because a subset check is
not a count, the pivot count that drifted twice, and the type-check command that
never type-checked. `web/app/*/page.tsx` IS the route list, so that is what the
test reads.

**There is deliberately no `docs/robots.txt`, and this is the place that says so.**
A crawler fetches `robots.txt` only from the origin root. The mirror is a GitHub
project page at `https://doginfantry.github.io/india-widebody-window/`, so a file
committed to `docs/` would be served at `/india-widebody-window/robots.txt` and
nothing would ever ask for it. The origin root belongs to whichever repository
publishes the user page, which is not this one. A robots.txt that cannot be
fetched is gotcha 72 in another costume: a control that looks like verification
and is not. `docs/sitemap.xml` is different and does exist, because a sitemap is
useful at its own URL and when submitted directly.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VERCEL = "https://india-widebody-window.vercel.app"
PAGES = "https://doginfantry.github.io/india-widebody-window/"


def _locs(path: Path, base: str) -> set[str]:
    xml = path.read_text(encoding="utf-8")
    return set(re.findall(rf"<loc>{re.escape(base)}([^<]*)</loc>", xml))


def test_the_sitemap_lists_every_route_the_app_builds():
    """The route list is walked. A route added without a sitemap entry fails here."""
    routes = {"/"} | {
        "/" + p.parent.name for p in (ROOT / "web" / "app").glob("*/page.tsx")
    }
    assert len(routes) >= 7, "the app route glob stopped matching, so this proves nothing"
    listed = _locs(ROOT / "web" / "public" / "sitemap.xml", VERCEL)
    assert listed == routes, (
        f"sitemap drift. Missing {sorted(routes - listed)}, "
        f"extra {sorted(listed - routes)}."
    )


def test_the_sitemap_urls_match_the_canonical_url_shape():
    """`vercel.json` sets cleanUrls and trailingSlash false, so the sitemap must too.

    A sitemap that advertises a URL which redirects is a sitemap that spends its
    crawl budget on redirects.
    """
    listed = _locs(ROOT / "web" / "public" / "sitemap.xml", VERCEL)
    offenders = [
        u for u in listed
        if u != "/" and (u.endswith("/") or u.endswith(".html"))
    ]
    assert not offenders, f"{offenders}: canonical URLs carry no extension and no trailing slash"


def test_the_mirror_sitemap_lists_the_four_pages_surfaces():
    listed = _locs(ROOT / "docs" / "sitemap.xml", PAGES)
    assert listed == {"", "deck.html", "report.html", "brief.html"}
    for name in listed:
        if name:
            assert (ROOT / "docs" / name).exists(), f"{name} is in the sitemap and not on disk"


def test_robots_points_at_the_sitemap_and_blocks_nothing():
    robots = (ROOT / "web" / "public" / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {VERCEL}/sitemap.xml" in robots
    assert "Allow: /" in robots
    blocking = [ln for ln in robots.splitlines() if ln.strip().startswith("Disallow:")
                and ln.split(":", 1)[1].strip()]
    assert not blocking, f"{blocking}: everything here is public and meant to be read"


def test_there_is_no_mirror_robots_txt():
    """Inverting the test that would have guarded it, rather than leaving a gap.

    See the module docstring. If this ever needs to become a real robots.txt,
    the repository will have moved to an origin it controls, and then this test
    is the thing to invert.
    """
    assert not (ROOT / "docs" / "robots.txt").exists(), (
        "docs/robots.txt cannot be fetched: a crawler reads robots.txt only from "
        "the origin root, and the mirror is a project page under a path. Delete it, "
        "or move the site to an origin this repository controls."
    )


def test_the_two_llms_files_are_the_same_bytes():
    """One document, two roots, and nothing checked they agreed.

    `docs/llms.txt` is served by GitHub Pages and `web/public/llms.txt` by Vercel.
    Neither host can serve the other's copy: `.vercelignore` excludes `/docs`, and
    Pages serves only `docs/`. The duplication is necessary; the drift is not.
    This is gotcha 57, where a whole surface sat exempt from a rule everything
    else obeyed.
    """
    a = (ROOT / "docs" / "llms.txt").read_bytes()
    b = (ROOT / "web" / "public" / "llms.txt").read_bytes()
    assert a == b, (
        "docs/llms.txt and web/public/llms.txt have diverged. They are the same "
        "document served from two roots; copy one over the other."
    )
