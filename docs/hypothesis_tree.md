# Hypothesis tree

The case decomposed before any analysis ran, so the work could be sequenced by what would
most change the answer rather than by what was easiest to compute.

**Governing question:** where should Indian carriers deploy their next 100 long-haul
aircraft, and can the India-Gulf corridor absorb them?

```
Deploy wide-bodies to the Gulf corridor first
│
├── 1. Is the Gulf corridor large enough to matter?                    ANSWERED: yes
│   ├── 1.1 How big is India-Gulf against other corridors?
│   │       36.9M vs 8.8M for all Europe. 4.2x. DGCA, 2024
│   ├── 1.2 Is it growing or mature?
│   │       Pre-covid CAGR 7.18% on total international; Gulf share stable near half
│   └── 1.3 Is the traffic point-to-point or connecting?
│           PARTIALLY ANSWERED. DGCA sector 51.2% vs IATA O-D ~40%.
│           The gap bounds the connecting share; the exact split needs O-D data
│           that no free source publishes
│
├── 2. Are Indian carriers actually losing it?                         ANSWERED: yes
│   ├── 2.1 What share do Indian carriers hold?
│   │       45.3% of India international sector pax. Foreign carriers 54.7%
│   ├── 2.2 Which foreign carriers, specifically?
│   │       Gulf carriers 25.5%. Emirates alone 5.57M passengers, 2024
│   └── 2.3 Is the share trend worsening or stable?
│           OPEN. Needs a share time series, computable from existing data
│
├── 3. Is equipment the binding constraint?                            ANSWERED: yes
│   ├── 3.1 Do Indian carriers fly short-haul internationally?
│   │       IndiGo average stage 2,643 km vs Air India 5,316 km, 2025
│   ├── 3.2 Is that a network choice or a fleet limit?
│   │       Fleet. IndiGo's international fleet is narrow-body; the A350 order
│   │       is the first equipment capable of the missing distance
│   └── 3.3 Could the gap close without wide-bodies?
│           NO for Europe and North America. Narrow-bodies cannot fly it.
│           This is why the equipment constraint is binding rather than incidental
│
├── 4. Can the corridor absorb 100 more aircraft?                      PARTIALLY ANSWERED
│   ├── 4.1 Does demand grow enough by 2030?
│   │       106M to 109M international passengers, from 72M. Two methods, band reported
│   ├── 4.2 Do the seats on order exceed that demand?
│   │       BLOCKED. Fleet and utilisation figures unverified; the capacity
│   │       method refuses to run rather than guess
│   └── 4.3 Do bilateral seat rights permit it?
│           OPEN, AND MATERIAL. India-Gulf capacity is negotiated, not open.
│           A fleet that cannot be flown for want of rights is deployed wrongly.
│           No free machine-readable source for bilateral entitlements
│
└── 5. Is the Gulf a better first move than the West?                  ANSWERED: yes
    ├── 5.1 Relative market size?
    │       Gulf 36.9M vs Europe 8.8M vs North America 2.5M
    ├── 5.2 Relative competitive intensity?
    │       Europe and North America are served by mature incumbent networks;
    │       Gulf point-to-point demand is diaspora-anchored and needs no hub
    └── 5.3 Where does the margin sit?
            BLOCKED. Profit pools need yields. DGCA publishes no fares and
            Air India is unlisted. Gated until figures are verified
```

## What the tree says about sequencing

Branches 1, 2, 3 and 5 are answered from free public data and together carry the
recommendation. Branch 4 is where the case is genuinely incomplete, and both of its open
questions matter more than anything left in the answered branches:

- **4.3, bilateral rights**, is the single most likely reason the recommendation fails. It
  is a policy constraint, not a market one, and no amount of traffic data touches it.
- **4.2 and 5.3** are blocked on the same root cause: numbers that exist but are not
  published free. The code refuses them rather than estimating, so the gap is visible
  instead of buried in an assumption.

## Branches deliberately not opened

- **Aircraft financing and lease economics.** Real, and out of scope for a market entry
  question. It changes whether a carrier can buy the aircraft, not where to fly them.
- **Airport slot constraints at Indian gateways.** Material at Delhi and Mumbai, but a
  capacity question rather than a corridor choice.
- **Cargo.** DGCA publishes freight alongside passengers and it is loaded into the pipeline,
  but wide-body belly cargo is a second-order effect on this decision and analysing it would
  have been scope for its own sake.
