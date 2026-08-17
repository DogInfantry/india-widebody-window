# CLAUDE.md

## Project

**India's Wide-Body Window.** A recruiter-facing portfolio project mimicking Bain Capability
Network (BCN) Advanced Manufacturing & Services commercial aviation casework, targeting the
Associate AMS CoE role in Gurugram.

Case question: **"India's Wide-Body Window: where should Indian carriers deploy their next 100
long-haul aircraft, and can the India-Gulf corridor absorb them?"**

- **Live site:** https://doginfantry.github.io/india-widebody-window/
- **Repo:** https://github.com/DogInfantry/india-widebody-window (public, MIT)
- **Stack:** Python (pandas, numpy, pyarrow, plotly, requests, lxml, pytest). Static site,
  three CDN scripts (Plotly.js, scrollama.js, Perspective below the fold). No build step.
- **The real job description is in `jd.txt`**, extracted from the posting PDF.

---

## Hard rules

### Writing
- **No em dashes. Anywhere.** Comma, colon, parentheses, or a full stop.
- Hyphens only for standard compounds (`wide-body`, `long-haul`, `city-pair`). Never decorative.
- **Not a research paper.** No abstract, no literature review, no "this study finds". Executive
  summary, recommendation, evidence. Answer first, always.
- Chart titles state the takeaway, never the topic. A test enforces this.

### Deliverables
- No PowerPoint. No Excel. Not as output, not as intermediate.
- No supply chain framing. Market strategy, go to market, profit pools, benchmarking.
  (Note: the real JD *does* list "logistics & transport" as an AMS sub-sector, so this is a
  personal preference, not a JD requirement. Kept anyway.)

### Data integrity
- **Every hard number is either computed in-repo from committed data, or carries a source URL
  and pull date in `data/data_dictionary.md`.**
- Modelled numbers are labelled **on the chart face**, not in a footnote. Pass `modeled=True`
  to `charts.finish()`; do not hand-write "MODELLED" into a subtitle.
- Conflicts are flagged, never silently resolved.
- Hand-entered numbers go in `data/manual/assumptions.csv` and are gated: `dp.assumption()`
  raises unless status is `VERIFIED` or `CORRECTED_VERIFIED`.
- **Commits are authored as DogInfantry with no `Co-Authored-By` trailer.** The user asked for
  this explicitly; earlier commits had the trailer stripped via `filter-branch`.

---

## Architecture

Data flows one way and no step is skipped:

```
source -> data/raw/<name>_<YYYYMMDD>.{csv,json}   (gitignored, regenerable)
       -> tidy DataFrame                           (transformations in _build_* functions)
       -> data/processed/*.parquet                 (COMMITTED; what tests read)
       -> docs/assets/charts/*.json                (COMMITTED; what the page reads)
       -> docs/index.html
```

**Loaders read the committed parquet by default.** They only hit the network when
`force=True`. This is deliberate: it makes the test suite deterministic and offline, because
CI has no `data/raw/` cache and a flaky upstream should not turn the build red.

### Key decisions and why
- **Static site, not Streamlit/Panel/Superset/Redash/Vizro-as-framework.** All need a running
  process; GitHub Pages serves static files. Vizro adopted as a *code reference* only.
- **No DuckDB.** Whole corpus is ~90k rows, ~15 MB. pandas holds it in memory.
- **OpenSky dropped.** DGCA city-pair passenger counts beat frequency inferred from ADS-B.
- **`docs/` is the only copy of the site.** Never mirror it.
- **Market sizing reports a BAND, never an average.** The spread is the useful output.
- **Demand levers and unit-economics levers are kept apart.** Fuel and FX change what a
  passenger is worth, not how many there are. Folding them into the demand paths would imply
  a price elasticity nobody here has measured.

### Palette and type
`#CC0000` primary red, `#EE3224` accent, `#1A1A1A` ink, `#E6E6E6`/`#999999` neutrals.
**One red element per chart** (a test enforces it), everything else grey, minimal gridlines.

**IBM Plex Serif for display, IBM Plex Sans for body and all chart labels.** Serif is confined
to h1/h2/h3, the case question, the governing thought, and chart titles; anything at 13px or
below stays sans. `src/charts.py` holds `FONT` and `FONT_DISPLAY`. Changing type means changing
`style.css` and `charts.py` together, then re-running `scripts/refresh.py`, because the font is
baked into every exported chart JSON.

### Dependency discipline
`requirements.txt` is deliberately seven packages. Already rejected with reasons: duckdb,
pyopensky, pdfplumber, vizro, dash, streamlit, panel. Do not reintroduce them.
Third party attribution in `NOTICE`; `charts.py::mekko()` is adapted from Vizro (Apache-2.0).

---

## File map

| Path | Role |
|---|---|
| `src/data_pipeline.py` | Fetch, clean, cache. All three DGCA traps handled here, once. ~935 lines |
| `src/charts.py` | Bain palette builders. House rules as code, enforced by tests |
| `src/benchmarking.py` | Carriers and corridors. Stage length is the differentiating metric. Also holds `is_gulf_point()` and the bilateral seat check |
| `src/market_sizing.py` | Three methods to a band. `_ORDER_BOOK` holds the wide-body variant mix |
| `src/profit_pools.py` | Corridor profit pool. Most heavily modelled module; every seam labelled |
| `src/scenario.py` | All three levers: demand paths, plus fuel and FX on unit economics |
| `src/gap_analyzer.py` | Maps `jd.txt` to artifacts, checks each exists. Reports 82% |
| `scripts/refresh.py` | **Single entry point, and exactly what CI runs** |
| `docs/index.html` | The site. 13 scrolly steps + reconciliation table + methodology |
| `docs/assets/{style.css,scrolly.js}` | Sticky-graphic scrollytelling, mobile stacks |
| `docs/{storyline,hypothesis_tree,methodology,coverage,alternative_b_datacenters}.md` | Written IP |
| `data/data_dictionary.md` | Provenance contract. Every field, source, pull date, grade |
| `data/manual/assumptions.csv` | Hand-entered numbers, 11-state status vocabulary |
| `tests/test_pipeline.py` | Loaders, units, anomalies, provenance |
| `tests/test_analysis.py` | Findings, chart house rules, sizing, scenarios, profit pools, bilaterals |
| `.claude/launch.json` | `preview_start` config for serving `docs/` without orphaning a server |
| `.github/workflows/refresh.yml` | Monthly cron. Tests, refresh, tests again, commit |
| `PROJECT_STATE.md` | **STALE.** Still describes the 2026-08-15 state. Not maintained |

---

## Current state

**Done and green.** 77 tests pass. 13 charts. CI green. Site live. In sync with origin/main.
Working tree clean. All of the previous handoff's next steps are complete.

**The findings, all computed from DGCA unless noted:**
- India international sector pax 2024: **72.2M**, Gulf six **51.2%**, UAE alone 21.5M
- The Gulf corridor is **4.2x** India's entire direct Europe market (36.9M vs 8.8M)
- **The core finding:** IndiGo carried 16.7M international pax in 2025 to Air India's 10.7M,
  at **2,643 km** average stage length against **5,316 km**. Same market, different aircraft.
- **Premise reversed mid-project:** Indian carriers are *not* losing. Share went 37.0% (2015)
  to **45.9%** (2025) while Gulf carriers fell 32.7% to 26.2%.
- DGCA and Eurostat agree to **2.6%** across seven countries measured from opposite ends
- DGCA and IndiGo's own block hours agree to **0.31%** (1,614,608 vs 1,619,570, FY2026)
- 2030 sizing band **91M to 108M** across three methods (capacity is the low leg at 90.7M)
- Scenarios **102 / 108 / 134M**
- **Profit pool:** the Gulf is **52% of passengers but 31% of revenue**, a 20.9 point gap
- **Cost bridge:** currency added **+0.41** to FY2026 CASK against a net rise of **+0.34**,
  because fuel fell 0.18 and real non-fuel inflation was only 0.11
- **Bilateral:** India-Dubai runs ~119,200 one-way seats/week against a reported two-sided
  entitlement of 133,008, roughly **90% utilised**

**Assumptions: 24 of 28 cleared.** The four open rows are all **terminal, not pending work**:

| Row | Status | Why it will not close |
|---|---|---|
| `air_india_yield_inr_per_rpk` | `NOT_AVAILABLE` | Unlisted, files nothing |
| `aircraft_utilisation_hours_per_day_active` | `NOT_AVAILABLE` | Grounded count absent from AR FY26 and the June 2026 analyst deck |
| `india_dubai_weekly_seat_entitlement_one_side` | `UNVERIFIED_NO_PRIMARY` | India publishes no entitlement table. Corroborated from the traffic end instead |
| `gulf_hub_connect_premium_pct` | `MODELED` | Nobody publishes it |

**Not in git:** nothing. `.env` still does not exist (only needed for the optional
data.gov.in ATF history).

---

## Active task

None in flight. The session ended at a clean milestone: everything committed, rebased onto
CI's refresh, pushed, working tree clean, 77 tests green.

---

## Next steps, in order

Nothing is blocking. These are all optional improvements.

1. **Re-verify the live site after Pages rebuilds.** The local render path was verified for all
   13 charts, but the deployed site has not been loaded since the last push.
2. **Bilateral entitlements for the non-Dubai Gulf points.** Dubai is now quantified at ~90%
   utilisation. Abu Dhabi (5.7M pax) and Sharjah (3.4M) hold separate MoUs whose entitlements
   were not found. Same method would work if a figure surfaces.
3. **BTS T-100 loader** for a both-ends India to United States reconciliation, as India to
   Europe already has via Eurostat.
4. **Belly cargo.** Freight already flows through the pipeline unused. Second-order for this
   decision but real money on wide-bodies.
5. **Optional:** wire the data.gov.in ATF historical series when their API recovers. Key is in
   an older chat log; resource IDs `20c8db40-d4b8-4c69-b7e5-a6fa3fd24d05` and
   `e3b19e4d-e287-4d32-b53d-70e9617c7770`. Create `.env` with `DATAGOV_API_KEY=...`
   (gitignored). IOCL publishes its own monthly history, needs no key, and is primary.
6. **Delete or rewrite `PROJECT_STATE.md`.** It has drifted badly and duplicates this file.

---

## Gotchas

Every one of these cost real time or produced a wrong published number.

### DGCA source data
1. **Distance columns are in THOUSANDS; passenger counts are raw. The files say so nowhere.**
   Caught because average stage length came out at 5 km. Converted once in `_build_dom_carrier`.
   Two tests guard it.
2. **Two-digit years** (`15` means 2015) in the international files, four-digit in domestic.
   `_norm_year` normalises both and is idempotent.
3. **Pseudo-airline rows contain "TOTAL" anywhere, not just as a prefix.** `GRAND TOTAL` sat in
   the 2019 international carrier file worth 17.53M pax being counted as a foreign airline. A
   cross-table reconciliation test now catches this class.
4. **Carrier names have variants and typos.** `JET AIRWAYS` and `GO AIR` are Indian.
   `AIR ARABIA-ABU DHABI` uses a hyphen where the list had a space. **`QATAR AIRWATYS` is a
   misspelling in DGCA's own source.**
5. **CITY names have the same problem, and it bit a second time.** `GULF_POINTS` listed
   `ABU DHABI` and `RAS AL KHAIMAH`; DGCA writes `ABUDHABI` and `RAS AL-KHAIMAH`. Exact
   matching missed both, filing **5.0M passengers a year, 20% of the Gulf hub flow**, under
   "Everywhere else, direct" in the Sankey. **All 72 tests passed the whole time, because a
   wrong bucket is still a valid bucket.** Always match through `is_gulf_point()`, never
   `in GULF_POINTS`. DGCA also spells two points `NOTTIMGHAM` and `TAIPAE`.
6. **Eight foreign points carry freight and zero passengers** (Cologne, Leipzig, Liege,
   Luxembourg, Guangzhou, Shenzhen among them). Any per-passenger derivation must filter
   `pax > 0` or it divides by zero and emits meaningless rows.
7. **`aircraft_number` counts departures, not fleet size.**
8. **Two corrected anomalies, both in `CITY_ANOMALIES` / `COUNTRY_ANOMALIES`.** 2019 Q3 UK is
   published at 1,162,094 against a 2015-18 Q3 median of 654,870, corrupting *both* tables.
   Removing it reconciles DGCA to Eurostat and moves the pre-covid CAGR to 6.964%.
9. **`DISPUTED_ROUTES` holds Rome to Delhi**, where Eurostat reports 171,942 pax and DGCA lists
   nothing. Both numbers are reported and the route is excluded from anything depending on one
   agency being right.

### Pipeline mechanics
10. **`force=True` bypasses the parquet but does NOT write it. Only `build_all()` writes.**
    If you change a transformation, run `python -m src.data_pipeline` or the committed parquet
    goes stale and tests pass against old data.
11. **`if __name__ == "__main__"` must stay at the very end of `data_pipeline.py`.**
12. **World Bank API returns intermittent 400.** `_fetch` retries four times with backoff.
13. **Parquet is not byte-reproducible across pyarrow versions**, so CI and local rewrite each
    other's files. Harmless churn, but it causes the push rejection below.

### Git and CI
14. **CI commits its own refresh and pushes**, so your push will be rejected as
    non-fast-forward. `git fetch && git rebase origin/main`. This happened again this session;
    CI's commit touched only parquet bytes and the rebase was clean.
15. **During a rebase, `--ours` means UPSTREAM and `--theirs` means your replayed commits.**
    Inverted from merge. **Always verify actual values after a rebase**, not just that tests
    pass.
16. **No `Co-Authored-By` trailer on commits.** See Hard rules.

### Analysis
17. **A margin claim was published and retracted.** An asserted operating-margin halving of
    22.3% to 14.0% was wrong: ₹18,050 cr is an aggregator convention IndiGo does not publish.
    Real EBITDAR margin **improved**, 26.3% to 27.3% ex-forex. The retraction is in
    `docs/methodology.md` and must stay there.
18. **The symmetric version of that error is just as easy.** IndiGo **reported** an FY2026
    EBITDAR margin of **17.8%**; 27.3% is ex-forex. The profit pool anchors on ex-forex, which
    is correct because forex on USD lease liabilities is not an operating item, **but both
    numbers must appear**. Quoting only 27.3% is the retracted mistake with the sign flipped.
19. **Use CASK ex-fuel ex-forex ₹3.00, not ₹3.52, when an FX lever is running**, or the forex
    effect is double counted. **Two different quantities both equal 3.00**: FY2025 CASK ex-fuel
    and FY2026 CASK ex-fuel ex-forex. Confusing them collapses the bridge.
20. **A "reported ~13 hours/day" utilisation figure did not survive arithmetic.** It requires
    100 of 441 aircraft grounded. Reported groundings were in the 40s, giving 11.07. The real
    range is about 10.5 to 11.7. The capacity leg uses the owned-fleet 10.06 and says so.
21. **Never quote 66,504 seats/week as the India-UAE cap.** It is one emirate and one side.
    India-UAE runs roughly 255,000 one-way seats/week across Dubai, Abu Dhabi and Sharjah,
    which hold separate MoUs. Wrong by about a factor of four.
22. **Only 5.6% of India's international traffic is cross-checked** against a second agency.
    The Gulf, which carries half the traffic, has **no equivalent open source**.
23. **`UNVERIFIED_NO_PRIMARY` is the status that matters.** It marks a plausible value that can
    *never* be checked. `assumption(key, allow_unverified=True)` exists and is used in exactly
    one place, `dubai_entitlement_check()`, whose whole purpose is to test such a figure.

### Tooling and environment
24. **`pdftotext` (mingw64) and `pypdf` are already installed.** Two sessions were spent
    believing PDFs were unreadable. `pdftoppm` is absent, so the Read tool cannot rasterise
    PDF pages, but `pdftotext -layout` extracts text fine. This cracked the Airbus and Boeing
    airport planning manuals and IndiGo's annual report.
25. **Boeing and Airbus airport planning manuals are the citable seat source.** Product pages
    are not. Two-class layouts: A350-900 **315**, A350-1000 **369**, 787-9 **290**, 777-9
    **426**. Boeing also gives 787-9 at 406 all-economy, 40% higher. Never mix bases.
26. **PDF-heavy company reports mangle table column alignment** under `pdftotext -layout`.
    IndiGo's operational highlights table puts values one row below their label. Verify any
    extracted table against a known value before trusting it (revenue 849,619 was the anchor).
27. **Firecrawl (`firecrawl_search`) reads pages that plain fetching cannot**, and found the
    NSE-filed analyst deck and the ORF bilateral report. It is search, not a scraper: it will
    not parse a PDF. `civilaviation.gov.in` returns 403 to WebFetch.
28. **`python -m http.server` never exits.** Two orphaned servers held port 8000 for 25 hours.
    Use `preview_start` with `.claude/launch.json` (name `site`) and `preview_stop` instead.
29. **The Browser pane does not composite frames when hidden**, so screenshots time out and
    IntersectionObserver never fires. The scroll trigger cannot be verified in automation. The
    render path can be, by calling `Plotly.react` for each chart directly.
30. **GateGuard** (`pre:edit-write:gateguard-fact-force`, ECC plugin) demands a four-point
    justification before every new file. `.claude/settings.local.json` sets `ECC_GATEGUARD=off`.
31. **`go.Waterfall` colours `totals` red.** Use `measure="absolute"` for the opening bar and
    `"total"` only for the closing one, or the chart spends the red twice.

---

## Commands

```bash
pip install -r requirements.txt
python -m pytest -q                              # offline, a few seconds
python scripts/refresh.py                        # pull + rebuild everything
python scripts/refresh.py --no-fetch             # rebuild figures from cached parquet
python -m src.data_pipeline                      # refresh parquet ONLY (needed after transform changes)
python -m src.profit_pools                       # print the pool, the Gulf gap and the sensitivity
python -m src.scenario                           # print demand paths, unit economics and the CASK bridge
python -m src.gap_analyzer --write               # regenerate docs/coverage.md
```

Serve the site through `preview_start` (config name `site`), not a bare `http.server`.

---

## Working agreements

- Commit at the end of every phase with a descriptive message.
- **Ask before any push.** The repo is public.
- Timeboxed loaders fail soft. One attempt, then drop it and say so in `docs/methodology.md`.
- Framework prose comes from `DogInfantry/claude-skill-management-consultant-B1` (146 modules).
  Cite it, do not rewrite it.
- **When a gate opens, invert the test that guarded it rather than deleting it.** Three tests
  asserted the capacity leg was blocked and the band provisional; a silent regression to
  blocked would drop a whole leg out of the band without failing anything.
