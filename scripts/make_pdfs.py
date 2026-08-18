"""Render the brief and the full report to committed PDFs.

**Why a file and not a button.** The site already prints well and `report.html`
carries a Save as PDF control, but that asks the reader to do the work. People
forward attachments; they rarely stop to print a web page first. So the PDFs are
generated once and committed, and anyone can attach them to an email without
visiting anything.

**Why local Chrome and not Puppeteer.** The external review that prompted this
recommended a serverless Puppeteer route with `@sparticuz/chromium`. That solves
a problem this project does not have: it needs a Node toolchain, a cold-starting
function, and a host that runs code, in return for producing a file that changes
about as often as the headline does. Chrome is already installed, it renders the
same print CSS the browser does, and the output is a static asset like any other.

**Deliberately not part of `refresh.py` and not run by CI**, for the same reason
as `make_social_card.py`: these are artifacts, not figures. `requirements.txt`
stays at seven packages, because this needs no Python library at all.

    python scripts/refresh.py --no-fetch     # so the charts are current
    # serve docs/ on :8000, then
    python scripts/make_pdfs.py

The server matters: both pages fetch `index.html` and the chart JSON at load, so
opening them from disk produces an empty document. The script checks for that
rather than silently writing a blank PDF, which is the failure mode most worth
catching here.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASE = "http://localhost:8000"

# Standard install locations. Edge renders the same engine and is the fallback,
# because a machine with neither is not one this script can help.
CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

PAGES = (
    ("brief.html", "india-widebody-brief.pdf", "the two-page brief"),
    ("report.html", "india-widebody-window.pdf", "the full report"),
)

# Minimum plausible size. A PDF of an empty page is a few kilobytes, so anything
# under this means the page did not finish loading and the output is worthless.
MIN_BYTES = 40_000


def find_browser() -> str:
    for path in CANDIDATES:
        if Path(path).exists():
            return path
    found = shutil.which("chrome") or shutil.which("chromium") or shutil.which("msedge")
    if found:
        return found
    raise SystemExit(
        "No Chrome or Edge found. Install one, or add its path to CANDIDATES. "
        "This script deliberately has no Python PDF dependency."
    )


def check_server() -> None:
    try:
        with urllib.request.urlopen(f"{BASE}/index.html", timeout=5) as r:
            if r.status != 200:
                raise SystemExit(f"{BASE}/index.html returned HTTP {r.status}")
    except (urllib.error.URLError, OSError) as exc:
        raise SystemExit(
            f"Nothing is serving {BASE}. Both pages fetch index.html and the chart JSON at "
            f"load, so printing from disk yields a blank document.\n"
            f"Start the site first (preview_start, config name 'site'), then re-run.\n"
            f"  underlying error: {exc}"
        ) from exc


def render(browser: str, page: str, out: Path) -> None:
    subprocess.run(
        [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            # The pages render their charts asynchronously. Without a virtual time
            # budget Chrome prints whatever exists at first paint, which is a
            # document full of empty chart boxes.
            "--virtual-time-budget=30000",
            "--run-all-compositor-stages-before-draw",
            # Chrome renamed this; pass both so it works either side of the change.
            "--print-to-pdf-no-header",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out}",
            f"{BASE}/{page}",
        ],
        check=True,
        capture_output=True,
        timeout=180,
    )


def main() -> int:
    browser = find_browser()
    check_server()
    print(f"rendering with {browser}\n")

    for page, filename, label in PAGES:
        out = DOCS / filename
        render(browser, page, out)
        if not out.exists():
            raise SystemExit(f"{page}: no PDF produced")
        size = out.stat().st_size
        if size < MIN_BYTES:
            raise SystemExit(
                f"{filename} is only {size:,} bytes, which means {page} rendered empty. "
                "Check the site is serving and the charts load."
            )
        print(f"  {filename:<32} {size:>9,} bytes   {label}")

    print("\nStatic artifacts. Commit them; refresh.py does not rebuild them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
