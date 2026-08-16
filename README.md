# India's Wide-Body Window

**Where should Indian carriers deploy their next 100 long-haul aircraft, and can the
India-Gulf corridor absorb them?**

> **Reclaim the Gulf corridor first.** It carries half of India's international traffic and
> is four times the size of the entire direct Europe market, yet Indian carriers fly it with
> short-haul aircraft and cede the connecting passenger to Dubai, Doha and Abu Dhabi.
> Long-haul to the West is the second move, not the first.

A commercial aviation market entry case, built in the style of Bain Capability Network
Advanced Manufacturing & Services work. Python analysis layer, single-page scrollytelling
site, no PowerPoint and no Excel anywhere in the pipeline.

---

## The finding, in two numbers

In 2025 **IndiGo carried more international passengers than Air India** (16.7M against
10.7M) while flying **barely half the distance per passenger**: an average international
stage length of **2,643 km** against Air India's **5,316 km**.

IndiGo is not losing long-haul. It has never been able to fly it. That gap is what the
wide-body order exists to close, and it falls straight out of two published columns with no
assumption in between.

The consequence shows up in who flies the market. Indian carriers account for **45.3%** of
India's international sector passengers. Gulf carriers alone take **25.5%**. In its own
market, the home industry is the minority shareholder.

## Four things this repo does that a summary would not

**1. It computes the headline instead of quoting it.**
Secondary sources put the Gulf at "around 40%" of India's international traffic. This repo
computes **51.2%** from DGCA directly. Both are right: 51.2% is *sector* traffic, ~40% is
true *origin-destination*. The eleven point gap is passengers connecting through a Gulf hub
to somewhere else, and it is the case rather than a discrepancy to reconcile away.

**2. It checks the data against a second agency, and the check found something.**
Eurostat measures the same India-Europe routes from the European end. Across seven countries
both cover, DGCA and Eurostat agree to **2.6%** (Finland to 0.0%, Germany 1.3%, France
-0.9%). Italy diverges 37%, and the entire gap is one route: Eurostat reports 171,942
passengers on Rome to Delhi, DGCA lists no such pair. No free source settles it, so the
route is **quarantined**, excluded from anything depending on one agency being right, and
reported with both numbers.

**3. It refuses to use numbers nobody has checked.**
DGCA publishes no fares and Air India is unlisted, so yields must be hand-entered. Every
such row carries a status, and `dp.assumption()` raises rather than returning a value that
is not `VERIFIED`. The capacity leg of the market sizing is **blocked by this gate right
now**, and the chart says so on its face. A band built partly on unchecked numbers is worse
than one that names the missing leg.

**4. It reports its own gaps.**
`python -m src.gap_analyzer` maps the real job posting to artifacts and checks each exists.
It currently reports **82%**, not 100%, because the posting asks for survey analysis and
first-level team management and a solo repository cannot honestly evidence either. It also
caught a requirement I had invented that appears nowhere in the posting, and that row was
deleted rather than reworded.

## A trap worth naming

DGCA publishes distance columns in **thousands** while passenger counts are raw, and the
files say so nowhere. Taken at face value, the average Indian domestic passenger flies
0.98 km. The correction was confirmed three independent ways before being applied:

| Check | Result |
|---|---|
| Scale | Reproduces India's published 163.8bn domestic RPK for 2025 |
| Ratio | Computed load factor matches DGCA's own column to 0.25pp on the majors |
| Coherence | Aircraft-km and RPK columns independently give 588 and 589 km per departure |

Two tests guard it. Left uncaught it would have published a chart claiming Air India's
average international flight is 5 km.

---

## Run it

```bash
pip install -r requirements.txt
python scripts/refresh.py
python -m pytest -q
python -m http.server 8000 --directory docs
```

`scripts/refresh.py` is the single entry point and exactly what CI runs: it pulls every
source, rebuilds all eight figures and recomputes the hero numbers from the parquet. No
figure on the page is typed by hand.

## Layout

```
src/data_pipeline.py   fetch, clean, cache; the two DGCA traps handled once, here
src/benchmarking.py    carriers and corridors; stage length is the differentiating metric
src/market_sizing.py   three methods reconciled to a band, never averaged
src/charts.py          Bain palette builders; house rules enforced by tests
src/gap_analyzer.py    job posting to artifact coverage, checked not assumed
scripts/refresh.py     single entry point, and what CI calls
docs/                  the only copy of the site, served by GitHub Pages
```

| Document | What it holds |
|---|---|
| [Storyline](docs/storyline.md) | SCQA, and what would change the recommendation |
| [Hypothesis tree](docs/hypothesis_tree.md) | The decomposition, including branches still open |
| [Methodology](docs/methodology.md) | Frameworks, limits, and what the data cannot tell you |
| [Data dictionary](data/data_dictionary.md) | Every field: source, pull date, reliability grade |
| [Coverage](docs/coverage.md) | Job posting mapped to artifacts, gaps included |
| [Alternative B](docs/alternative_b_datacenters.md) | The case that lost, and why |

## Data

All free, all machine readable, all reproducible.

| Source | Role | Licence |
|---|---|---|
| DGCA traffic statistics | Spine. Five datasets, fresh to May 2026 | ODbL via community mirror |
| Eurostat `avia_par` | European end of India-Europe routes, for reconciliation | EU reuse policy |
| World Bank Open Data | Income, population, air travel propensity across 12 peers | CC BY 4.0 |
| OurAirports | Airport reference and coordinates | CC0 |

Two sources were attempted once and dropped rather than scraped unreliably: BTS T-100 and
Indian Oil fuel prices. The United States arm is therefore measured from the India side
only, and `docs/methodology.md` says so.

## Licence and attribution

MIT. The Mekko builder is adapted from [Vizro](https://github.com/mckinsey/vizro) under
Apache-2.0, whose chart taxonomy derives from the FT Visual Vocabulary (MIT). Full
attribution in [`NOTICE`](NOTICE).
