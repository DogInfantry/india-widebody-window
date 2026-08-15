# Project state

**Last updated:** 2026-08-15
**Current phase:** Phase 1a complete (pipeline green, 15 tests pass), Phase 1b next
**Full plan:** `C:\Users\Anklesh\.claude\plans\c-users-anklesh-downloads-compass-artif-refactored-journal.md`

This file is the single place to look when resuming. It survives context loss.
Dated snapshots live in `memory/`.

---

## Phases

| # | Phase | Status | Gate |
|---|---|---|---|
| 0 | Scaffold, git, state files | **Done** | Repo initialised, files committed |
| 1a | Core loaders + data dictionary + tests | **Done** | 15 tests pass, every verified figure reproduces |
| 1b | Eurostat, IOCL ATF, timeboxed BTS and UK CAA | Next | Both-ends reconciliation possible, or documented as single-sided |
| 2 | Analysis modules + chart builders | Not started | All figures exported to `docs/assets/charts/*.json` |
| 3 | Scrollytelling page | Not started | Renders at 1280px and 375px, console clean |
| 4 | Docs + gap analyzer | Not started | Coverage at or above 90%. **Blocked on `jd.txt`** |
| 5 | CI, acceptance, push | Not started | `scripts/refresh.py` runs clean, then ask before pushing |

---

## Verified figures (computed 2026-08-15, do not recompute blind)

Phase 1 must reproduce these. If it does not, the pipeline is wrong, not the numbers.

**India international, 2024, DGCA sector traffic**
- Total 72.2M passengers (both directions summed)
- Gulf six (UAE, Saudi, Qatar, Oman, Kuwait, Bahrain): **51.2%**
- UAE alone 21.5M = 29.8%. Next: Singapore 5.47M, Saudi 5.20M, Thailand 4.66M, Qatar 4.27M, UK 3.49M
- Indian carriers hold **45%** of the 71.9M carrier-attributed total. Foreign carriers 55%
- Carriers: IndiGo 13.32M, Air India 9.26M, Air India Express 5.89M, Emirates 5.57M,
  Etihad 2.82M, Singapore 2.37M, Qatar 2.20M, Vistara 2.17M, Air Arabia 1.82M, SpiceJet 1.61M

**India domestic, 2025, scheduled only**
- IndiGo 107.0M pax, **64.1%** share, 86.1% load factor
- Air India 26.2M, 15.7%, 82.3% | Air India Express 18.8M, 11.3%, 83.1%
- Akasa 8.5M, 5.1%, **92.5%** (highest load factor in market) | SpiceJet 4.7M, 2.8%, 86.2%

**The core finding, international 2025, Indian carriers**
- IndiGo: 16.67M pax, 44.07bn RPK, average stage length **2,643 km**, 82.0% LF
- Air India: 10.72M pax, 57.00bn RPK, average stage length **5,317 km**, 81.4% LF
- Air India Express: 6.87M pax, 18.43bn RPK, 2,683 km, 79.0% LF

IndiGo carries more international passengers than Air India while flying far fewer
passenger-kilometres. Closing that stage length gap is what the wide-body orders buy.

**The headline reconciliation**
DGCA sector traffic puts the Gulf at 51.2%. IATA true origin-destination puts it at
roughly 40%. The gap of about 11 percentage points is the connect leak. That reconciliation,
not either number alone, is the argument.

---

## Data sources

| Source | Access | Status | Role |
|---|---|---|---|
| DGCA via `Vonter/india-aviation-traffic` | raw.githubusercontent CSV | Verified, fresh to 2026-05 | Spine. All five aggregated CSVs |
| OurAirports | CC0 CSV, 12.4 MB | Verified 200 | Airport metadata, great circle distance |
| World Bank API v2 | JSON, no key | Verified 200 | Macro. `IS.AIR.PSGR` has **no data after 2023** |
| Eurostat `avia_par_*` | JSON API, no key | Verified 200 | European end of India-Europe routes |
| IOCL aviation fuel | Web page | Verified 200 | ATF price for the fuel lever |
| BTS T-100 International | Form driven download | Verified 200, **timeboxed** | US end. Drop after one failed attempt |
| UK CAA airport data | File download | Verified 200, **timeboxed** | UK end. Drop after one failed attempt |
| Wikipedia | `pd.read_html` | Verified 200 | Fleet and order cross-check only |
| IndiGo / SpiceJet filings | Manual transcription | Pending | Yields into `data/manual/assumptions.csv` |

`data/manual/assumptions.csv` schema:
`key, value, unit, source_name, source_url, pull_date, page_ref, reliability`
with `pull_date` as `YYYY-MM-DD` and `reliability` in `{H, M, L}`.

---

## Decisions log

| Date | Decision | Reason |
|---|---|---|
| 2026-08-15 | Static HTML on GitHub Pages, not Streamlit, Panel, Superset, Redash, or Vizro | All need a running process. Pages serves static files |
| 2026-08-15 | Drop OpenSky | DGCA city-pair pax beats inferred ADS-B frequency, and removes OAuth fragility |
| 2026-08-15 | Drop DuckDB (Gemini's only original suggestion) | 90k rows total. pandas holds it in memory |
| 2026-08-15 | Drop AAI PDF parsing and pdfplumber | Airport level traffic adds nothing to a route and carrier case |
| 2026-08-15 | Drop the `dashboard/` to `docs/` mirror | One site directory. Two copies drift |
| 2026-08-15 | Drop all 5 notebooks | They duplicate `src/` and rot on every module change |
| 2026-08-15 | Adapt Vizro's `marimekko.py` under Apache-2.0, attributed in NOTICE | Hardest chart, already solved. Reuse beats rewrite |
| 2026-08-15 | Waterfall uses native `go.Waterfall` | It is a built-in Plotly trace. No custom geometry needed |
| 2026-08-15 | Perspective for one lazy-loaded appendix block only | Exploration tool in a persuasion artifact. Keep it off the narrative path |
| 2026-08-15 | Add Eurostat and a `go.Sankey` connect-leak chart | Lets the same route be measured from both ends. Triangulation performed, not claimed |
| 2026-08-15 | Reuse `DogInfantry/claude-skill-management-consultant-B1` for framework prose | 146 modules already written. Cross-links two repos into a body of work |
| 2026-08-15 | Build local, push at the end | User choice. CI and Pages stay untested until Phase 5, accepted knowingly |
| 2026-08-15 | Replace the blueprint's "~40% Gulf" news quote with computed 51.2% plus reconciliation | Our number, better story, traceable to DGCA |
| 2026-08-15 | Convert DGCA distance columns from thousands to true units inside the loader | Found during Phase 1a verification, see below. Fixing in the loader means no caller can get it wrong |
| 2026-08-15 | Gap analyzer reports honestly, target dropped from "at or above 90%" | The real JD asks for survey analysis and team management, neither of which a solo repo can evidence. A gap analyzer tuned to hit 90% is one that lies |
| 2026-08-15 | Keep the no-supply-chain rule, but stop calling it a JD requirement | The real JD names logistics and transport as an AMS sub-sector twice. The rule came from elsewhere and is now labelled a preference |

---

## Phase 1a findings

### The units bug, and why it matters

DGCA publishes `Passenger Kilometers`, `Seat Kilometers` and `Aircraft Kilometres` in
**thousands**, while `Passenger Number` is a raw count. The file says so nowhere.

Caught because average stage length came out at 5 km. Confirmed three independent ways
before applying the conversion:

1. **Scale.** Thousands gives India domestic 163.8bn RPK for 2025, matching the published
   industry range of roughly 160 to 170bn. Raw implies 0.98 km per passenger.
2. **Ratio.** Computed `rpk / ask` matches DGCA's own `load_factor` column to within
   0.25pp on the majors, 0.93pp worst case.
3. **Coherence.** For one month, the aircraft-km column gives 588 km per departure and the
   RPK column gives 589 km, two independent columns agreeing to one part in 600.

Converted once in `load_dgca_domestic_carrier`. Guarded by
`test_stage_length_is_physically_plausible` and `test_computed_load_factor_matches_published`.

### What the real job description says

Extracted from the posting PDF into `jd.txt`, 5,920 characters.

- **Confirms the case choice.** "commercial aviation" is named as an AMS sub-sector, and
  the role explicitly involves "Bain case teams from ME offices". The India-Gulf angle is
  in the job, not inferred.
- **Contradicts the blueprint.** The JD lists "real estate/construction, heavy machinery,
  commercial aviation, logistics & transport" twice. Logistics and transport is part of
  the job, so the no-supply-chain rule is a personal preference, not a JD constraint.
  Kept in `CLAUDE.md`, relabelled.
- **Two requirements this repo cannot honestly evidence:** "survey analysis" (no survey
  data exists and inventing one would be fabrication) and "first-level team management
  ... conducting performance / feedback discussions" (a solo repo cannot show this; tests
  and a review checklist are a proxy at best). Both go to `ROADMAP.md` as named gaps.

---

## Blockers and open items

1. ~~`jd.txt` is empty.~~ **Resolved 2026-08-15.** Extracted from the posting PDF.
2. **`data/manual/assumptions.csv` needs your review** before the yields drive the revenue
   waterfall. I draft roughly 15 rows with sources, you sanity check them.
3. **Repo name at push time.** Default `india-widebody-window`. Repo has no remote and
   nothing has been pushed. Confirmed by `git remote -v` returning empty.
4. **CI and Pages are untested** until Phase 5, a known consequence of pushing at the end.
   Expect one or two fixup commits after the first push.
5. **GateGuard (`pre:edit-write:gateguard-fact-force`) denies every new file** until a
   four-point justification is written first. It has fired 12 times. Disable with
   `ECC_GATEGUARD=off` or by adding the hook name to `ECC_DISABLED_HOOKS`, otherwise every
   remaining phase pays the same toll.

---

## Next actions

Phase 1b:

1. `load_eurostat_avia_par()` for the European end of India-Europe routes
2. `load_atf_price()` from IOCL for the scenario fuel lever
3. `load_bts_t100()` and `load_uk_caa()`, one attempt each, fail soft and document
4. Extend `tests/test_pipeline.py`, update `data_dictionary.md` section 8, commit

Then Phase 2: `market_sizing.py`, `benchmarking.py`, `profit_pools.py`, `scenario.py`,
`charts.py` with the Vizro-derived `mekko()`, and chart JSON export to `docs/assets/charts/`.
