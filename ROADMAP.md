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
  headroom. What remains genuinely open is the entitlement for the other Gulf points, and
  whether India renegotiates. Branch 4.3 of the hypothesis tree.
- ~~**Carrier share trend.**~~ Answered, and it reversed the project's premise. Indian
  carriers' share went from 37.0% in 2015 to **45.9%** in 2025 while Gulf carriers fell 32.7%
  to 26.2%. The storyline was rewritten around the finding rather than against it.
- **The Rome to Delhi dispute.** Quarantined pending a source that can settle whether DGCA
  omits the route or Eurostat over-reports it.

## Coverage gaps that will not close

`python -m src.gap_analyzer` reports 82%. Three requirements in the posting cannot be
honestly evidenced by a solo repository, and they are listed rather than papered over:
survey analysis, mentoring and coaching analysts, and first-level team management.

## Possible extensions

- **Destination-side data for the US arm.** BTS T-100 was attempted once and dropped. A
  working loader would let the India to United States corridor be reconciled from both
  ends, as India to Europe already is.
- **Cargo.** Freight moves through the pipeline already and is unused. Wide-body belly
  cargo is second-order for this decision but is real money.
- **Alternative B.** The India data centre case, scoped in `docs/alternative_b_datacenters.md`,
  revisited only if a reproducible capacity dataset appears.
