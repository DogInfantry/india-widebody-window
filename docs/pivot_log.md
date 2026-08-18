# How this analysis changed

Six times, evidence turned the work against what it had been assuming. Once it changed the
recommendation. Once it reversed the premise of the whole case. Once it forced a published
claim to be withdrawn. Once it found a wrong answer that every test in the repo had passed.

They are recorded here for one reason: a case that arrives in a straight line was either
trivial or is hiding something. Each entry names what was believed, what the evidence said,
what changed as a result, and the commit where it happened, so any of it can be checked.

Ordered by how much each changed the answer, not by date.

---

## Pivot 1. "Gulf first" became "compete with the Gulf hubs, do not fly to them"

`fe43dd5` *Ask what each corridor must earn to cover its cost, and find the Gulf tightest*
and `3ac7729` *Measure the order book in ASK, and find it is sized for a longer network*

**What was believed, and it was this project's headline.** Reclaim the India-Gulf corridor
first, defend long-haul second. The corridor is half of India's international traffic and four
times the entire direct Europe market, so that is where the wide-bodies should go.

**What the evidence said.** The traffic is there. The aircraft cannot be. Three independent
lines, none of which existed when the headline was written, say so:

1. **The room that exists is trivial next to the aircraft.** India-Dubai runs at **88.8%**
   of its reported bilateral entitlement. This was first written as "there is no room in the
   Gulf", which was an overstatement: checking the second point found **Abu Dhabi at about
   70%**. What survives is the number that matters, that both points' remaining entitlement
   absorbs only **about 4% of the order book** at the Gulf's own sector length. The
   constraint is economic first and legal second.
2. **The unit economics are the worst on the map.** Scaling IndiGo's published unit cost across
   the corridors, the Gulf has the **least** room of any to absorb a yield decline, because
   sectors that short keep cost per seat kilometre high. Europe could take about a fifth off
   the fare and still clear its cost. The Gulf does not clear its cost today.
3. **The order book is sized for a longer network.** The 140 firm wide-bodies would add **78%**
   to Indian carriers' international capacity. Holding share needs about half that. The book
   clears only if the average sector lengthens roughly **27%**, or if share reaches 58%.
   Pointing them at 2,200 km Gulf sectors leaves most of that capacity doing nothing the
   existing narrow-bodies could not.

**What changed.** The recommendation, and with it the headline of the site. The Gulf corridor
stays the strategic centre of the case, because that is where the traffic and the contested
revenue are. The aircraft point somewhere else.

The reconciliation is in the traffic split. Of 39.7M Gulf passengers, roughly **31.2M are
genuinely point-to-point**, the diaspora and labour corridor that Kochi feeds, already served
by narrow-bodies that suit it. About **8.5M are connecting** onward to Europe and North
America on a Gulf carrier, and that traffic is worth INR 28,900 to 56,700 crore. It is won by
flying past the Gulf, not to it. Which is a long-haul move.

**Why it is the first entry.** It is the only one that changed the answer rather than the
evidence behind it. It also matters that the case did not need rescuing to survive it: every
supporting exhibit stands unchanged, and the new recommendation uses more of them than the old
one did.

**What it should have caught earlier.** Branch 4.3 of the hypothesis tree already said
incremental Gulf capacity "has to go long-haul, or to Gulf points with slack, or wait on a
renegotiation India has so far refused". That conclusion sat in the tree and never propagated
to the storyline or the headline. The analysis was ahead of the write-up for a while, which is
its own lesson.

**Where it lives.** `docs/recommendation.md`, `src/options.py::corridor_economics`,
`src/fleet_gap.py::absorption_summary`, `benchmarking.dubai_entitlement_check`.

---

## Pivot 2. "India is losing its own market" became "India is winning it, just not in long-haul"

`9c473a9` *Find three carrier classification bugs; one reverses the premise*

**What was believed.** The case opened on the standard framing: Gulf carriers are eating
India's international market, Indian carriers are in retreat, and the wide-body order is a
rescue. It is the version of this story that gets written most often, and the blueprint this
project started from assumed it.

**What the evidence said.** The opposite. Indian carriers went from **37.0%** of India's
international sector passengers in 2015 to **45.9%** in 2025, while Gulf carriers fell from
32.7% to **26.2%**. Not an industry being routed. One closing on parity.

The finding only surfaced because three carrier classification bugs were fixed first. One of
them, `GRAND TOTAL` sitting in the 2019 international carrier file worth 17.53M passengers,
was being counted as a foreign airline. Until that row came out, the trend was measurably
wrong in the direction that flattered the original premise.

**What changed.** The storyline was rewritten around the finding rather than against it. The
argument became sharper, not weaker: the share Indian carriers have taken back is short-haul,
Gulf and Southeast Asia, flyable with the narrow-bodies they already own. The deficit that
remains sits precisely where aircraft range binds. That is a better case for a wide-body
order than "we are losing", because it identifies the constraint instead of describing a
symptom.

**Where it lives.** `src/benchmarking.py::carrier_share_trend`, hypothesis tree branch 2.3,
and the `carrier_share_trend` exhibit.

---

## Pivot 3. A wrong answer that passed all 72 tests

`f9359d0` *Quantify the bilateral constraint, and fix a bucket bug it exposed*

**What was believed.** That the Gulf-hub flow diagram was right, because the test suite was
green.

**What the evidence said.** `GULF_POINTS` listed `ABU DHABI` and `RAS AL KHAIMAH`. DGCA writes
`ABUDHABI` and `RAS AL-KHAIMAH`. Exact string matching missed both, filing **5.0M passengers a
year, about 20% of the entire Gulf hub flow**, under "Everywhere else, direct" in the Sankey.

**All 72 tests passed the whole time, because a wrong bucket is still a valid bucket.** Shares
summed to 100. Flows were well formed. Nothing was null. Every property the suite checked was
true of an answer that was wrong.

Worse, the same failure mode had already been found once, in carrier names, where
`AIR ARABIA-ABU DHABI` used a hyphen where the list used a space. The lesson was learned for
carriers and never carried across to city points.

**What changed.** Matching now goes through `is_gulf_point()`, which compares on a normalised
key and fixes the whole class rather than the two names that happened to be noticed. Three new
tests were added, and they check the thing that actually failed: that every literal in
`GULF_POINTS` matches a real DGCA name, that matching survives spacing and hyphen variants,
and specifically that Abu Dhabi lands in the Gulf bucket.

**Why this one is in the log.** It is the least flattering entry and the most useful. A green
suite is evidence that the properties you thought to check are holding, and nothing more. The
bug was found by going looking for a bilateral seat number, not by any test.

**Where it lives.** `src/benchmarking.py::_norm_point`, and the three tests named above.

---

## Pivot 4. A published margin claim, withdrawn

`9f76662` *Adopt the verification vocabulary, and retract the IndiGo margin claim*

**What was believed, and stated on the page.** That IndiGo's operating margin had **halved
from 22.3% to 14.0%**, and that wide-bodies would have to be funded out of that squeeze.

**What the evidence said.** The figures came from an aggregator's "operating profit" line.
₹18,050 cr is not a line item IndiGo publishes; it reconciles to a convention the company
does not report, so it could never have been verified against a primary source. Against the
company's own filings the margin **improved**, EBITDAR 26.3% to 27.3% ex forex.

**What changed.** Three things, and the third matters most.

1. The claim was withdrawn, and the retraction is kept in `docs/methodology.md` rather than
   quietly deleted.
2. The real operating pressure was found where it actually sits, in unit cost rather than
   margin: CASK rose 4.66 to 5.00 while RASK fell to 4.99, so unit cost crossed above unit
   revenue. That became the CASK bridge exhibit, and the bridge shows currency added +0.41
   against a net rise of +0.34, because fuel fell.
3. **The symmetric error was then guarded against.** IndiGo *reported* an FY2026 EBITDAR
   margin of **17.8%**; 27.3% is ex forex. The profit pool anchors on ex forex, which is
   correct because forex on USD lease liabilities is a treasury outcome and not a route one,
   but quoting only 27.3% would be the retracted mistake with the sign flipped. Both numbers
   now appear wherever either does.

**What it cost.** The whole verification vocabulary in `data/manual/assumptions.csv` exists
because of this. `dp.assumption()` now refuses to let an unverified number reach a published
chart, and it has blocked real work since.

**Where it lives.** `docs/methodology.md`, retraction section. Assumption rows
`indigo_operating_profit_fy2025_inr_cr`, `indigo_operating_profit_fy2026_inr_cr` and
`indigo_ebitdar_margin_fy2026_reported_pct`.

---

## Pivot 5. Verifying the gated numbers made the recommendation harder to argue

`9866c76` *Close the capacity sizing leg from primary manufacturer manuals*
and `c124d6e` *Weight the capacity leg by variant instead of one seat count for every tail*

**What was believed.** That the capacity leg of the market sizing was blocked on paperwork.
Find the seat counts, unblock the method, move on.

**What the evidence said.** The seat counts came from the Airbus and Boeing airport planning
manuals at published two-class layouts, and the utilisation from IndiGo's own block hours. The
leg then ran and produced **90.7M**, which is the **low** end of the band. Verifying the gated
inputs widened the range downward, from 106M to 108M on two methods to **96M to 109M** on
three.

A second correction followed inside the same leg. Counting all 140 wide-bodies at A350-900
seating understated the order book by about 5%, because the A350-1000 and the 777-9 are
materially larger aircraft. Weighting by variant fixed it, and the two variant assumptions
that remain are surfaced on the chart face rather than buried in code.

**What changed.** Nothing was relaxed to make this work, and that is the entry. Note the
direction: the gate that had been holding the number back opened onto a result that made the
case harder to argue, not easier.

**A gate that only ever unlocks good news is not a gate.**

**Where it lives.** `src/market_sizing.py::estimate_capacity`, and
`test_capacity_leg_runs_now_that_every_input_is_verified`, which was written by inverting the
test that used to assert the leg was blocked.

---

## Pivot 6. A widely quoted utilisation figure that did not survive arithmetic

`edc18d1` *Close the active-fleet utilisation row, and retire a number that failed its check*

**What was believed.** That IndiGo runs its fleet at roughly **13 block hours per aircraft per
day**. The figure appears in trade coverage and had been carried in this project's own notes.

**What the evidence said.** It cannot be reconciled with the company's published block hours.
IndiGo flew 1,619,570 block hours in FY2026. At 13 hours a day that requires 341 active
aircraft, meaning **100 of 441 grounded**. Reported groundings for 31 March 2026 were in the
40s, which gives **11.07**. The plausible active-fleet range is about 10.5 to 11.7, not 13.

The number is probably not invented, just stale, from FY2024 when groundings genuinely ran
near 70 to 80.

**What changed.** The figure was retired. The capacity leg runs on the **owned-fleet** basis
of 10.06 hours per aircraft per day, which is the conservative choice, and the chart names
that basis rather than leaving a reader to assume. The active-fleet row was closed as
`NOT_AVAILABLE` after two primary documents were searched and neither disclosed the grounded
count, so it reads as resolved rather than as outstanding work.

The block-hour figure that replaced it was then cross-checked in its own right: DGCA
independently reports 1,614,608 hours for the same carrier and year, **0.31%** apart. That is
the second both-ends check in the repo, after DGCA against Eurostat.

**Where it lives.** Assumption rows `aircraft_utilisation_hours_per_day` and
`aircraft_utilisation_hours_per_day_active`.

---

## What these have in common

Four of the five were found by cross-checking one source against another, or one number
against its own arithmetic. None were found by inspection, and none by the test suite.

That is the argument for the reconciliation work on this site being an exhibit rather than an
appendix. DGCA against Eurostat, DGCA against IndiGo's block hours, implied seats against a
reported bilateral entitlement: each of those is a chance for something to disagree, and
disagreement is the only mechanism here that reliably surfaces a wrong answer.

The corollary is uncomfortable and worth stating. **Only 5.6% of India's international traffic
is cross-checked against a second agency.** The Gulf, which carries half of it, has no
equivalent open source. Everything on this site about the Gulf rests on one agency's numbers,
and the checks that caught these five pivots cannot be run there.
