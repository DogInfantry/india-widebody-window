# Methodology

What was done, what it rests on, and what it cannot tell you.

---

## Frameworks

| Framework | Where it is applied |
|---|---|
| **SCQA / Minto pyramid** | `docs/storyline.md`. Governing thought first, MECE support beneath, evidence last |
| **Issue tree** | `docs/hypothesis_tree.md`. Decomposed before analysis, so work was sequenced by what would most change the answer |
| **Market sizing triangulation** | `src/market_sizing.py`. Three methods with different failure modes, reconciled to a band |
| **Competitive benchmarking** | `src/benchmarking.py`. Share, load factor, and stage length as the differentiating metric |
| **Profit pools** (Gadiesh & Gilbert, HBR 1998) | `src/charts.py::profit_pool_curve`. Built, not yet populated: blocked on yields |
| **Hypothesis invalidation** | `docs/storyline.md` closes with what would change the recommendation. A recommendation that cannot be falsified is not analysis |

Framework structure draws on
[DogInfantry/claude-skill-management-consultant-B1](https://github.com/DogInfantry/claude-skill-management-consultant-B1),
a reference library of 146 consulting modules, rather than being reinvented here.

---

## The measurement that matters most

**DGCA counts sector passengers, not origin-destination.** A passenger flying Delhi to Dubai
to London is recorded as a passenger to the United Arab Emirates. The India-to-foreign-point
leg is what gets counted; the rest of the journey is invisible.

This is why:

- DGCA sector data puts the Gulf at **51.2%** of India's international traffic
- IATA true origin-destination figures put it near **40%**

Both are correct measurements of different things. The roughly eleven point gap is
passengers connecting onward through a Gulf hub. **That gap is the case**, not a
discrepancy to be reconciled away, and it is why the flow diagram on the site stops at the
first foreign point rather than modelling a second leg the data cannot support.

Anywhere the two measures are compared, which is used is stated.

---

## Triangulation, performed rather than claimed

Every Indian figure comes from one national agency. Before relying on it, the same routes
were measured from the other end using Eurostat, which has no knowledge of the Indian
series.

| Country | DGCA (India end) | Eurostat (Europe end) | Gap |
|---|---|---|---|
| Finland | 149,508 | 149,551 | 0.0% |
| France | 964,079 | 955,339 | -0.9% |
| Switzerland | 340,372 | 343,583 | 0.9% |
| Germany | 1,744,685 | 1,766,890 | 1.3% |
| Netherlands | 664,238 | 673,438 | 1.4% |
| Poland | 108,223 | 109,731 | 1.4% |
| Denmark | 95,986 | 99,036 | 3.2% |
| **Italy** | **222,689** | **305,303** | **37.1%** |
| Total | 4,289,780 | 4,402,871 | 2.6% |

A regression test fails the build if the two ever diverge by more than 5% across the
countries both cover.

### The Italy dispute, unresolved on purpose

Milan to Delhi agrees to 1.6%. The entire Italian gap is one route: Eurostat reports
**171,942** passengers on Rome Fiumicino to Delhi in 2024, and DGCA lists **no Rome to Delhi
pair at all**. It is not a naming mismatch, since DGCA uses `ROME` elsewhere in the same file
for Rome to Amritsar.

Three explanations are possible and free sources cannot separate them: DGCA omits the route,
Eurostat counts something indirect as direct, or an operating carrier is filed differently
by the two agencies.

The pair is quarantined in `src.data_pipeline.DISPUTED_ROUTES`, excluded from any figure
depending on one agency being right, and reported with both numbers. A test stops it
silently rejoining the analysis.

---

### The 2019 United Kingdom anomaly, found and corrected

The UK is India's largest European market at 3.5M passengers, and Eurostat does not cover it
because the UK left the EU. Eurostat does still hold pre-Brexit data, so the market was
cross-checked for **2019** instead, and that check found a corrupt observation.

DGCA reports **2019 Q3 United Kingdom at 1,162,094** passengers against a 2015-18 third
quarter median of **654,870**, returning to 505,102 the very next quarter. The same event
inflates the London to Chennai city row to **570,763** against a decade-long baseline of
roughly 33,000 per quarter, seventeen times its own neighbours on either side.

Two independent lines of evidence, which is the bar for treating a value as wrong rather
than merely surprising:

1. **Its own history.** Forty other quarters of the same route sit near 33,000.
2. **A second agency.** Uncorrected, DGCA and Eurostat disagree on the UK by **25.8%**.
   Corrected, they agree to **2.5%**, which is exactly the agreement level seen on every
   other route the two agencies both cover.

**Why it mattered.** The pre-covid CAGR is fitted from 2015 to 2019, so an inflated endpoint
propagates into the trend leg of the market sizing and into all three demand scenarios.
Correcting it moved the CAGR from **7.176% to 6.964%** and the sizing band from 106M to 109M
down to **106M to 108M**. The core findings, which rest on 2024 and 2025 data, are unchanged.

The corrections live in `src.data_pipeline.COUNTRY_ANOMALIES` and `CITY_ANOMALIES`, are
flagged on every affected row by an `anomaly_corrected` column, and are guarded by four
tests. Nothing is removed on suspicion.

### How much of the analysis is actually cross-checked

Stated plainly, because the reconciliation above could imply more coverage than exists.

| | Passengers, 2024 | Share |
|---|---|---|
| Cross-checked against a second agency | 4.04M | **5.6%** |
| Single-sourced on DGCA alone | 68.17M | 94.4% |

This is not missing data. DGCA covers 100% of India's international traffic. It is that only
the European portion has an independent agency publishing the same routes from the other
end. The Gulf, which carries half the traffic and most of the argument, has **no equivalent
open source**: GCC civil aviation authorities do not publish route-level statistics in
machine-readable form.

So the honest position is that the DGCA spine has been validated where validation was
possible, and it passed. Extending that to the Gulf would need paid data (Cirium, OAG, or
IATA DDS) and is named in `ROADMAP.md` rather than glossed over.

---

## The profit pool, and everything modelled inside it

`src/profit_pools.py` is the most heavily modelled module in this repo, so it states its own
seams rather than leaving them to be found.

| Quantity | Status | Basis |
|---|---|---|
| Passengers per corridor | **Computed** | DGCA international country table, 2024, both directions summed |
| Corridor stage length | **Computed, but a reference** | Great circle from Delhi to one named hub per corridor, from committed OurAirports coordinates |
| Revenue per corridor | **Proxy** | Passengers x reference distance x IndiGo's verified FY2026 yield of 5.06 INR per RPK |
| Margin per corridor | **Modelled** | Linear in stage length, anchored to a published margin |

**Why the stage length is a reference and not a traffic-weighted mean.** A weighted mean needs
every DGCA city name matched to airport coordinates. DGCA writes city names, not IATA codes,
and matching them against OurAirports municipalities resolves 78% of foreign points and 62% of
Indian ones, roughly half the traffic once both ends must match. Publishing a weighted mean
that is quietly wrong for the unmatched half would be worse than publishing a labelled
reference distance, so each corridor names its hub (Gulf: Dubai, Europe: London, North America:
New York, and so on) and the reader can check any of them in a minute.

**The direction of the revenue error is known and is stated on the chart.** Yield per RPK
normally falls as stage length rises. Holding it constant therefore *overstates* long-haul
revenue, which means the Gulf-versus-long-haul gap the pool reports is a floor, not a ceiling.
An error whose sign is known is worth more than one that is merely small.

**The margin model has exactly one knob**, `MARGIN_STAGE_SENSITIVITY`, the spread in margin
points between the shortest and longest corridor. Margins are spread linearly across it, then
shifted so the *revenue-weighted* mean equals the anchor. Linear because no available evidence
justifies a richer shape, and a richer shape would imply precision this data does not have.
`profit_pools.sensitivity()` publishes the result at 6, 12 and 18 points: the Gulf's profit
share moves only between 29% and 25% across that whole range, against a 52% passenger share. A
conclusion that survives its own sensitivity is worth stating; one that does not is not.

**The anchor is quoted twice on purpose.** The revenue-weighted mean margin is pinned to
IndiGo's FY2026 EBITDAR margin **excluding forex, 27.3%**, because forex on USD lease
liabilities is a real loss but not an operating one, and attributing a treasury outcome to a
route would be wrong. But IndiGo **reported 17.8%** for the same year, and the chart says so.
Quoting only the ex-forex figure would repeat, with the sign flipped, the error retracted
below: that retraction was for reading a non-operating collapse as an operating one, and the
symmetric mistake is presenting an operating improvement as the whole story.

**One chart deliberately survives rejecting all of this.** `pax_vs_revenue_share` compares
share of passengers against share of revenue and contains no margin assumption at all. If a
reader throws out the margin model entirely, that chart still stands and still carries the
argument.

**The DGCA residual "Other" is excluded**, not silently dropped. It spans Central Asia to South
America, so no single hub represents it. The exclusion is recorded in `EXCLUDED_REGIONS`,
returned in the note on `gulf_share_gap()`, and covered by a test.

---

## Limits, stated rather than buried

**Yields are not published.** DGCA publishes no fares. Air India is unlisted and files no
exchange results, with partial visibility only through Singapore Airlines' 25.1% stake
disclosures. Every hand-entered number therefore carries a `status`, and `dp.assumption()`
raises `UnverifiedAssumption` rather than returning anything not marked `VERIFIED`.

Consequences, visible on the site rather than hidden:

- The **capacity leg of the market sizing is blocked**, and the chart says so
- **Profit pools are not built**, and a claim about the margin anchor has been withdrawn.
  See the retraction below.
- **Scenario analysis is built for demand only.** Base, bull and bear paths need nothing
  but passenger counts, all of which are measured. The fuel and FX levers are **absent
  rather than stubbed**: both price into revenue, revenue needs gated yields, and a lever
  that raises on every call is inventory rather than analysis. The chart states the omission

**World Bank air passenger data stops at 2023.** `IS.AIR.PSGR` has no values after 2023. It
supports cross-country elasticity fitting over 2010 to 2023; it cannot size a current year.

**Trend and propensity are not fully independent.** The propensity model's core (income
elasticity, GDP, population) is World Bank only. But two bridging ratios come from DGCA, so
the 3% agreement between the two methods is worth less than fully independent agreement
would be. Stated because the alternative is a flattering reading.

**Two sources were dropped after one attempt.** BTS T-100's static path returns 404 and the
only alternative is a form POST carrying ASP.NET viewstate. Indian Oil's fuel page is
JavaScript driven with no parseable table. The United States arm is therefore measured from
the India side only, and ATF price is a hand-entered row rather than a scrape. A documented
single-sided measurement beats an undocumented scraper that breaks in CI.

**Eurostat is a validation instrument, not a census.** Nine reporting countries return India
routes. Austria reports none for 2024 though DGCA shows 65,016. Eight member states return
nothing. European totals come from DGCA; Eurostat checks them.

**What a real engagement would add.** Cirium or OAG schedule and O-D data would resolve the
sector versus origin-destination gap directly rather than bounding it. IATA DDS would price
the connect premium. Bilateral seat entitlement data would answer whether the corridor can
legally absorb the capacity, which is the open question most likely to break the
recommendation. All are paywalled and none are used here.

---

## Retraction: the IndiGo margin claim

An earlier version of this project asserted that IndiGo's operating margin **halved from
22.3% in FY2025 to 14.0% in FY2026**, and treated that as a finding: the squeezed margin
from which wide-bodies would have to be funded. **That was wrong on both the number and the
conclusion.** It is recorded here rather than quietly deleted, because a project that claims
its numbers are traceable has to show what happened when one was not.

**What went wrong.** The figures came from an aggregator's "operating profit" line, taken at
face value. ₹18,050 cr is not a line item IndiGo publishes. It reconciles to a convention
(roughly EBITDAR less other income) that the company itself does not report, so it could
never have been verified against a primary source. Dividing one derived number by another
and calling the result an operating margin was the error.

**What the primary source actually says.** IndiGo's own reported figures:

| | FY2025 | FY2026 |
|---|---|---|
| EBITDAR | ₹212,520 mn | ₹231,889 mn (excluding forex) |
| EBITDAR margin | **26.3%** | **27.3%** |

The margin **improved**. It did not halve.

**What the apparent collapse actually was.** Non-operating. A Q4 net foreign exchange loss
of roughly ₹48,230 mn as the rupee depreciated against USD-denominated lease liabilities,
plus an exceptional provision of ₹2,499 mn for the new labour codes, taking IndiGo to a
full-year net loss of about ₹23,936 mn. A currency translation on leases is not an operating
squeeze, and presenting it as one would have put a false mechanism at the centre of the
recommendation.

**The real operating pressure, which is a genuine finding.** It sits in unit cost, not
margin. CASK rose from ₹4.66 to **₹5.00** while RASK fell to **₹4.99**, so unit costs
crossed above unit revenues. Non-fuel cost rose 27.8% while fuel cost fell 3.1%.

One caution that matters for the scenario model: of the ₹0.52 rise in CASK ex-fuel (₹3.00 to
₹3.52), only about ₹0.11 is genuine non-fuel inflation. The rest is forex. Anything running
a separate FX lever must use the ex-forex figure of ₹3.00, or it double-counts the same
currency move twice.

**Two related corrections from the same verification pass.** The value recorded as RASK of
₹4.51 was not RASK at all, it was IndiGo's Q4 FY2025 CASK, a cost mistaken for a revenue
metric. And the yield of ₹5.33 matched no published period; the closest real figure is Q4
FY2025 at ₹5.32. A cross-check I had described as corroborating those numbers was therefore
comparing a yield against a cost, and proved nothing.

---

## Conflicts flagged, never silently resolved

| Quantity | Competing figures | Why they differ |
|---|---|---|
| Gulf share of India international | 51.2% (DGCA sector, computed) vs ~40% (IATA O-D) | Sector counts the India-to-hub leg; O-D counts the real destination |
| India total passengers | 180.4M (World Bank, carriers-carried, 2023), 211M (IATA, 2024), 406M (DGCA, airport-handled, 2025) | Three different things counted. The definition is stated every time |
| Air India post-merger fleet | 198 / 205 / 218 | Varies by source date and by whether Vistara and Air India Express are consolidated |

---

## Reproducibility

```bash
pip install -r requirements.txt
python scripts/refresh.py
python -m pytest -q
```

Every figure on the site is regenerated by that one command from sources that are free and
machine readable. Nothing is typed by hand into the page. `data/data_dictionary.md` records
source, URL, pull date and reliability grade for every field, and `data/raw/MANIFEST.md`
records what was pulled and when.

The test suite is not decorative. Each test guards a specific way this source data has
already tried to produce a wrong headline number: two-digit years, `Total *` pseudo-airlines
that double count every passenger, and distance columns published in thousands.

---

## Architecture note

An early design review proposed a DuckDB layer between the raw cache and the analysis
modules. It was rejected: the whole corpus is roughly 90,000 rows and 15 MB, which pandas
holds in memory without effort, and Parquet via pyarrow already covers the storage need.
The dependency would have bought nothing.

Similarly rejected for the site: Streamlit, Panel, Superset, Redash and Vizro as a
framework. Each needs a running process, and GitHub Pages serves static files. Vizro was
adopted as a **code reference** instead, and its Mekko recipe is adapted here under
Apache-2.0 with three fragility fixes. See `NOTICE`.
