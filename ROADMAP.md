# Roadmap

What is deliberately unfinished, and why. Nothing here is a placeholder.

## Cleared, and how

Everything that once sat under "blocked on source verification" is built. Recorded here
rather than deleted, because every one was unblocked by finding a primary source and none by
relaxing the gate.

- **Profit pools.** `src/profit_pools.py` exists. Passengers and reference stage lengths are
  computed; the margin axis is modelled, labelled `MODELLED` on the chart face, and anchored
  to IndiGo's FY2026 EBITDAR margin ex forex. The finding: the Gulf is 52% of India's
  international passengers and 31% of its revenue.
- **Capacity leg of the market sizing.** Runs. Seat counts came from Airbus and Boeing airport
  planning manuals at published two-class layouts, weighted by variant. The band went from
  106M to 108M on two methods to 91M to 108M on three.
- **Fuel and FX scenario levers.** Built. They did not need the gated yields after all, they
  needed a unit cost decomposition, which IndiGo publishes. The finding: currency added +0.41
  to FY2026 CASK against a net rise of +0.34, because fuel fell.

## Terminal, not pending

Three assumption rows will not close, and are marked so rather than left looking like work:

- `air_india_yield_inr_per_rpk` is `NOT_AVAILABLE`. Air India is unlisted and files nothing.
- `gulf_hub_connect_premium_pct` is `MODELED`. Nobody publishes it.
- `aircraft_utilisation_hours_per_day_active` is `NOT_AVAILABLE`. IndiGo's grounded-aircraft
  count is absent from both the FY26 annual report and the June 2026 analyst presentation.
  Searching for it did retire a bad number: the "~13 hours/day" this project used to carry
  requires 100 of 441 aircraft grounded, and the real range is about 10.5 to 11.7.

## Open questions that would change the answer

- **Bilateral seat entitlements.** Still the most likely reason the recommendation fails, but
  no longer just a named gap. India publishes no entitlement table: the Ministry of Civil
  Aviation lists its agreements and a *"Guidelines for publication/sharing of information
  pertaining to Air Services Agreement"* but no seat figures, and the agreements page returns
  403. Rajya Sabha Unstarred Question 827 of 27 July 2026 confirms the mechanism without
  publishing a number.

  So it was measured from the traffic end instead, with `benchmarking.dubai_entitlement_check`.
  India-Dubai runs about **119,200 one-way seats a week against a reported two-sided
  entitlement of 133,008, roughly 90% utilised**. Two independent routes to the same order of
  magnitude, which corroborates the secondary entitlement figure and puts a number on the
  headroom.

  **Extended 2026-08-18 to a second point, and it corrected the claim.** Abu Dhabi's
  entitlement was found (50,000 weekly seats one side, two independent secondary sources
  agreeing, a third reconciling from the traffic end) and it runs at about **58%**, not 90.
  The Gulf is not uniformly capped, and the recommendation was rewritten to say so. What
  survives is that both points' remaining entitlement absorbs only about **5% of the order
  book**, so the constraint is economic first and legal second.

  **Sharjah remains open and is the one worth chasing.** It holds the third UAE MoU and
  carries 2.3M passengers a year, and two timeboxed searches found no seat figure. The other
  eight Gulf points have none either, so the 5% is a floor on Gulf headroom rather than a
  measurement of it. Branch 4.3 of the hypothesis tree.
- ~~**Carrier share trend.**~~ Answered, and it reversed the project's premise. Indian
  carriers' share went from 37.0% in 2015 to **45.9%** in 2025 while Gulf carriers fell 32.7%
  to 26.2%. The storyline was rewritten around the finding rather than against it.
- **The Rome to Delhi dispute.** Quarantined pending a source that can settle whether DGCA
  omits the route or Eurostat over-reports it.
- **Wide-body lease rates.** The largest single unresolved input in the recommendation, and
  named as such in `docs/recommendation.md` rather than filled with a modelled figure. Whether
  to damp-lease before the first owned delivery turns entirely on the rate, and transaction
  rates are paywalled trade press (IBA, Cirium). No assumption row can clear, so the
  lease-bridge option is presented with its economics explicitly unquantified.
- **The origin-destination share.** `gulf_od_share_pct` is `UNVERIFIED_NO_PRIMARY` and cannot
  clear: IATA sells the data. It carries the eleven point connect gap that the whole
  recommendation rests on, so it is **the most likely reason the case is wrong**. It is read
  only through `allow_unverified=True` in one diagnostic, and everything downstream is a band.

## Answered since, and how the answers moved the recommendation

- ~~**Where should the wide-bodies go?**~~ The answer changed. "Reclaim the Gulf corridor
  first" became **"compete with the Gulf hubs, do not fly more aircraft to them"**, on three
  lines of evidence: the Dubai bilateral at 89.6% utilised, the Gulf holding the least yield
  headroom of any corridor, and an order book sized for a network about a quarter longer than
  the one Indian carriers fly. Recorded as pivot 1 in `docs/pivot_log.md`.
- ~~**Is the order book the right size?**~~ Answered by `src/fleet_gap.py`. It adds 78% to
  Indian carriers' international ASK where holding share needs roughly half that. Absorbed
  only if the average sector lengthens about 27% or share reaches 58%. Under bull demand it is
  nearly right-sized; under bear it is badly oversized, which the scenario selector on the
  absorption frontier shows directly.
- ~~**Do the corridor economics work?**~~ Answered by `src/options.py`, and uncomfortably. The
  Gulf has the least room of any corridor to absorb a yield decline and does not cover its own
  cost at IndiGo's realised yield. Europe can take about a fifth off the fare and still clear.

## Coverage gaps that will not close

`python -m src.gap_analyzer` reports 82%. Three requirements in the posting cannot be
honestly evidenced by a solo repository, and they are listed rather than papered over:
survey analysis, mentoring and coaching analysts, and first-level team management.

## Possible extensions

- ~~**Destination-side data for the US arm via BTS T-100.**~~ **Attempted a second time on
  2026-08-18 and dropped again.** All four `PREZIP` filename patterns 404, so BTS has
  reorganised TranStats rather than moved a file, and the `data.transportation.gov` Socrata
  catalog does not carry the series. The only remaining route is a form POST carrying
  ASP.NET viewstate. Reopen only if BTS republishes a static path or an API.

  This matters more than it used to. The risk register names the 5.6% cross-check coverage
  as the most likely reason the case is wrong, and this was the cheapest available way to
  raise it. It is now a known dead end rather than an untried idea, which is worth recording:
  the next person should not spend an afternoon rediscovering it.
- **Cargo.** Freight moves through the pipeline already and is unused. Wide-body belly
  cargo is second-order for this decision but is real money.
- **Alternative B.** The India data centre case, scoped in `docs/alternative_b_datacenters.md`,
  revisited only if a reproducible capacity dataset appears.
