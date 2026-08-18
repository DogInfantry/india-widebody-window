# Make it a company case: restore what was lost, then add the client work

## Context

Two separate failures, and the first one is mine to own plainly.

### Failure 1: the app is thinner than the site it replaced

I built five routes and called it a delivery layer, but I ported a fraction of the content.

| | Original `docs/index.html` | The Next.js app | Lost |
|---|---|---|---|
| Exhibits | **18** | 11, four of them partial | **8** |
| Narrative steps with action titles | **22** | 0 | **22** |
| Distinctive chart forms | Mekko, Sankey, waterfall, slope, frontier | waterfall, frontier | **Mekko, Sankey, slope** |

The eight dropped exhibits: `gateway_flows` (the Sankey showing where the passenger vanishes),
`profit_pool` (the Mekko), `fleet_gap` (the gap path over time), `scenarios`, `value_at_stake`,
`who_carries_india`, `load_factor_slope`, `domestic_share`.

Those include the three most visually distinctive things in the project. The site did not get
better and scattered by accident: it got **thinner and spread over five routes**, which reads
as scattered because there is less on each one.

**I was also wrong to recommend dropping `/story`.** The 22-step narrative was the original's
spine. Dropping it is a large part of why the app feels like a sector summary.

### Failure 2: the client is invisible

`docs/storyline.md` already contains, written and test-guarded:

- **Client:** IndiGo (InterGlobe Aviation), network and fleet strategy
- **The decision:** 60 A350-900s on firm order plus 40 purchase rights, where to deploy them
- **Timeframe:** through 2030
- **Success metrics**, including one the app never shows: **RASK 4.99 against CASK 5.00, FY2026,
  currently inverted.** IndiGo does not cover its unit cost. That is arguably the sharpest
  number in the project.
- Full SCQA, and an explicit "what this deliberately is not"

None of it reached the app. The analysis was always IndiGo-anchored; the delivery never said so,
which is exactly why it reads as sector research.

### What the financial data actually supports

Already gated and committed: revenue FY25 80,803 and FY26 84,962 crore, EBITDAR 21,252 and
23,189 crore, reported margin 17.8% **and** ex-forex 27.3% (both must appear, gotcha 19), CASK
5.00, RASK 4.99, yield 5.06, CASK ex-fuel 3.52, ex-fuel ex-forex 3.00, ATF, dollar exposure,
utilisation 10.06, 60 A350s on order. **Gulf carrier yield 9.924 INR per RPK** against IndiGo's
5.06 is the competitive pricing evidence, and it is already in the repo.

No balance sheet, no ROIC, no WACC. Per your decision, this stays a P&L, unit-economics and
capital-scale case, and says so.

### Decisions taken

Financials: P&L + unit economics + capital scale, no new sourcing risk. Structure: add
`/company`, keep everything else. Driver tree: revenue, profit, reach, competitive position.
Deck: all four kinds of polish. Nothing that exists is erased.

---

## The idea that fixes "all over the place"

**The value-driver tree is the site's navigation, not an ornament.**

Most driver trees on consulting sites are decoration: a box diagram nobody clicks. This one is
the index. Root question at the top, four branches, every leaf carrying its computed number and
linking to the exhibit that proves it.

```
Does the wide-body order create value for IndiGo?
├── PROFIT      can it earn?      (RASK − CASK) × ASK        spread is −0.01, inverted
├── REVENUE     can it fill?      ASK × load factor × yield  81.1% LF, yield 5.06
├── REACH       can it fly there? stage length, entitlement  2,643 km, Dubai 88.8% used
└── COMPETITIVE can it win?       yield vs Gulf carriers      5.06 against 9.924
```

That is not four frameworks rammed together: it is one identity decomposed. Revenue and profit
share the same ASK term, reach is what sets the stage length inside yield, and competitive
position is what determines whether the yield holds. Each branch fails for a different reason,
and the recommendation is the branch that survives.

It answers your question directly. We are optimising **profit per unit of committed capacity**,
and the levers are price (yield), fill (load factor), distance (stage length) and who else is
selling the same seat.

---

## Presentation and interaction design

This has to survive being put on a screen in front of a client. Three rules, and the point of
all three is **one grammar reused everywhere** rather than more elements. A reader should learn
the interaction once, on the first exhibit, and never think about it again.

### 1. Every decision has the same three layers, switched by tabs

The current `Exhibit` component has a single "The evidence" disclosure. It becomes a tabbed
panel with a fixed vocabulary, and **a tab only appears when it has content**, so nothing is an
empty shell:

| Tab | What is behind it | Where it comes from |
|---|---|---|
| **Exhibit** (default) | The action title and the chart. Nothing else | the export |
| **Evidence** | The two or three sentences that argue the claim, and the figures in prose | written, T-model |
| **How it was computed** | The module and function, the modelled knobs, the sensitivity | `src/` docstrings and the registry |
| **What would break it** | The risk row and its leading indicator, or the assumption that is not verifiable | `narrative.risks`, the assumption gate |

That is the answer to "show depth behind the decision". A partner sees one chart and one
sentence. When they push, the depth is one click away and it is always in the same place.

**Restraint rule:** four tabs maximum, never nested, never a tab inside a tab. If an exhibit
needs a fifth, it is two exhibits.

### 2. Chart form is chosen by the question, not by habit

Mechanical is what happens when every exhibit is a bar chart. The fix is not more chart types,
it is the right one each time and never more than one idea per exhibit.

| The question | Form | Exhibits here |
|---|---|---|
| How big, ranked? | horizontal bar | corridor scale, yield headroom |
| What share, of what size? | Mekko | profit pool |
| Where does it go? | Sankey | gateway flows |
| What changed, and why? | waterfall | CASK bridge, revenue bridge |
| Two things, are they related? | scatter, area = weight | capability, stage vs headroom |
| Same measure, many groups? | slope | load factor, share trend |
| Trade-off between two axes? | 2x2 | option menu |
| A path over time? | line with a band | fleet gap, scenarios |
| Position on a scale? | bullet or gauge | entitlement utilisation |

If a chart needs a legend of more than three items, it is two charts.

### 3. Annotation carries the argument, not decoration

- **Exactly one annotated point per exhibit**: the place where the so-what happens, labelled on
  the chart face. The 88.8% bar, the zero line the Gulf sits under, the year the lines cross.
- **Direct labelling over legends.** Label the line at its end. A legend makes the reader look
  away from the data and back again.
- **One red per exhibit**, already a rule and already tested. Red is the argument. Everything
  else is grey and recedes.
- **Value labels only where a reader would otherwise squint**, never on every bar.
- No gridline on the category axis, no tick marks, no gradients, no shadows, no rounded corners
  on data marks, no animation on load.

### What NOT to add, written down so it does not creep in

No dark mode. No theme switcher. No sparkline in every KPI card. No icon set. No "insights"
panel that restates the title. No carousel. No modal. No tooltip that is the only way to read a
value. No second accent colour.

### Client-facing checklist, verified before it is called done

Every exhibit carries a source line. Every route prints cleanly. No layout shift on load. No
empty states, no placeholder text, no route that 404s. Charts render at 1280 and at 375. The
deck runs fullscreen from a keyboard with no visible browser furniture. Every number on screen
can be traced to a module function in one click.

---

## Plan

### W1. Restore parity. Nothing new, just the eight exhibits that were dropped

Port to React against the existing export, adding datasets to `src/app_export.py` where needed:
`gateway_flows` (Sankey via `react-plotly.js`, already the plan for exotic charts),
`profit_pool` (Mekko via Visx, the Vizro-derived builder in `src/charts.py::mekko` is the
reference), `fleet_gap` path, `scenarios`, `value_at_stake`, `who_carries_india`,
`load_factor_slope`, `domestic_share`. **Result: 19 exhibits in the app, one more than the
original**, because the option 2x2 and risk heatmap are additions.

### W2. `/story`, restored. The 22-step narrative

Reversing my own recommendation. Sticky-graphic scrollytelling, the same step order and action
titles as `docs/index.html`, prose cut to one claim per step with the rest behind the T-model
disclosure. Parse the step headings out of `index.html` so the two surfaces cannot diverge, the
same way the option menu and risk register are parsed from `recommendation.md`.

### W3. Frame the case on `/`

Parse `docs/storyline.md` into the export: client, decision, timeframe, success metrics, and
the "what this is not" paragraph. Landing becomes: client and decision box, SCQA, the
**success-metric scorecard** (four metrics, each with where it stands today and whether it is
moving the right way), the driver tree as navigation, then the three proof exhibits, then the
doors. Nothing currently on the landing is removed.

### W4. `/company`. The client, and the work that was missing

New module `src/financials.py`, computed from the gated rows, plus new exhibits:

- **Revenue bridge** FY25 to FY26, and what the order book would add at today's unit revenue
- **Margin ladder** showing reported 17.8% and ex-forex 27.3% side by side, with the retraction
  note, because publishing one without the other is the error this project already made once
- **The inverted spread**: RASK 4.99 against CASK 5.00, and what stage length would fix it
- **Cost decomposition**: CASK, ex-fuel, ex-fuel ex-forex, with the currency contribution
- **Capital scale**: 60 A350s against annual EBITDAR, stated as order of magnitude rather than
  a financing plan, since financing is explicitly out of scope
- **Competitive position**: IndiGo yield 5.06 against the Gulf carrier 9.924, with stage length,
  load factor and share against Air India and the Gulf three
- **Operations**: utilisation 10.06, block hours reconciled to DGCA at 0.31%, fleet and network
  shape

### W5. Deck polish, all four kinds

Cover naming client and decision, agenda, executive-summary slide carrying SCQA, section
dividers, page numbers, a source line on every slide. The new company slides. Visual craft:
one type scale, consistent chart height and margin, a takeaway strip under each exhibit.
Speaker support: presenter notes per slide, a five-minute path and a fifteen-minute path, and
an appendix of backup exhibits behind the main flow.

### W6. Sweep the record

`CLAUDE.md`, a pivot-log entry for the delivery-thinning audit, and
`docs/external_review_response.md`, which currently claims G1 (named client) was done when the
delivery never showed it.

---

## Order of work

W1 and W3 first: parity plus the client frame is what turns this from a sector page into a case,
and both are cheap because the content exists. Then W4, which is the new analysis. Then W2 and
W5, which are the largest and benefit from everything else being settled. W6 last.

## Verification

| Check | How |
|---|---|
| Parity is real | Count exhibits in the app against the 18 in `docs/index.html`; a test asserts every chart id in `index.html` has an app counterpart or a recorded reason |
| The client is unmissable | The word IndiGo, the decision and the timeframe appear above the fold on `/`, and on the deck cover |
| The inverted spread is stated | RASK 4.99 against CASK 5.00 appears on `/`, `/company` and the deck, from the export, not typed |
| Both margins appear together | A narrative-guard entry fails the build if 27.3% appears without 17.8% nearby |
| Nothing was erased | `git diff` shows no deletions in `docs/`; the mirror stays byte-identical |
| Numbers still agree | `python -m pytest -q` green, and the export drift guard catches a stale rebuild |
| Driver tree navigates | Every leaf links to a rendered exhibit; a test asserts no leaf points at a missing anchor |
| It reads as a company case | Timed pass: within 30 seconds a reader can say who the client is, what is being decided, and what the answer is |
| One grammar, not many | Every exhibit uses the same tabbed component; a test asserts no exhibit declares a tab outside the fixed vocabulary, and none has more than four |
| Every exhibit argues | A test asserts each registry entry has an annotation and a source line; an exhibit with neither fails the build |
| Form follows the question | Review pass against the form table: no two consecutive exhibits share a form unless the comparison is the point |
| Presentable | Fullscreen the deck on a 1280 screen and read it end to end with the keyboard; print every route to PDF; load with the network throttled and watch for shift |
