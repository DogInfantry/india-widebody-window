# CLAUDE.md

## Project

**India's Wide-Body Window.** A recruiter-facing portfolio project mimicking Bain Capability
Network (BCN) Advanced Manufacturing & Services commercial aviation casework, targeting the
Associate AMS CoE role in Gurugram.

Case question: **"India's Wide-Body Window: where should Indian carriers deploy their next 100
long-haul aircraft, and can the India-Gulf corridor absorb them?"**

**The answer, changed 2026-08-18:** *Compete with the Gulf hubs. Do not fly more aircraft to
them.* Europe first, North America second, Gulf capacity roughly flat. It was "reclaim the
Gulf corridor first" until three lines of evidence said the aircraft cannot be deployed there.

- **Live site:** https://india-widebody-window.vercel.app (canonical)
- **Mirror:** https://doginfantry.github.io/india-widebody-window/ (still built, still works)
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
       -> docs/index.html  +  docs/report.html
```

**Loaders read the committed parquet by default.** They only hit the network when
`force=True`. This is deliberate: it makes the test suite deterministic and offline, because
CI has no `data/raw/` cache and a flaky upstream should not turn the build red.

### Key decisions and why
- **Static site, not Streamlit/Panel/Superset/Redash/Vizro-as-framework.** All need a running
  process; GitHub Pages serves static files. Vizro adopted as a *code reference* only.
- **The Next.js decision, as it actually stands (revised 2026-08-18, pivot 7).** No rebuild of
  the ANALYSIS layer: `src/` is untouched and is still the only place a number is computed.
  **A real Next.js delivery layer in `web/`, which is now canonical.** The original refusal
  conflated the two questions, which is the same conflation that delayed Vercel hosting.
  `web/` is a **static export**, so Vercel builds it from the repo root with no Root Directory
  setting and the output stays a static artifact. Historic note follows.
- **No Next.js REBUILD, but Vercel hosting is wanted.** Two separate questions and they were
  conflated for most of 2026-08-18. The rebuild is rejected: weeks of work, zero new analysis,
  rewrites 19 charts, breaks the seven-package and no-build-step decisions. **Hosting the same
  static files on Vercel is agreed and wanted**, on a `.vercel.app` URL, no custom domain. The
  assistant repeatedly framed a domain as the only reason to bother, which was wrong and
  annoying: preview deploys and a cleaner URL are reason enough. **Deployed 2026-08-18** and
  canonical. The account step turned out not to need the user at all: the Vercel CLI was
  already installed and `vercel whoami` already authenticated, so `vercel link` plus
  `vercel deploy --prod` did the whole thing. The repo is git-connected, so `main` deploys
  itself and branches get previews.
- **No DuckDB.** Whole corpus is ~90k rows, ~15 MB. pandas holds it in memory.
- **OpenSky dropped.** DGCA city-pair passenger counts beat frequency inferred from ADS-B.
- **`docs/` is the only copy of the site.** Never mirror it.
- **Market sizing reports a BAND, never an average.** The spread is the useful output.
- **Demand levers and unit-economics levers are kept apart.** Fuel and FX change what a
  passenger is worth, not how many there are.
- **Capacity is measured in ASK, not seats or aircraft.** A seat is not capacity until you say
  how far and how often it flies, and this case turns on how far. ASK is also the CASK/RASK
  denominator, so capacity and unit economics share a unit.
- **No NPV.** A DCF per option needs a discount rate, capital cost, residual value and corridor
  yield. None is verifiable here. `options.py` asks the same question from published unit costs
  instead, and reports yield *headroom* so the unknown sits on the reader's side of the line.

### Palette and type
`#CC0000` primary red, `#EE3224` accent, `#1A1A1A` ink, `#E6E6E6`/`#999999` neutrals.
**One red element per chart** (a test enforces it), everything else grey, minimal gridlines.

**IBM Plex Serif for display, IBM Plex Sans for body and all chart labels.** Serif is confined
to h1/h2/h3, the case question, the governing thought, and chart titles; anything at 13px or
below stays sans. `src/charts.py` holds `FONT` and `FONT_DISPLAY`. Changing type means changing
`style.css` and `charts.py` together, then re-running `scripts/refresh.py`, because the font is
baked into every exported chart JSON.

### Dependency discipline
`requirements.txt` is **still deliberately seven packages** and the analysis layer takes no
new ones. Already rejected with reasons: duckdb, pyopensky, pdfplumber, vizro, dash,
streamlit, panel.

**`web/` has its own npm dependencies and that is not a reversal of the above.** The Python
side is untouched; the delivery layer is Next.js, React, Tailwind v4, Recharts. Tremor was
considered and rejected: about 200KB against shadcn-style primitives at 50KB, and its opinions
fight a palette and type system that tests already enforce. Puppeteer was rejected again: the
PDFs render through local Chrome against the same print CSS, which needs no Node toolchain and
no cold-starting function.
Third party attribution in `NOTICE`; `charts.py::mekko()` is adapted from Vizro (Apache-2.0).

---

## File map

| Path | Role |
|---|---|
| `src/data_pipeline.py` | Fetch, clean, cache. All three DGCA traps handled here, once. ~935 lines |
| `src/charts.py` | Bain palette builders. House rules as code, enforced by tests |
| `src/benchmarking.py` | Carriers and corridors. Stage length is the differentiating metric. Also holds `is_gulf_point()` and `dubai_entitlement_check()` |
| `src/market_sizing.py` | Three methods to a band. `_ORDER_BOOK` holds the wide-body variant mix |
| `src/fleet_gap.py` | **NEW.** Order book in ASK vs what the market asks for. Block speed and seats/departure computed from DGCA. Absorption frontier + gap path |
| `src/options.py` | **NEW.** Corridor breakeven, yield headroom, value at stake, option menu. Holds `CASK_STAGE_ELASTICITY`, the one knob |
| `src/profit_pools.py` | Corridor profit pool. Heavily modelled; every seam labelled. Holds `MARGIN_STAGE_SENSITIVITY` |
| `src/scenario.py` | Demand paths, plus fuel and FX on unit economics |
| `src/cargo.py` | **NEW.** Belly freight by corridor. Physical units only, no revenue leg. Holds the non-correlation caveat |
| `src/gap_analyzer.py` | Maps `jd.txt` to artifacts, checks each exists. Reports 82% |
| `scripts/refresh.py` | **Single entry point, and exactly what CI runs** |
| `docs/index.html` | The site. 17 scrolly steps, recommendation section, pivots section, reconciliation, methodology |
| `docs/deck.html` | **NEW.** Slide view. Same no-prose pattern: reads `index.html`, one step per screen, arrow keys plus scroll-snap |
| `scripts/make_pdfs.py` | **NEW.** Chrome headless to committed PDFs. Needs the site served on :8000. Not in `refresh.py`, not in CI |
| `docs/brief.html` | **NEW.** Two one-pagers: one for a case team, one for a screener |
| `scripts/make_social_card.py` | **NEW.** Generates `social-card.png` and `favicon.svg`. Run once, commit. NOT in `refresh.py`, CI never runs it, needs matplotlib which is deliberately absent from requirements.txt |
| `docs/report.html` | **NEW.** Print edition. Holds no prose: fetches `index.html` at load and relays it linearly. Save as PDF button |
| `docs/assets/{style.css,scrolly.js}` | Sticky-graphic scrollytelling, mobile stacks, `@media print` block |
| `docs/recommendation.md` | **NEW.** Option menu, roadmap, WWHTBT, 9-row risk register, leading indicators |
| `docs/survey_design.md` | **NEW.** Conjoint instrument, sampling frame and analysis plan for `gulf_od_share_pct`. Designed, NOT fielded. Coverage deliberately still reports survey analysis as a gap |
| `docs/pivot_log.md` | Seven documented changes of mind, each citing its commit |
| `web/` | **NEW.** The client-facing delivery layer. Next.js **static export**, five routes, Recharts. Canonical on Vercel |
| `src/app_export.py` | **NEW.** Tidy JSON, exhibit data, the scenario cube and the evidence ledger for `web/`. Calls the SAME functions the charts do |
| `tests/test_app_export.py` | **NEW.** Strict-JSON, determinism and stale-export drift guards |
| `docs/{storyline,hypothesis_tree,methodology,coverage,alternative_b_datacenters}.md` | Written IP |
| `data/data_dictionary.md` | Provenance contract. Every field, source, pull date, grade |
| `data/manual/assumptions.csv` | Hand-entered numbers, 11-state status vocabulary. 31 rows |
| `tests/test_pipeline.py` | Loaders, units, anomalies, provenance, data-dictionary drift guards |
| `tests/test_narrative.py` | **NEW.** The prose must agree with the code. `must_not_appear` is the half that catches drift |
| `tests/test_analysis.py` | Findings, chart house rules, sizing, scenarios, pools, bilaterals, fleet gap, options |
| `vercel.json` | Static Vercel config: `docs/`, `framework: null`, no build step. **`framework: null` is load-bearing**: `requirements.txt` at root makes Vercel detect a Python app and fail with "No Flask entrypoint found" |
| `.vercelignore` | **NEW.** Nothing outside `docs/` is served, so nothing else is uploaded |
| `docs/external_review_response.md` | **NEW.** The Fable review mapped item by item: taken, taken differently, or refused with the reason |
| `.claude/launch.json` | `preview_start` config (name `site`) for serving `docs/` without orphaning a server |
| `.github/workflows/refresh.yml` | Monthly cron. Tests, refresh, tests again, commit |

`PROJECT_STATE.md` was **deleted 2026-08-18**. It described the 2026-08-15 state and duplicated
this file. Do not recreate it.

---

## Current state

**Done and green. 164 tests pass. 19 Plotly charts on the mirror, plus the React delivery
layer. Working tree clean.**

**Closed 2026-08-18, third block (`434f186`, pushed):** the Vercel deploy and the brief PDF
page break, the two items that had been open. Plus `docs/external_review_response.md`, which
answers the external review item by item. Nothing from the previous handoff is still open.

**Data vintage: 2025.** `INTL_COUNTRY_YEAR` and `market_sizing.BASE_YEAR` both moved from
2024 on 2026-08-18. The Eurostat reconciliation stays on 2024, the last year both agencies
publish complete, and is labelled as such on the page. See `docs/methodology.md`.

**Live on two hosts.** Vercel is canonical and redeploys on every push to `main`; GitHub Pages is the mirror. CI green on freshly pulled data.

**The findings, all computed from DGCA unless noted:**
- India international sector pax 2025: **78.0M**, Gulf six **50.9%**, 39.7M passengers
- The Gulf corridor is **4.1x** India's entire direct Europe market (39.7M vs 9.6M)
- IndiGo carried 16.7M international pax in 2025 to Air India's 10.7M, at **2,643 km**
  average stage length against **5,316 km**
- **Premise reversed:** Indian carriers went 37.0% (2015) to **45.9%** (2025); Gulf 32.7% to 26.2%
- DGCA and Eurostat agree to **2.6%** across seven countries measured from opposite ends
- DGCA and IndiGo's own block hours agree to **0.31%** (1,614,608 vs 1,619,570, FY2026)
- 2030 sizing band **96M to 109M** across three methods (capacity is the low leg at 96.5M)
- Scenarios **104 / 109 / 131M**
- **Profit pool:** the Gulf is **52% of passengers but 31% of revenue**
- **Cost bridge:** currency added **+0.41** to FY2026 CASK against a net rise of **+0.34**
- **Bilateral:** India-Dubai ~118,159 one-way seats/week vs entitlement 133,008, **88.8% utilised**; Abu Dhabi **70.1%**, so the Gulf is NOT uniformly capped

**New this session (2026-08-18):**
- **Baseline capacity:** Indian carriers 2025, 36.4M pax, **153.8bn ASK**, 3,426 km blended
  sector, LF 81.1%. Wide-body block speed proxy **698 km/h** (Air India intl, computed)
- **Order book:** 46,546 seats to **119.3bn ASK**, **+78%** on today's international capacity.
  **1.94x** the growth needed to hold share
- **Absorption:** clears only at sector **+26.8%** (4,345 km) or share **58.2%**.
  Bear +35% / 62%, Base +27% / 58%, **Bull +2% / 47%**
- **Yield headroom by corridor:** Gulf **-4.3%**, South Asia -1.9%, East Asia +8.9,
  SE Asia +11.2, Africa +16.9, Europe **+21.3**, Oceania +29.5, North America **+31.5**
- **Value at stake:** 8.49M connecting pax, **INR 28,916 to 56,712 cr** (a third to two thirds
  of IndiGo's revenue). Banded between IndiGo's 5.06 and Emirates' 9.924 INR/RPK
- **Options reference:** IndiGo system sector 1,172 km, CASK 5.00, yield 5.06,
  `CASK_STAGE_ELASTICITY = -0.25`

**Assumptions: 25 of 31 cleared.** The six open rows are **terminal, not pending work**
(this said 30 and five until 2026-08-18: an Abu Dhabi entitlement row was added and never
reached the handoff, which the methodology route caught by counting the file):

| Row | Status | Why it will not close |
|---|---|---|
| `air_india_yield_inr_per_rpk` | `NOT_AVAILABLE` | Unlisted, files nothing |
| `aircraft_utilisation_hours_per_day_active` | `NOT_AVAILABLE` | Grounded count absent from AR FY26 and the June 2026 analyst deck |
| `india_dubai_weekly_seat_entitlement_one_side` | `UNVERIFIED_NO_PRIMARY` | India publishes no entitlement table. Corroborated from the traffic end |
| `gulf_od_share_pct` | `UNVERIFIED_NO_PRIMARY` | IATA sells O-D data. **Carries the 11-point connect gap, so it is the likeliest reason the case is wrong** |
| `gulf_hub_connect_premium_pct` | `MODELED` | Nobody publishes it |

---

## Active task

**Building the client-facing delivery layer in `web/`.** P0 to P4b are committed and live.
164 tests green, tree clean at commit time, no running servers.

| Phase | State |
|---|---|
| P0 scaffold and prove deployment | Done, `85d3b89` |
| P1 export layer and drift guards | Done, `fe79456` |
| P2 `/` and `/dashboard` | Done, `705356d` and `d0ffa09` |
| P3 `/frameworks`, the five-link chain | Done, `77737a9` |
| P4a `/deck`, fifteen slides | Done |
| P4b `/methodology`, the evidence ledger | Done |
| P4c `/story`, scrollytelling | **NOT BUILT.** See next steps |
| P5 polish and record | This entry, the pivot log and the CLAUDE.md sweep |

**Nothing is pushed.** Every deploy so far has been `vercel deploy --prod` from the CLI. The
first push will also fire the git-connected build, which has never run against `web/`.

---

## Next steps, in order

1. **`/story`, or a decision not to build it.** The approved plan had a scrollytelling route.
   It was not built, deliberately and provisionally: `/deck` already walks the argument one
   exhibit at a time, and a fifth route re-telling it in a different scroll idiom risks being
   duplication rather than delivery. **This is the user's call, not the assistant's**, and it
   is recorded here rather than quietly dropped.
2. **The forwarding note.** Still unwritten and it is now the binding constraint. The user
   applied to the BCN AMS Associate role and has had no reply, and has a warm contact who
   could refer them. The artifact is finished; what is missing is a short note in the **user's
   own voice** to send that contact, with the `.vercel.app` link and the brief PDF attached.
   `docs/brief.html` and the PDFs exist precisely to make that forward cheap. Agreed in an
   earlier session and never delivered.
3. **Wide-body lease rates.** Now the largest named unresolved input: the damp-lease bridge
   option in `docs/recommendation.md` is presented with its economics explicitly unquantified.
   IBA/Cirium transaction rates are paywalled. If a citable rate ever surfaces, the bridge
   option becomes comparable and the roadmap's Phase 1 gets a real answer.
4. **Bilateral entitlements for the non-Dubai Gulf points.** Abu Dhabi (5.7M pax) and Sharjah
   (3.4M) hold separate MoUs whose entitlements were not found. Dubai's 88.8% utilisation is
   now load-bearing for the recommendation, so a second point would strengthen or break it.
5. **BTS T-100 loader** for a both-ends India to United States reconciliation, as India to
   Europe already has via Eurostat. Would raise the 5.6% cross-checked share.
6. **Belly cargo.** Freight already flows through the pipeline unused. Real money on wide-bodies.
7. **Optional:** wire the data.gov.in ATF historical series when their API recovers. Resource IDs
   `20c8db40-d4b8-4c69-b7e5-a6fa3fd24d05` and `e3b19e4d-e287-4d32-b53d-70e9617c7770`. Create
   `.env` with `DATAGOV_API_KEY=...` (gitignored). IOCL publishes its own history, no key, primary.

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
   the 2019 international carrier file worth 17.53M pax being counted as a foreign airline.
4. **Carrier names have variants and typos.** `JET AIRWAYS` and `GO AIR` are Indian.
   `AIR ARABIA-ABU DHABI` uses a hyphen where the list had a space. **`QATAR AIRWATYS` is a
   misspelling in DGCA's own source.**
5. **CITY names have the same problem, and it bit a second time.** `GULF_POINTS` listed
   `ABU DHABI` and `RAS AL KHAIMAH`; DGCA writes `ABUDHABI` and `RAS AL-KHAIMAH`. Exact
   matching missed both, filing **5.0M passengers a year, 20% of the Gulf hub flow**, under
   "Everywhere else, direct". **All 72 tests passed the whole time, because a wrong bucket is
   still a valid bucket.** Always match through `is_gulf_point()`, never `in GULF_POINTS`.
6. **Eight foreign points carry freight and zero passengers.** Any per-passenger derivation must
   filter `pax > 0` or it divides by zero.
7. **`aircraft_number` counts departures, not fleet size.**
8. **Two corrected anomalies, in `CITY_ANOMALIES` / `COUNTRY_ANOMALIES`.** 2019 Q3 UK is
   published at 1,162,094 against a 2015-18 Q3 median of 654,870, corrupting *both* tables.
9. **`DISPUTED_ROUTES` holds Rome to Delhi**, where Eurostat reports 171,942 pax and DGCA lists
   nothing. Excluded from anything depending on one agency being right.

### Pipeline mechanics
10. **`force=True` bypasses the parquet but does NOT write it. Only `build_all()` writes.**
    If you change a transformation, run `python -m src.data_pipeline` or the committed parquet
    goes stale and tests pass against old data.
11. **Editing a figure in Python does NOT update `docs/assets/charts/*.json`.** The site reads
    the exported JSON. Changing a chart title and only running pytest leaves the old title on
    the page. Re-run `python scripts/refresh.py --no-fetch`. This bit once this session.
12. **`if __name__ == "__main__"` must stay at the very end of `data_pipeline.py`.**
13. **World Bank API returns intermittent 400.** `_fetch` retries four times with backoff.
14. **Parquet is not byte-reproducible across pyarrow versions**, so CI and local rewrite each
    other's files. Harmless churn, but it causes the push rejection below.

### Git and CI
15. **CI commits its own refresh and pushes**, so your push will be rejected as
    non-fast-forward. `git fetch && git rebase origin/main`.
16. **During a rebase, `--ours` means UPSTREAM and `--theirs` means your replayed commits.**
    Inverted from merge. **Always verify actual values after a rebase**, not just that tests pass.
17. **No `Co-Authored-By` trailer on commits.** See Hard rules.

### Analysis
18. **A margin claim was published and retracted.** An asserted operating-margin halving of
    22.3% to 14.0% was wrong: ₹18,050 cr is an aggregator convention IndiGo does not publish.
    Real EBITDAR margin **improved**, 26.3% to 27.3% ex-forex. The retraction is in
    `docs/methodology.md` and must stay there.
19. **The symmetric version of that error is just as easy.** IndiGo **reported** an FY2026
    EBITDAR margin of **17.8%**; 27.3% is ex-forex. **Both numbers must appear.**
20. **Use CASK ex-fuel ex-forex ₹3.00, not ₹3.52, when an FX lever is running**, or the forex
    effect is double counted. **Two different quantities both equal 3.00**: FY2025 CASK ex-fuel
    and FY2026 CASK ex-fuel ex-forex.
21. **A "reported ~13 hours/day" utilisation figure did not survive arithmetic.** It requires
    100 of 441 aircraft grounded. Real range about 10.5 to 11.7. The capacity leg uses the
    owned-fleet 10.06 and says so.
22. **Never quote 66,504 seats/week as the India-UAE cap.** It is one emirate and one side.
    India-UAE runs roughly 255,000 one-way seats/week across three separate MoUs. An external
    review repeated this error in 2026-08-18; it was caught because this list exists.
23. **Only 5.6% of India's international traffic is cross-checked** against a second agency.
    The Gulf, which carries half the traffic, has **no equivalent open source**.
24. **`UNVERIFIED_NO_PRIMARY` is the status that matters.** It marks a plausible value that can
    *never* be checked. `assumption(key, allow_unverified=True)` is used in exactly **two**
    places: `dubai_entitlement_check()` and `options.connect_gap()`.
25. **`fleet_gap` and hypothesis branch 4.2 look contradictory and are not.** 4.2 divides the
    order book by the WHOLE market's growth; `fleet_gap` divides it by Indian carriers' share of
    that growth. Both true. A test pins the reconciliation. Read the module docstring first.
26. **A modelled knob belongs as a module constant, not an assumptions row.** `MODELED` is not
    in `USABLE_STATUSES`, so `assumption()` refuses it and the module cannot run. Follow
    `MARGIN_STAGE_SENSITIVITY` / `CASK_STAGE_ELASTICITY`, each beside a `sensitivity()`.
27. **Do not compare corridor breakeven against a flat yield.** Yield per RPK falls with stage
    length, so holding it constant flatters long-haul. `options.py` reports *headroom* instead.

### Tooling and environment
28. **`pdftotext` (mingw64) and `pypdf` are already installed.** `pdftoppm` is absent, so the
    Read tool cannot rasterise PDF pages, but `pdftotext -layout` extracts text fine.
29. **Boeing and Airbus airport planning manuals are the citable seat source. Product pages are
    not.** Two-class: A350-900 **315**, A350-1000 **369**, 787-9 **290**, 777-9 **426**. A
    product page IS acceptable for a *range* spec (`a321xlr_range_km`), because range carries no
    configuration ambiguity. The A320-family ACAP 404ed; no XLR seat row exists as a result.
30. **PDF-heavy company reports mangle table column alignment** under `pdftotext -layout`.
    Verify any extracted table against a known value (revenue 849,619 was the anchor).
31. **Firecrawl (`firecrawl_search`) reads pages that plain fetching cannot.** It is search, not
    a scraper: it will not parse a PDF. `civilaviation.gov.in` returns 403 to WebFetch.
32. **`python -m http.server` never exits.** Two orphaned servers held port 8000 for 25 hours.
    Use `preview_start` with `.claude/launch.json` (name `site`) and `preview_stop`.
33. **The Browser pane does not composite frames when hidden**, so screenshots time out and
    IntersectionObserver never fires. Verify the render path by calling `Plotly.react` per chart.
34. **The Browser pane caches `style.css` hard, and `location.reload(true)` does not bust it.**
    A CSS change will silently appear not to apply. Verify by removing the `<link>` and
    injecting a cache-busted one, then read `getComputedStyle`. Cost 20 minutes this session.
35. **Plotly `updatemenus` buttons fire on `click`, not `mousedown`/`mouseup`.** Synthetic
    mousedown+mouseup does nothing. Also, exported trace arrays can be **binary-encoded**, so
    `host.data[0].y` is an object with no `.length`; assert against `_fullLayout.<axis>.range`
    or the SVG path instead.
36. **`go.Waterfall` colours `totals` red.** Use `measure="absolute"` for the opening bar and
    `"total"` only for the closing one, or the chart spends the red twice.
37. **GateGuard** (`pre:edit-write:gateguard-fact-force`, ECC plugin) demands a four-point
    justification before every new file. `.claude/settings.local.json` sets `ECC_GATEGUARD=off`.

### The site
38. **GitHub Pages serves `docs/*.md` as RAW markdown.** There is no `_config.yml` and no
    `.nojekyll`, so a link from `index.html` to a `.md` file lands the reader on plain text.
    Link written IP to **GitHub blob URLs** instead, which is what the footer does.
39. **New chart modules inherit ZERO house-rule coverage** unless added to
    `PUBLISHING_MODULES` in `tests/test_analysis.py`. `market_sizing` and `scenario` were
    exempt from the one-red and takeaway-title rules for the life of the project and nothing
    ever failed. A test now walks `src/` and fails if a publishing module is left out.
41. **Build the chart data table from Plotly's `_fullData`, never the exported JSON.**
    Exported trace arrays are frequently binary encoded, so `fig.data[0].y` from the file is
    an object with no `.length`, while `_fullData` holds a decoded typed array.
42. **`.sticky-graphic` is a flex COLUMN.** It was a row carrying one child, so anything
    added beside the chart landed next to it rather than under it.
43. **Three surfaces, one narrative.** `index.html` holds all the prose; `report.html` and
    `deck.html` fetch it and re-lay it out. Never write step prose into the other two, and a
    test asserts the deck has no headings of its own.
44. **`scripts/make_social_card.py` needs matplotlib, which is NOT in `requirements.txt`.**
    Deliberate: the card and favicon are static assets, generated once and committed, so CI
    never needs the dependency and the seven-package discipline holds. Re-run it only if the
    hero numbers or the headline change.
46. **Vercel's Root Directory cannot be set from the CLI, and `vercel link` from a subdirectory
    does not set it either.** It writes `.vercel/repo.json` at the GIT ROOT with
    `"directory": "."` every time. The project also had `Framework Preset: Flask` stuck on it
    from the first failed deploy. **The build sidesteps all of it**: `web/` is a Next.js
    **static export**, and the root `vercel.json` runs `npm --prefix web run build` and serves
    `web/out`. No Root Directory setting, no dashboard step, and the output stays a static
    artifact like everything else here.
48. **`.vercelignore` follows gitignore semantics, so bare patterns match at ANY depth.** A
    bare `data` excluded `web/public/data` and the Vercel build failed with
    `Can't resolve '@/public/data/access.json'` while the local build passed. Every pattern in
    that file is anchored with a leading slash now, with the reason written in it.
49. **`json.dumps` writes bare `NaN`, which is not JSON.** pandas produces NaN freely: the
    "Other" corridor has no hub, so no stage length and no yield headroom. The browser's
    `JSON.parse` rejects it and the page renders nothing while every Python test passes.
    `src/app_export.py` maps NaN to null and passes `allow_nan=False` so a leak is a build
    failure.
50. **`benchmarking.carrier_operating_summary()` returns DOMESTIC unless told otherwise.** The
    capability exhibit plotted a 943 km domestic stage length while claiming to compare
    international networks, where the real figures are 2,643 km against 5,316 km. The export
    names both tables rather than defaulting to one. **Read the signature before trusting a
    default.**
51. **Recharts 3 widened the Tooltip `formatter` signature.** A parameter typed `number` is
    contravariant with `ValueType` and fails type checking. Take the value untyped and coerce
    inside.
52. **A chart title that a CONTROL can falsify is worse than a topic title.** The dashboard's
    shock panel asserted "currency costs more spread than fuel", which is false at zero shock
    where both are zero. Action titles on interactive exhibits must be computed from the
    current control position.
47. **Tailwind v4 `@theme` declares `--font-sans` on `:root`, so the next/font class must go on
    `<html>`, not `<body>`.** A `var()` inside a custom property is resolved at the element
    that DECLARES it. With the font variables on `<body>`, `:root` could not see
    `--font-plex-sans`, the declaration was invalid, and every heading fell back to
    `-apple-system` while the page still looked deliberate. Verify with
    `getComputedStyle(h1).fontFamily`, never by eye.
45. **A page-level class collided with a component class and voided every page break.**
    `docs/brief.html` shipped as `<body class="brief">`, and `.brief` was already the
    decision-list grid from `index.html`. The brief's body became a GRID CONTAINER, and Chrome
    does not honour a forced break between grid items, so `page-break-after` and `break-after`
    were both present, both correct and both inert. The PDF printed both audiences in
    side-by-side columns and nothing failed: right size, every word present. It is `.brief-doc`
    now and a test pins it. **Before debugging a break property, check what `display` the
    printing context actually has.**
40. **The `.recon` table class sets `white-space: nowrap` on mobile.** Any new table reusing it
    for prose cells explodes horizontally: the option tables hit 1300px on a 335px screen. The
    `.options` class overrides it.

---

## Commands

```bash
pip install -r requirements.txt
python -m pytest -q                              # offline, ~20 seconds
python scripts/refresh.py                        # pull + rebuild everything
python scripts/refresh.py --no-fetch             # rebuild figures from cached parquet
python -m src.data_pipeline                      # refresh parquet ONLY (needed after transform changes)
python -m src.fleet_gap                          # baseline, order book, absorption frontier, gap band
python -m src.options                            # corridor economics, sensitivity, value at stake, option menu
python -m src.profit_pools                       # the pool, the Gulf gap and the sensitivity
python -m src.scenario                           # demand paths, unit economics and the CASK bridge
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
- **When a gate opens, invert the test that guarded it rather than deleting it.**
- **When a headline number moves, add its OLD value to `must_not_appear` in
  `tests/test_narrative.py`, not just the prose.** That is what turns the next drift into a
  failing build. Prose was reconciled to the modules by hand three times in one session and
  four figures still survived it, every one missed because the phrase wrapped across a line
  break. A passage that quotes a superseded figure ON PURPOSE opts out with
  `<!-- narrative-guard: ignore -->`, visibly, in the source.
- **When the answer changes, say so in `docs/pivot_log.md` rather than quietly amending.** Six
  entries so far, each citing its commit. Changing a recommendation also means sweeping
  `storyline.md`, `hypothesis_tree.md`, `index.html`, `README.md` and `methodology.md`: the
  2026-08-18 change left four of them self-contradicting for one commit.
