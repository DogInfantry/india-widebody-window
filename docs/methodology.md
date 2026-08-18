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
| **Profit pools** (Gadiesh & Gilbert, HBR 1998) | `src/profit_pools.py`. Built and populated. Margin axis modelled and labelled on the chart face |
| **Capacity absorption** | `src/fleet_gap.py`. What the order book can fly, in ASK, against what the market asks for |
| **Breakeven analysis** | `src/options.py`. How far yield can fall before a corridor stops covering its cost, in place of an NPV whose inputs cannot be verified |
| **Option evaluation** | `docs/recommendation.md`. Five options, each with what would have to be true, and the recommendation falling out of the breakeven table |
| **Hypothesis invalidation** | `docs/storyline.md` and `docs/recommendation.md`. A recommendation that cannot be falsified is not analysis |
| **Decision audit trail** | `docs/pivot_log.md`. Six documented changes of mind, each citing the commit it happened in |

Framework structure draws on
[DogInfantry/claude-skill-management-consultant-B1](https://github.com/DogInfantry/claude-skill-management-consultant-B1),
a reference library of 146 consulting modules, rather than being reinvented here.

---

## The measurement that matters most

**DGCA counts sector passengers, not origin-destination.** A passenger flying Delhi to Dubai
to London is recorded as a passenger to the United Arab Emirates. The India-to-foreign-point
leg is what gets counted; the rest of the journey is invisible.

This is why:

- DGCA sector data puts the Gulf at **50.9%** of India's international traffic
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

## A wrong bucket is still a valid bucket

`GULF_POINTS` listed `ABU DHABI` and `RAS AL KHAIMAH`. DGCA writes `ABUDHABI` with no space
and `RAS AL-KHAIMAH` with a hyphen. Exact string matching missed both, so **5.0 million
passengers a year, 20% of the Gulf hub flow**, were filed under "Everywhere else, direct" in a
chart whose entire argument is how much traffic disappears into a Gulf hub.

Nothing failed. Every test passed throughout, because a wrong bucket is still a valid bucket:
the shares summed to 100, the flows were positive, the Sankey rendered. This is the failure
mode that unit tests are worst at, and it is the second time this exact mistake has appeared
in this repo. The first was `AIR ARABIA-ABU DHABI`, recorded in the carrier-name notes. The
lesson was learned for carriers and never carried across to city points.

Fixed at the root rather than by patching two literals: `is_gulf_point()` compares on a key
with spaces and hyphens stripped, so the whole class is closed. A test now asserts that every
literal in `GULF_POINTS` resolves to a real DGCA city name, which would have caught it.

Found, incidentally, while building the bilateral seat check below. Eight foreign points also
turn out to carry freight and no passengers (Cologne, Leipzig, Liège, Luxembourg, Guangzhou
and Shenzhen among them), and DGCA spells two others `NOTTIMGHAM` and `TAIPAE`.

---

## Bilateral seat rights, measured from the only end that is open

Branch 4.3 of the hypothesis tree asks whether bilateral seat rights permit the deployment. It
is the most likely reason the recommendation fails, and it is the hardest thing in this project
to source.

**India does not publish entitlements.** The Ministry of Civil Aviation posts a *List of Air
Services Agreements* and, tellingly, a *Guidelines for publication/sharing of information
pertaining to Air Services Agreement*, but no seat table, and the agreements page returns 403.
Rajya Sabha Unstarred Question 827 of 27 July 2026 confirms the mechanism, that ASAs set
mutually agreed capacity limits and foreign carriers need a designated point of call, without
publishing a single number. The widely quoted 66,504 seats per week for India to Dubai comes
from trade press and an Observer Research Foundation report. It is `UNVERIFIED_NO_PRIMARY` and
labelled as such.

**So it was checked from the traffic end**, the same move used for DGCA against Eurostat and
IndiGo's block hours against DGCA. Passengers over load factor, halved because DGCA reports
both directions, over 52 weeks:

| | One-way seats per week |
|---|---|
| India-Dubai, implied by DGCA 2024 traffic | ~118,200 |
| Reported entitlement, two sides at 66,504 | 133,008 |
| **Utilisation** | **~90%** |

Two independent routes land in the same place. That corroborates the secondary figure and puts
a number on the headroom: **under 15% left on India's largest international city pair**, with
Emirates and flyDubai reported to be at their half already.

**The implication runs toward the recommendation, not against it.** Wide-body capacity aimed at
Dubai largely cannot be flown on existing rights. It has to go long-haul, or to Gulf points with
slack, or wait on a renegotiation India has so far declined.

Two cautions. The check assumes the standard reciprocal structure, both sides holding equal
entitlement, and it uses the all-India international load factor of 81.1% rather than a
Dubai-specific one. At a more realistic 85% the implied figure falls further below the cap. And
66,504 is **one emirate and one side**: India-UAE as a whole runs roughly 255,000 one-way seats
a week across Dubai, Abu Dhabi and Sharjah, which hold separate MoUs. Quoting the Dubai number
as the India-UAE cap would be wrong by a factor of about four.

---

## The Gulf is not uniformly capacity-capped, and saying so was a correction

The bilateral section above measures India-Dubai from the traffic end and finds it
at **88.8%** of its reported entitlement. That number was, for one commit, carried
as "there is no room in the Gulf" and used as the first leg of the recommendation.

Generalising the check to a second point showed the claim was too strong. Abu
Dhabi's entitlement could be found, from two independent secondary sources that
agree on **50,000 weekly seats one side**, and the same traffic-end inference puts
usage at about **70%**. Roughly 30,000 one-way seats a week are unused.

A third figure reconciles both. A trade report puts the India-Abu Dhabi market at
about 77,050 weekly seats each way at the start of a September, which sits under a
two-sided entitlement of 100,000 and above this project's DGCA-derived annual
average of 57,600. A seasonal peak above a yearly mean is exactly the relationship
those two numbers should have.

**What survives the correction**, and it is the number the recommendation now
rests on rather than the utilisation percentages: both points' remaining
entitlement together is about 2.3M seats a year, and flown at the Gulf's own
2,182 km sector it absorbs **roughly 4% of the order book**. The constraint on
Gulf deployment is therefore economic first and legal second, which is the reverse
of the original framing.

**Two limits, stated.** Sharjah holds the third UAE MoU and carries 2.3M
passengers a year; two timeboxed searches found no entitlement figure and none is
estimated, so the true Gulf headroom is larger than 5%. And the remaining eight
Gulf points have no findable entitlement either. This is a floor on Gulf headroom,
not a measurement of it, which is why the argument is built on the order book's
size rather than on the corridor being full.

---

## Aircraft utilisation, and a number that did not survive being checked

The capacity sizing leg needs one figure: hours flown per aircraft per day. It is reported on
an **owned-fleet** basis at **10.06**, and the basis is named on the chart rather than left to
the reader, because the two possible bases differ by enough to move the leg by a third.

**The figure has an independent cross-check, which is rare here.** IndiGo's FY26 annual report
gives 1,619,570 block hours (1,220,966 domestic plus 398,604 international) across 441 aircraft
at period end. DGCA's `aircraft_hours` gives 1,614,608 for the same carrier and the same year.
Two agencies, opposite ends, **0.31% apart**. That is the second both-ends check in this
project after DGCA against Eurostat.

**A number carried in the project notes did not survive.** Working notes recorded a "reported
~13 hours/day" against the DGCA-derived figure, and explained the gap as grounded aircraft.
The explanation was the right shape and the arithmetic was never done. Doing it:

| Grounded | Active | Hours/aircraft/day |
|---|---|---|
| 0 | 441 | 10.06 |
| 40 | 401 | 11.07 |
| 60 | 381 | 11.65 |
| **100** | **341** | **13.01** |

13 hours/day requires **100 of 441 aircraft grounded**. IndiGo does not disclose its grounded
count: the annual report confirms the situation and an IAE compensation plan in note 41 without
quantifying it, and the June 2026 analyst presentation labels an AOG bar with no number. Trade
coverage puts the 31 March 2026 figure in the 40s, which yields 11.07. The ~13 is most likely
stale, from FY2024 when groundings genuinely ran near 70 to 80.

So the plausible active-fleet range is roughly **10.5 to 11.7**, not 13, and the honest band is
much narrower than first assumed. The capacity leg runs on the owned-fleet figure alone, which
is the conservative end. The active row is closed as `NOT_AVAILABLE` rather than filled with a
round number nobody sourced, and it records which documents were searched so the next person
does not repeat the search.

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

## Capacity, measured in ASK rather than in aircraft

`src/fleet_gap.py` asks whether the order book is enough, and answers in **available seat
kilometres** rather than seats or aircraft. That choice carries the module. A seat is not a
unit of capacity until you say how far and how often it flies, and this case turns entirely
on how far: two carriers with identical fleets and identical load factors produce completely
different ASK if one flies Dubai and the other New York. ASK is also the denominator of CASK
and RASK, so the capacity side and the unit-economics side are denominated in the same thing.

**Two figures that would normally be assumed are computed.** DGCA publishes `aircraft_km` and
`aircraft_hours`, so block speed is a division, and `ask / aircraft_km` gives seats per
departure:

| Carrier, international 2025 | Block speed | Sector | Seats per departure |
|---|---|---|---|
| Air India | 698 km/h | 5,316 km | 254 |
| IndiGo | 656 km/h | 2,643 km | 207 |

Short sectors block slower, because taxi, climb and descent are a larger share of them. The
data reproducing a known physical relationship is a reason to trust the columns, and a test
pins the ordering.

**One thing is modelled: the delivery schedule.** The Airbus release confirming IndiGo's 60
firm A350s states no delivery timing, and one attempt to source it found none. So no start
year is asserted anywhere in the module. It appears only as a scenario axis, run at 2027,
2028 and 2029, and the headline figure does not need it at all.

**A reconciliation worth naming.** The order-book ASK computed here is the same quantity the
capacity sizing leg computes, reached from the other direction, and a test pins them together.
What the equivalence exposed is that the `block_hours = 7.5` constant inside the sizing leg
implies a sector of roughly 5,235 km. The capacity leg had always assumed the wide-bodies fly
long-haul. It just never said so.

---

## Corridor breakeven, and why it is not an NPV

`src/options.py` asks which way to add capacity. It deliberately does not build a discounted
cash flow. A ten-year NPV per option needs a discount rate, an aircraft capital cost, a
residual value and a corridor yield, and **not one of those can be verified against a primary
source here**: Air India is unlisted, DGCA publishes no fares, and aircraft transaction prices
are commercially confidential. Four unverifiable inputs stacked into one number produce a
figure that looks precise and cannot be checked, on a site whose whole claim is that its
numbers can be.

So the question is asked from the other end. Unit cost falls as sectors lengthen, so IndiGo's
published CASK is scaled across the corridors and the output is **how far yield could fall
before each stops covering its own cost**.

**Why headroom rather than a straight breakeven comparison.** The obvious exhibit is breakeven
yield against IndiGo's achieved 5.06 INR per RPK. It is also wrong, in a way this project has
already been caught by: yield per RPK falls with stage length, so holding it flat across an
11,755 km sector flatters long-haul, which is exactly the caveat the profit pool carries.
Modelling the yield decline as well would have added a second unverifiable knob. Reporting
headroom needs none, and puts the unknown on the reader's side of the line as a tolerance to
judge against.

**The one knob** is `CASK_STAGE_ELASTICITY`, default -0.25, meaning a doubled sector cuts unit
cost about 16%. It cannot be fitted from anything here, because IndiGo is the only Indian
carrier that publishes CASK and one point fits no curve. It lives as a module constant beside
`sensitivity()`, mirroring `MARGIN_STAGE_SENSITIVITY` in the profit pool, rather than in
`assumptions.csv`: a modelled knob has no source to verify against, so the gate could only
ever refuse it, and two copies of one number is the drift this project spends its effort
avoiding.

**One sensitivity stated before a reader finds it.** The result moves with the load factor
chosen. International sectors run at 81.1% and IndiGo's system at 84.8%, because domestic
flies fuller. International is the right basis for international corridors and is the one
used, but it is also the less flattering: at the system load factor the Gulf comes out at
roughly breakeven rather than about four points under. The ordering across corridors does not
change either way, and neither does the conclusion the recommendation turns on.

**It corroborates the profit pool from an unrelated direction.** The pool models margin
*upward* from an EBITDAR anchor; this scales cost *downward* from a published CASK. They share
nothing but the corridor distances and they rank the corridors identically. A test asserts the
rank correlation stays above 0.95.

---

## The origin-destination share, and a gate that was missing

The eleven point gap between DGCA's computed 50.9% Gulf sector share and the roughly 40%
origin-destination figure is the connect leak, and it anchors the recommendation.

**That 40% was carried as a hard number on the live site with no assumption row at all.** It
appeared in two conflicts tables with no URL and no pull date, so `dp.assumption()` never saw
it. By this project's own rule, that every hard number is either computed in-repo or carries a
source and a pull date, it should have been gated from the start and was not.

It now is, as `gulf_od_share_pct` with status `UNVERIFIED_NO_PRIMARY`. It can never clear:
IATA sells origin-destination data and publishes no free table, so there is no primary
document to check it against. It is read only through `allow_unverified=True`, in exactly one
diagnostic function, the same pattern `dubai_entitlement_check` uses for the bilateral
entitlement. Everything derived from it is reported as a band and labelled `MODELLED`, and a
test asserts the gate bites.

---

## Data vintage, and why two years appear on one page

Headline figures moved from **2024 to 2025 on 2026-08-18**, when it was noticed that the
constant driving them still said 2024 while a complete 2025 series sat in the repo unused.
The comment directly above that constant already said data ran complete through 2025, so this
was drift rather than a decision.

What moved, and none of it reverses anything:

| | 2024 | 2025 |
|---|---|---|
| India international sector passengers | 72.2M | **78.0M** |
| Gulf share | 51.2% | **50.9%** |
| Gulf against direct Europe | 4.2x | **4.1x** |
| Indian carrier share | 45.3% | **45.9%** |
| 2030 sizing band | 91M to 108M | **96M to 109M** |
| Demand scenarios | 102 / 108 / 134M | **104 / 109 / 131M** |

The growth rates behind the band and the scenarios are **unchanged**, because they are fitted
from history rather than from the base year. Only the level moved. The corridor ordering, the
yield headroom by corridor, the profit pool split and the absorption arithmetic are all
untouched.

**Two dates still appear on the page, deliberately.** The Eurostat reconciliation runs on
**2024**, because that is the last year both agencies publish complete, and it is labelled
as such where it appears. It validates the DGCA source rather than any one year's numbers,
so re-running it on a partial year would weaken it for no gain.

**Why the base year matters more than it looks.** It is also the launch point for every
projection to 2030, so moving it shortens the runway by a year and narrows the band. That is
why both constants moved together: leaving the sizing base on 2024 while the corridor figures
said 2025 would have put two different totals for the same market on the same page.

---

## Limits, stated rather than buried

**Yields are not published.** DGCA publishes no fares. Air India is unlisted and files no
exchange results, with partial visibility only through Singapore Airlines' 25.1% stake
disclosures. Every hand-entered number therefore carries a `status`, and `dp.assumption()`
raises `UnverifiedAssumption` rather than returning anything not marked `VERIFIED`.

Consequences, visible on the site rather than hidden:

All three consequences below have since been resolved, and they are kept here rather than
deleted because how a gate closes is worth as much as the gate. Each was unblocked by finding
a primary source, never by relaxing the rule:

- The **capacity leg of the market sizing was blocked** and the chart said so. It now runs.
  Seat counts came from the manufacturers' own airport planning manuals (Airbus `AC_A350`,
  Boeing `D6-58333` and `D6-86073`), and utilisation from IndiGo's annual report block hours
  cross-checked against DGCA. The band went from 106M to 108M on two methods to **91M to
  108M on three**, and the new leg is the low one, so closing the gap made the answer more
  conservative rather than more flattering.
- **Profit pools are now built**, in `src/profit_pools.py`, with the margin axis modelled and
  labelled as such. The withdrawn margin claim stands withdrawn; see the retraction below.
- **Scenario analysis now carries all three levers.** Demand was always built. Fuel and FX
  were called absent rather than stubbed, on the reasoning that both price into revenue and
  revenue needs gated yields. That reasoning was half wrong, and the wrong half is the useful
  part: they do not need a **yield**, they need a **unit cost decomposition**, which IndiGo
  publishes. Once CASK was split into fuel, dollar-linked and rupee components, both levers
  followed and reconcile to the published CASK to the paisa.

What remains genuinely gated is narrower than it was. Air India's yield is `NOT_AVAILABLE`
because the company is unlisted and files nothing; the Gulf hub connect premium is `MODELED`
because nobody publishes it; IndiGo's grounded-aircraft count is `NOT_AVAILABLE` after two
primary documents were searched. All three are terminal states, not pending work.

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
| Gulf share of India international | 50.9% (DGCA sector, computed) vs ~40% (IATA O-D) | Sector counts the India-to-hub leg; O-D counts the real destination |
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
