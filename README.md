# India's Wide-Body Window

**Where should Indian carriers deploy their next 100 long-haul aircraft, and can the
India-Gulf corridor absorb them?**

**Live: [india-widebody-window.vercel.app](https://india-widebody-window.vercel.app)** (also mirrored on [GitHub Pages](https://doginfantry.github.io/india-widebody-window/))

> **Compete with the Gulf hubs. Do not fly more aircraft to them.** The corridor carries
> half of India's international traffic and is four times the entire direct Europe market,
> but about 8.5M of those passengers a year are going somewhere else entirely, and what
> treaty room remains in the Gulf would absorb about 4% of the aircraft on order. The
> wide-bodies win that traffic by flying past the Gulf, not to it. Europe first, North
> America second.

This was not the opening view. It was "reclaim the Gulf corridor first" until three separate
lines of evidence said the aircraft cannot be deployed there. That change, and five others,
are documented in [the pivot log](docs/pivot_log.md) rather than presented as though the
answer had always been obvious.

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

The consequence shows up in who flies the market. Indian carriers account for **45.9%** of
India's international sector passengers, against **26.2%** for Gulf carriers. In its own
market, the home industry is still the minority shareholder.

But the trend runs the other way, and that reversed the case's opening premise. Indian
carriers held **37.0%** in 2015 and hold 45.9% now, while Gulf carriers fell from 32.7% to
26.2%. They are not losing their home market, they are closing on parity. The deficit that
remains sits exactly where aircraft range binds: the share taken back is short-haul, and
long-haul needs the aircraft that have only just been ordered.

## Five things this repo does that a summary would not

**1. It computes the headline instead of quoting it.**
Secondary sources put the Gulf at "around 40%" of India's international traffic. This repo
computes **50.9%** from DGCA directly. Both are right: 50.9% is *sector* traffic, ~40% is
true *origin-destination*. The eleven point gap is passengers connecting through a Gulf hub
to somewhere else, and it is the case rather than a discrepancy to reconcile away.

**2. It checks the data against a second agency, and the check found something.**
Eurostat measures the same India-Europe routes from the European end. Across seven countries
both cover, DGCA and Eurostat agree to **2.6%** (Finland to 0.0%, Germany 1.3%, France
-0.9%). Italy diverges 37%, and the entire gap is one route: Eurostat reports 171,942
passengers on Rome to Delhi, DGCA lists no such pair. No free source settles it, so the
route is **quarantined**, excluded from anything depending on one agency being right, and
reported with both numbers.

**3. It refuses to use numbers nobody has checked, and the gate has cost it.**
DGCA publishes no fares and Air India is unlisted, so yields must be hand-entered. Every such
row carries a status and `dp.assumption()` raises rather than returning anything not
`VERIFIED`. The capacity leg of the market sizing sat **blocked** for most of this project's
life. It was unblocked by finding the sources, never by relaxing the rule, and note which way
that moved the answer: the new leg came in at 90.7M, the **low** end, so verifying the gated
numbers widened the band downward and made the recommendation harder to argue.

**4. It publishes the ten times it was wrong.**
[The pivot log](docs/pivot_log.md) records every change of mind with the commit it happened
in. A margin claim published on the site and withdrawn. A premise reversed. A bucket bug that
misfiled 5.0M passengers a year **while all 72 tests passed**, because a wrong bucket is still
a valid bucket. A widely quoted utilisation figure retired because it requires 100 of 441
aircraft to be grounded. Four of the six were caught by cross-checking one source against
another; none by the test suite.

**5. It reports its own gaps.**
`python -m src.gap_analyzer` maps the real job posting to artifacts and checks each exists.
It reports **82%**, not 100%, because the posting asks for survey analysis, mentoring and
first-level team management, and a solo repository cannot honestly evidence any of them. It
also caught a requirement I had invented that appears nowhere in the posting, and that row
was deleted rather than reworded.

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
```

`scripts/refresh.py` is the single entry point and exactly what CI runs: it pulls every
source, rebuilds all seventeen figures and recomputes the hero numbers from the parquet. No
figure on the page is typed by hand. `--no-fetch` rebuilds from cached parquet without going
to the network.

To read the site locally, serve `docs/` with any static file server and open `index.html`.
`report.html` is the same analysis laid out for printing, with a Save as PDF button.

## Layout

```
src/data_pipeline.py   fetch, clean, cache; the three DGCA traps handled once, here
src/benchmarking.py    carriers and corridors; stage length is the differentiating metric
src/market_sizing.py   three methods reconciled to a band, never averaged
src/fleet_gap.py       what the order book can fly, in ASK, against what the market needs
src/options.py         what each corridor must earn to cover its cost, and the option menu
src/profit_pools.py    corridor profit pool; the most heavily modelled module, every seam labelled
src/scenario.py        demand paths, plus fuel and FX on unit economics
src/charts.py          Bain palette builders; house rules enforced by tests
src/gap_analyzer.py    job posting to artifact coverage, checked not assumed
scripts/refresh.py     single entry point, and what CI calls
docs/                  the only copy of the site, served by GitHub Pages
```

| Document | What it holds |
|---|---|
| [Storyline](docs/storyline.md) | The client brief, the recommendation, and the SCQA under it |
| [Recommendation](docs/recommendation.md) | Five costed options, roadmap, risk register, leading indicators |
| [Pivot log](docs/pivot_log.md) | The ten times evidence turned the analysis, each citing its commit |
| [Hypothesis tree](docs/hypothesis_tree.md) | The decomposition, including branches still open |
| [Survey design](docs/survey_design.md) | A conjoint instrument for the softest number in the case. Designed, not fielded |
| [Methodology](docs/methodology.md) | Frameworks, limits, what the data cannot tell you, and the retraction |
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
