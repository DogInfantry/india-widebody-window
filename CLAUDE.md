# CLAUDE.md

## What this is

A recruiter-facing portfolio project that mimics Bain Capability Network (BCN) Advanced
Manufacturing & Services commercial aviation casework, targeting the Associate AMS CoE role.

Case question: **"India's Wide-Body Window: where should Indian carriers deploy their next 100
long-haul aircraft, and can the India-Gulf corridor absorb them?"**

Deliverable is a Python analysis layer plus a single-page scrollytelling site served from
`docs/` by GitHub Pages. Nothing else.

**Read `PROJECT_STATE.md` first on any resume.** It holds the phase table, verified figures,
decisions log, and blockers. Dated snapshots are in `memory/`.

---

## Hard rules

### Writing

- **No em dashes. Anywhere.** Use a comma, a colon, parentheses, or a full stop.
- Hyphens only for standard compound terms (`wide-body`, `long-haul`, `answer-first`,
  `city-pair`, `point-to-point`). Never as decoration between words that do not need joining.
- **This is not a research paper.** No abstract, no literature review, no "this study finds",
  no academic hedging. Executive summary, recommendation, evidence. Answer first, always.
- Chart titles state the takeaway, never the topic. "IndiGo leads domestic but cedes the Gulf
  connect premium", not "Market share by carrier".

### Deliverables

- No PowerPoint. No Excel. Not as an output, not as an intermediate.
- No supply chain framing. This is market strategy, go to market, profit pools, and
  competitive benchmarking.

### Data integrity

- **Every hard number is either computed in-repo from a committed dataset, or carries a source
  URL and pull date in `data/data_dictionary.md`.** A number that fails this test does not
  appear on the page.
- Modeled numbers are labelled modeled **on the chart itself**, not in a footnote. Profit pool
  margins are modeled. Say so on the chart.
- Conflicts get flagged, never silently resolved. Standing list:
  - Air India post-merger fleet reported as 198 / 205 / 218 depending on source and date
  - India passenger totals differ by definition: World Bank 180.4M carriers-carried (2023),
    IATA 211M passengers (2024), DGCA 406M airport-handled (2025). State the definition each time
  - DGCA sector traffic versus IATA true origin-destination. This one is not a problem to hide,
    it is the finding

---

## Architecture

```
src/data_pipeline.py   fetch, clean, cache, expose load_* returning tidy DataFrames
src/market_sizing.py   three independent methods reconciled to a BAND, never averaged
src/benchmarking.py    carriers and hubs, stage length is the differentiating metric
src/profit_pools.py    value chain revenue against margin, margins are modeled
src/scenario.py        base / bull / bear over demand, fuel, FX
src/charts.py          Bain palette Plotly builders, one shared template
src/gap_analyzer.py    jd.txt to artifact coverage report
scripts/refresh.py     single entry point, and exactly what CI calls
docs/                  the ONLY copy of the site. Never mirror it
```

Data flows one way: source, to `data/raw/` with a date stamp, to `data/processed/*.parquet`,
to module, to `docs/assets/charts/*.json`, to the page. No step is skipped.

### Palette

`#CC0000` primary red, `#EE3224` accent, `#1A1A1A` ink, `#E6E6E6` and `#999999` neutrals.
Inter or system sans. **One red element per chart**, everything else grey. Minimal gridlines.

### Dependency discipline

`requirements.txt` is deliberately short. Already rejected with reasons in `PROJECT_STATE.md`:
duckdb, pyopensky, pdfplumber, vizro, dash, streamlit, panel. Do not reintroduce them.
The page budget is three CDN scripts: Plotly.js, scrollama.js, and Perspective below the fold.

Third party code carries attribution in `NOTICE`. `src/charts.py` `mekko()` is adapted from
Vizro under Apache-2.0.

---

## Commands

```bash
pip install -r requirements.txt
python -m pytest -q
python scripts/refresh.py
python -m http.server 8000 --directory docs
```

---

## Working agreements

- Commit at the end of every phase with a descriptive message.
- The repo stays local until Phase 5. Ask before `gh repo create` or any push.
- Timeboxed data loaders (BTS T-100, UK CAA) fail soft. One attempt. If a loader resists, drop
  it, measure that arm from the India side only, and say so plainly in `docs/methodology.md`.
  A documented single-sided measurement beats an undocumented scrape that breaks in CI.
- Framework prose comes from `DogInfantry/claude-skill-management-consultant-B1`, which already
  has 146 reference modules. Cite it, do not rewrite it.
