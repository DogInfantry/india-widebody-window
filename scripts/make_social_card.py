"""Generate the social preview card and favicon. Run once, commit the output.

**Deliberately not part of `refresh.py` and not run by CI.** These are static brand
assets, not figures: they change when the headline changes, which is roughly never,
and rebuilding them monthly would only add churn. `requirements.txt` therefore
stays at seven packages, because matplotlib is needed here and nowhere else.

The numbers on the card are read from `docs/assets/charts/kpis.json`, the same file
the page renders from, so the card cannot quietly disagree with the site. If the
KPIs move, re-run this and commit the new PNG.

**On the typeface.** IBM Plex is not installed here, so the card is set in Georgia
and Segoe UI. That is not an arbitrary substitution: those are the first fallbacks
the site's own stylesheet declares for the display and body faces, so a reader
without Plex already sees the page this way.

    python scripts/make_social_card.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"

RED = "#CC0000"
INK = "#1A1A1A"
GREY = "#999999"
LIGHT = "#E6E6E6"
PAPER = "#FFFFFF"

# The site's declared fallbacks, see the module docstring.
SERIF = "Georgia"
SANS = "Segoe UI"

HEADLINE = "India's Wide-Body Window"
EYEBROW = "COMMERCIAL AVIATION  ·  INDIA AND THE GULF"
ANSWER = "Compete with the Gulf hubs.\nDo not fly more aircraft to them."
URL = "india-widebody-window.vercel.app"


def _kpis() -> list[tuple[str, str]]:
    """The hero numbers, read from what the page actually renders."""
    path = ASSETS / "charts" / "kpis.json"
    if not path.exists():
        raise SystemExit(
            f"{path} is missing. Run `python scripts/refresh.py --no-fetch` first, "
            "so the card is built from the same numbers as the page."
        )
    cards = json.loads(path.read_text(encoding="utf-8"))
    return [(c["value"], c["label"]) for c in cards[:3]]


def _wrap(text: str, width: int) -> str:
    """Greedy wrap. textwrap would do, but this keeps it to two lines maximum."""
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if len(trial) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return "\n".join(lines[:2])


def build_card(out: Path) -> Path:
    """1200x630, the size every platform crops to."""
    fig = plt.figure(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 630)
    ax.axis("off")

    # The one red element, spent on a rule rather than on the type: the same
    # discipline the charts follow.
    ax.add_patch(patches.Rectangle((72, 548), 96, 7, facecolor=RED, edgecolor="none"))

    ax.text(72, 512, EYEBROW, fontfamily=SANS, fontsize=15, color=GREY,
            fontweight="600", va="top")
    # 52pt, not 62. At 62 the headline ran off the right edge of the canvas,
    # which is invisible in code and obvious the moment you look at the PNG.
    ax.text(72, 470, HEADLINE, fontfamily=SERIF, fontsize=52, color=INK,
            fontweight="bold", va="top")
    ax.text(72, 366, ANSWER, fontfamily=SERIF, fontsize=30, color=INK,
            va="top", linespacing=1.35)

    # Hairline above the figures, matching the page's answer block.
    ax.add_patch(patches.Rectangle((72, 214), 1056, 1, facecolor=LIGHT, edgecolor="none"))

    for i, (value, label) in enumerate(_kpis()):
        x = 72 + i * 352
        ax.text(x, 182, value, fontfamily=SANS, fontsize=44, color=RED,
                fontweight="600", va="top")
        # Wrapped over two lines rather than truncated. The first version cut the
        # labels off with an ellipsis, which loses the only thing that tells a
        # reader what the number counts.
        ax.text(x, 124, _wrap(label, 26), fontfamily=SANS, fontsize=14,
                color=INK, va="top", linespacing=1.4)

    ax.text(72, 46, URL, fontfamily=SANS, fontsize=14, color=GREY, va="bottom")
    ax.text(1128, 46, "Portfolio case study  ·  Apache-2.0 licensed", fontfamily=SANS,
            fontsize=14, color=GREY, va="bottom", ha="right")

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=PAPER, dpi=100)
    plt.close(fig)
    return out


# A rising line inside an ink square: the stage-length gap, which is the case in
# one mark. Kept to two shapes because anything finer is mud at 16 pixels.
FAVICON_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" fill="{INK}"/>
  <path d="M12 46 L34 46" stroke="{GREY}" stroke-width="7" stroke-linecap="square"/>
  <path d="M12 46 L52 18" stroke="{RED}" stroke-width="7" stroke-linecap="square"/>
</svg>
"""


def build_favicon(out: Path) -> Path:
    out.write_text(FAVICON_SVG, encoding="utf-8")
    return out


def main() -> int:
    card = build_card(ASSETS / "social-card.png")
    icon = build_favicon(ASSETS / "favicon.svg")
    for p in (card, icon):
        print(f"wrote {p.relative_to(ROOT)}  ({p.stat().st_size:,} bytes)")
    print("\nStatic assets. Commit them; refresh.py does not rebuild them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
