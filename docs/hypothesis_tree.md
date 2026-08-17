# Hypothesis tree

The case decomposed before any analysis ran, so the work could be sequenced by what would
most change the answer rather than by what was easiest to compute.

**Governing question:** where should Indian carriers deploy their next 100 long-haul
aircraft, and can the India-Gulf corridor absorb them?

```
Compete with the Gulf hubs, do not fly more aircraft to them
│   (opened as "deploy wide-bodies to the Gulf corridor first"; branch 5.4 reversed it)
│
├── 1. Is the Gulf corridor large enough to matter?                    ANSWERED: yes
│   ├── 1.1 How big is India-Gulf against other corridors?
│   │       36.9M vs 8.8M for all Europe. 4.2x. DGCA, 2024
│   ├── 1.2 Is it growing or mature?
│   │       Pre-covid CAGR 6.96% on total international; Gulf share stable near half
│   └── 1.3 Is the traffic point-to-point or connecting?
│           PARTIALLY ANSWERED. DGCA sector 51.2% vs IATA O-D ~40%.
│           The gap bounds the connecting share; the exact split needs O-D data
│           that no free source publishes
│
├── 2. Are Indian carriers actually losing it?                         ANSWERED: NO
│   ├── 2.1 What share do Indian carriers hold?
│   │       45.9% of India international sector pax, 2025. Everyone else 54.1%
│   ├── 2.2 Which foreign carriers, specifically?
│   │       Gulf carriers 26.2%. Emirates alone 5.57M passengers, 2024
│   └── 2.3 Is the share trend worsening or stable?
│           ANSWERED, AND IT REVERSES THE PREMISE. Neither: it is improving.
│           Indian 37.0% (2015) -> 45.9% (2025). Gulf 32.7% -> 26.2%.
│           Indian carriers are not losing, they are closing on parity
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
│   │       91M to 108M international passengers, from 72M. Three methods, band reported
│   ├── 4.2 Do the seats on order exceed that demand?
│   │       NO, AND THAT IS THE ANSWER. 140 wide-bodies on firm order carry
│   │       46,546 seats at published two-class layouts, weighted by variant.
│   │       Flown at the owned-fleet utilisation of 10.06 hours/day they add
│   │       enough for 91M, the LOW leg of the band. The order book is sized
│   │       below even the trend case, so it does not overshoot demand.
│   │       Was BLOCKED until the seat and utilisation figures were sourced
│   │       from manufacturer manuals and IndiGo's annual report
│   └── 4.3 Do bilateral seat rights permit it?
│           PARTLY ANSWERED, AND STILL THE BINDING RISK. India publishes no
│           entitlement table, so this was checked from the traffic end.
│           India-Dubai runs about 119,200 one-way seats a week against a
│           reported two-sided entitlement of 133,008, roughly 90% utilised.
│           So the single largest India-Gulf city pair has under 15% headroom
│           before a treaty change is needed, and Emirates and flyDubai are
│           reported to be at their half of it already.
│           IMPLICATION: incremental wide-body capacity aimed at Dubai cannot
│           be flown on existing rights. It has to go long-haul, or to Gulf
│           points with slack, or wait on a renegotiation India has so far
│           refused. That strengthens the deploy-long-haul recommendation.
│           No free machine-readable source for bilateral entitlements
│
└── 5. Is the Gulf a better first move than the West?         ANSWERED, AND IT REVERSED
    ├── 5.1 Relative market size?
    │       Gulf 36.9M vs Europe 8.8M vs North America 2.5M. The Gulf wins
    │       on size and that was never in doubt
    ├── 5.2 Relative competitive intensity?
    │       Europe and North America are served by mature incumbent networks;
    │       Gulf point-to-point demand is diaspora-anchored and needs no hub
    ├── 5.3 Where does the margin sit?
    │       ANSWERED, was blocked. Gulf 52% of passengers, 31% of revenue.
    │       Long-haul corridors carry higher modelled margin
    └── 5.4 Can the aircraft actually be deployed there?       THE DECIDING BRANCH
            NO, and this is what turned the answer. Three independent lines:
            (a) India-Dubai runs at 89.6% of its bilateral entitlement, leaving
                ~0.72M seats/year against a 36.9M corridor (branch 4.3)
            (b) the Gulf has the LEAST yield headroom of any corridor, and does
                not cover its own cost at IndiGo's realised yield
            (c) the order book adds 78% to international ASK where holding share
                needs ~half that, clearing only if sectors lengthen ~27%
            So the corridor is the prize and the aircraft cannot serve it. The
            8.1M connecting passengers inside it are won by flying PAST the Gulf.
            Recommendation restated: compete with the hubs, do not fly to them
```

**Branch 5 is where this tree earned its keep.** The question was posed as Gulf against West
and answered "Gulf" on size for most of the project. Adding 5.4, which asks whether the
aircraft can physically and economically be deployed rather than whether the traffic is there,
inverted it. A tree that only asks where the demand is will always answer "the biggest
corridor".

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
