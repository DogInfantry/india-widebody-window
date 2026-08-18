# A conjoint instrument for the number this case cannot verify

**Status: designed, not fielded.** There are no responses, no results and no
findings here. This document is the instrument, the sampling frame and the
analysis plan, written to the point where someone with a panel budget could run
it on Monday. Nothing in the case rests on it.

That distinction is the whole point of the document existing, so it is stated
first rather than buried: **designing a survey is not analysing one**, and
`docs/coverage.md` still reports survey analysis as a gap because of this file
rather than in spite of it.

---

## Why this instrument and not some other

Every quantified claim in this case is computed from DGCA or gated against a
primary filing, with two exceptions, and both sit on the same question:

| Row | Status | What it carries |
|---|---|---|
| `gulf_od_share_pct` | `UNVERIFIED_NO_PRIMARY` | The 40% origin-destination share. IATA sells this data and publishes no free table |
| `gulf_hub_connect_premium_pct` | `MODELED` | What a Gulf hub earns for the connection. Nobody publishes it at all |

Between them they produce the **10.9 point connect gap**, about **8.5M passengers
a year**, worth **INR 28,900 to 56,700 crore**. That is the prize the whole
recommendation chases, and it is the softest number on the site. The risk
register names it as the most likely reason the case is wrong.

No amount of further desk research fixes this. The data exists and is sold. The
only route to a figure this project could actually stand behind is to measure
the underlying preference directly, and a choice-based conjoint is the standard
instrument for exactly that.

**What it would resolve, precisely.** Not the O-D share itself, which is an
accounting fact about journeys already flown. It resolves the question the O-D
share is being used as a proxy for: **how many of those 8.5M would switch to a
direct flight, and at what fare gap.** That is the decision-relevant quantity,
and it is the one the recommendation actually needs.

---

## The instrument

**Method.** Choice-based conjoint. Respondents see repeated pairs of itineraries
and pick one, rather than rating attributes in isolation, because trade-off
behaviour under constraint is what is being measured and stated importance
rankings are famously poor at predicting it.

**Context shown to the respondent.** A specific, recent trip they have actually
taken or firmly intend to take, India to a named European or North American city,
so the choices are anchored to a real journey rather than an imagined one.

### Attributes and levels

Levels are anchored on figures already in this repository, so the instrument
cannot drift from the analysis it is meant to inform. The Europe reference sector
is **6,731 km**; fares are built from the two verified yields, IndiGo's **5.06**
and Emirates' **9.924 INR per RPK**.

| Attribute | Levels | Why it is here |
|---|---|---|
| **Itinerary** | Nonstop; one stop via a Gulf hub; one stop via a European hub | The whole question. The European-hub level exists so "nonstop premium" is not confounded with "dislike of the Gulf specifically" |
| **Total journey time** | 9h; 13h; 16h; 19h | Nonstop Delhi to London is roughly 9h; a Gulf connection adds 4 to 10h depending on the layover |
| **Return fare, economy** | INR 34,000; 45,000; 58,000; 72,000 | Spans the range the two verified yields imply across this sector, plus headroom either side so willingness to pay is bounded rather than censored |
| **Carrier** | Indian; Gulf; European | Isolates home-carrier preference, which the case assumes exists and never tests |
| **Checked baggage** | 25 kg; 35 kg; 46 kg | Load-bearing for the diaspora segment and routinely omitted from instruments written for business travellers |
| **Departure window** | Morning; late evening | Gulf connections cluster at night; without this the time penalty absorbs a schedule effect that is not really about connecting |

**Design.** 12 choice tasks per respondent, two alternatives plus a "would not
fly either" opt-out, from a balanced-overlap design blocked into four versions.
The opt-out matters: without it the model cannot distinguish "prefers A" from
"would not have flown at these prices at all", and the case is partly about
demand that does not currently exist.

**Holdout tasks.** Two fixed tasks per respondent, excluded from estimation and
used to check that the fitted model predicts choices it has not seen. A conjoint
without holdouts reports fit, not accuracy.

---

## Sampling frame

**Population.** Adults resident in India who have flown India to Europe or North
America in the past 24 months, or hold a firm intention to in the next 12.

**Frame.** Quota sample from an online panel, stratified by departure gateway
using DGCA's own passenger counts as the weighting target, so the sample can be
post-stratified back to the traffic this project measures:

| Gateway | Why it is quota'd separately |
|---|---|
| Delhi, Mumbai | The two largest long-haul gateways |
| Kochi, Kozhikode | **The Kerala diaspora corridor.** Kochi sends more passengers to Gulf hubs than to the entire rest of the world combined. If any segment behaves differently, it is this one, and a national sample would drown it |
| Bengaluru, Hyderabad, Chennai | The southern technology and student corridors, where trip purpose skews differently again |

**Segments reported separately**, because the case's central claim is that a
specific 8.5M would switch and an average across all travellers would hide
exactly the variation that matters: visiting friends and relatives; business;
leisure; student and family accompanying.

**Size.** n ≈ 1,400 completes. Driven by the need for stable hierarchical Bayes
estimates within the four segments and seven gateway strata, not by a
margin-of-error rule of thumb, which does not apply to choice models.

---

## Analysis plan

1. **Estimation.** Hierarchical Bayes multinomial logit, individual-level
   part-worths. HB rather than aggregate logit because the quantity of interest
   is heterogeneity: the case needs to know *which* travellers switch, not the
   average traveller's preference.
2. **Willingness to pay for nonstop.** The ratio of the nonstop part-worth to the
   fare coefficient, reported in rupees and as a percentage of fare, **by
   segment**. This is the direct replacement for `gulf_hub_connect_premium_pct`,
   which is currently a modelled constant.
3. **Share-of-preference simulation.** Given a fare gap and a journey-time gap,
   what share of each segment chooses nonstop. Run across the plausible range and
   reported as a curve, never a point, which is the same discipline the sizing
   band and the value-at-stake band already follow.
4. **The number the case actually wants.** Apply the simulated switching share to
   the measured 8.5M connecting passengers. That converts the prize from "the
   size of a contested pool" into "the share of it a direct operator could take
   at a given price", which is what the recommendation has been unable to say.
5. **Sensitivity.** Re-run at ±20% on the fare levels to check the WTP estimate
   is not an artefact of the range shown, which is the most common way conjoint
   overstates.

---

## What would make the results untrustworthy, stated in advance

Written before fielding, on the same principle as the risk register: a
limitation named after the fact reads as an excuse.

- **Stated preference is not revealed preference.** Conjoint routinely overstates
  willingness to pay, commonly by 20 to 40%. Any figure from this instrument
  enters `assumptions.csv` graded no higher than **M**, and the write-up says
  the direction of the bias rather than implying precision.
- **Panel samples over-represent the online, urban and English-reading.** For
  the Kerala corridor in particular that is a real threat, and it is why the
  gateway quotas and post-stratification exist. It does not eliminate the bias.
- **Hypothetical fares are not tickets.** Nobody in the sample pays.
- **It measures preference at one moment.** Fuel, currency and capacity all move,
  and the case already shows currency alone moved unit cost more than everything
  else combined.
- **If holdout hit rate is poor, the model is reported as failed.** Not tuned
  until it fits. That would be fitting the analyst's expectations, which is the
  error this project has already had to retract once.

---

## Cost and feasibility

Roughly **INR 7 to 12 lakh** for 1,400 completes through an Indian consumer panel
with incentives, plus licence cost for conjoint design and HB estimation software,
or an open-source route through R (`ChoiceModelR`, `bayesm`) at analyst time only.
Four to six weeks from instrument sign-off to fielded results.

That is a real budget, which is the honest reason this is a design rather than a
dataset. It is also why the case is built so that **nothing depends on it**: the
recommendation stands on measured DGCA capacity, published unit costs and a
bilateral position, and this instrument would sharpen the size of the prize rather
than decide the answer.

---

## What this does and does not evidence

**Does.** Instrument design, attribute selection under a real decision, sampling
and quota logic tied to measured traffic, a specified estimation approach, and
limitations named before results exist.

**Does not.** Survey *analysis*. There are no responses. `docs/coverage.md`
continues to report that requirement as a gap, and the note there points here so
a reader can see precisely how far the work got and where it stops.
