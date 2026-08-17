# Roadmap

What is deliberately unfinished, and why. Nothing here is a placeholder.

## Blocked on source verification

The revenue half of the case is gated by `dp.assumption()`, which refuses any figure not
marked `VERIFIED` in `data/manual/assumptions.csv`. Unblocking all three needs the same
handful of numbers checked against primary filings.

- **Profit pools.** Chart builder exists in `src/charts.py`; the module does not. The margin
  anchor is now real and primary-sourced: IndiGo EBITDAR margin **26.3% (FY2025) and 27.3%
  (FY2026, ex-forex)**. An earlier claim that the margin halved to 14.0% was wrong and is
  retracted in `docs/methodology.md`. What still blocks the module is the segment split, not
  the total margin.
- **Capacity leg of the market sizing.** Currently withheld, and the chart says so. Needs
  wide-body order counts, seat configurations and utilisation.
- **Fuel and FX scenario levers.** The demand lever is built and unblocked. Fuel needs ATF
  price, which Indian Oil publishes only through a JavaScript page, and FX needs the RBI
  reference rate. Both are absent rather than stubbed.

## Open questions that would change the answer

- **Bilateral seat entitlements.** India-Gulf capacity is negotiated, not open. This is the
  most likely reason the recommendation fails, and no free machine-readable source exists.
  Branch 4.3 of the hypothesis tree.
- **Carrier share trend.** Whether Indian carriers' 45.3% share is stable or eroding. The
  data to compute it is already in the pipeline; the series has not been built.
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
