# What the external review asked for, and what was built

An external review of this project (Fable, 2026-08-18) proposed rebuilding it as Next.js on
Vercel with seven routes, a discounted cash flow model per option, a Puppeteer export route and
a new palette. **The analytical half was taken almost in full and it changed the answer of the
case. The delivery half was refused, with one exception: Vercel hosting, which is now live.**

This file exists because the decisions are otherwise recorded only as a summary in `CLAUDE.md`,
and because a reader who wants to know whether the criticism was answered or dodged is entitled
to see it item by item, including the parts that were dodged.

## What the review got right

One sentence in it was worth the whole document: the piece answered *what is happening in the
India long-haul market* and never forced a named decision-maker to a costed choice. That is the
difference between a market study and a case, and it was true.

Acting on it produced `src/fleet_gap.py` and `src/options.py`, and those two modules **inverted
the recommendation**. The headline was "reclaim the Gulf corridor first". It is now "compete
with the Gulf hubs, do not fly more aircraft to them". The review itself predicted the opposite
pivot, listing "go West, then Gulf-corridor recapture first" as its candidate pivot 2. The
evidence went the other way: India-Dubai runs at 88.8% of its reported entitlement, Gulf sectors
have the least yield headroom of any corridor, and the firm order book is 1.94x the growth
needed to hold share. The corridor is still the prize. It is won by flying past it.

## Four forks, decided before any code

| Fork | Chosen |
|---|---|
| Delivery stack | Enhance the static site in place. No Next.js rebuild |
| Client framing | Name IndiGo, keep every number computed in-repo. Not the trade-press framing |
| Financial model | Breakeven and value at stake. Not a four-seam NPV |
| Scope | All four analytical workstreams |

## The eight gaps

| # | The gap as stated | Status |
|---|---|---|
| G1 | No named client or decision | **Done, and this entry was wrong for one commit.** IndiGo and the decision were named in `docs/storyline.md` and `docs/recommendation.md`, which is what this row originally claimed. They were named nowhere in the **delivery layer**, and that is the distinction the review was actually making: a reader arriving at the site could not say whose decision it was. Closed properly in `52aa12c`, which puts the client, the decision, the horizon, the SCQA and the success metrics on `/`, adds `/company`, and parses all of it from `storyline.md` rather than retyping it. Recorded as pivot 8 |
| G2 | No options with quantified trade-offs | **Done.** Five options, each with what would have to be true, in `options.py` |
| G3 | No financial model | **Done differently.** Capacity absorption in ASK, corridor breakeven, yield headroom, value at stake. The NPV is refused, see below |
| G4 | No roadmap, WWHTBT, risk register, leading indicators | **Done.** All four in `docs/recommendation.md`, the risk register nine rows |
| G5 | Supply side thin | **Done for the constraints that bind here.** Order book converted to ASK, absorption frontier, bilateral entitlement utilisation (Dubai 88.8%, Abu Dhabi 70.1%). **Not done:** OEM delivery slots and engine programme status, which are dated trade-press claims that cannot be computed in-repo and would sit outside the provenance contract |
| G6 | Static, non-interactive, single page | **Done in part.** A scenario selector, a slide view (`deck.html`), a print edition (`report.html`), two committed PDFs and a two-page brief. **Not done:** live API feeds and a filterable dashboard, both of which need a running process |
| G7 | Competitive and financial grounding light | **Done.** `src/benchmarking.py` on share, stage length and load factor; the CASK bridge from the filings; DGCA reconciled against IndiGo's own block hours to 0.31% |
| G8 | Macro linkage underused | **Already existed.** `scenario.fuel_fx_sensitivity()` wired fuel and FX before the review was written. This gap was not real |

## The model spec, 5a to 5e

- **5a, demand band.** Already existed and was kept. Now 96M to 109M by 2030 on a 2025 base,
  reported as a band across three methods and never as an average.
- **5b, fleet gap.** Built as `src/fleet_gap.py`, but **in ASK rather than seats**. A seat is
  not capacity until you say how far and how often it flies, and this case turns on how far.
  ASK is also the CASK and RASK denominator, so capacity and unit economics share a unit.
- **5c, unit-economics option comparison.** Built as `src/options.py`: corridor breakeven
  against IndiGo's published unit cost, scaled by stage length.
- **5d, NPV, scenario table and tornado. Refused.** A discounted cash flow per option needs a
  discount rate, a capital cost, a residual value and a corridor yield. Not one of the four is
  verifiable from anything this repo can cite, so the output would be a number whose precision
  came entirely from assumptions the reader cannot check. `options.py` asks the same question
  from published unit costs instead and reports yield **headroom**, which leaves the unknown on
  the reader's side of the line. The review also asked for the model to be mirrored as an Excel
  exhibit "for the JD". That is a hard rule here: no Excel as output or intermediate.
- **5e, risk matrix.** Built, as a nine-row register with likelihood, impact and a named
  mitigation each.

## The delivery design

Rejected: Next.js App Router, Tremor, Recharts, Visx, react-scrollama, Framer Motion, Puppeteer
with `@sparticuz/chromium`, and the charcoal-and-blue palette. The reasoning was not preference.
A rebuild is several weeks that produce zero new analysis, rewrite all 19 charts, and break two
decisions the project is built on: seven Python packages, and no build step. Scrollytelling
already worked here through `scrollama.js`. The PDFs are rendered by local Chrome against the
same print CSS a reader's browser uses, which needs no Node toolchain and no cold-starting
function to produce a file that changes about as often as the headline does.

**Vercel hosting was a separate question and it was conflated with the rebuild for most of a
day.** Serving the same static files on Vercel costs nothing, adds a preview deploy per branch,
and gives a cleaner URL. It is live at `india-widebody-window.vercel.app`, with GitHub Pages
kept as a working mirror.

## Chart inventory

The review proposed 14 exhibits with action titles. The repo exports **19**, every title stating
its takeaway rather than its topic, and a test fails the build if one does not. Of the review's
fourteen, the ones with no counterpart here are all downstream of something that was refused or
could not be sourced: the NPV bars and the tornado, and the two supply exhibits that would have
been drawn from paywalled slot and lease-rate data.

## Three things in the review that were wrong

1. **"India-UAE capped at 66,504 seats/week each side, a hard ceiling."** That figure is one
   emirate and one side. India-UAE runs roughly 255,000 one-way seats a week across three
   separate memoranda. Wrong by about 4x, and load-bearing for its argument, because the review
   used the cap to conclude that direct service was forced.
2. **"Mirror one clean Excel exhibit for the JD."** No Excel, as output or intermediate. The
   posting asks for model building, which this repo evidences in Python.
3. **"Fuel and FX are not wired to the model as sensitivity drivers."** They already were.

## What it opened that is still open

- **Wide-body lease rates.** The largest named unresolved input. The damp-lease bridge option is
  presented with its economics explicitly unquantified, because IBA and Cirium transaction rates
  are paywalled. The review quoted them from trade press, which is a secondary citation of a
  paywalled primary, and that is not accepted here for a number that would drive a
  recommendation.
- **Bilateral entitlements for Sharjah**, the third Gulf point with a separate memorandum.
- **A both-ends reconciliation for India to United States**, as Eurostat already provides for
  India to Europe. BTS T-100 was attempted and is recorded as a dead end.
- **Belly cargo revenue.** The physical freight flows through the pipeline and `src/cargo.py`
  reports it. There is no revenue leg, so it does not reach the recommendation.
- **Survey analysis.** `docs/survey_design.md` designs a conjoint instrument for the softest
  number in the case. Coverage still counts survey analysis as a gap at 82%, because designing
  a survey is not analysing one.

<!-- narrative-guard: ignore, the three figures below are the review's own and were superseded when the data vintage moved to 2025 -->
*A note on the review's numbers.* It was written against the 2024 vintage of this project and
quotes 72 million international passengers, a 91 to 108 million band, and a 51.2% Gulf sector
share. All three moved when the headline year became 2025. They appear here as the review had
them, not as current figures.
<!-- /narrative-guard -->
