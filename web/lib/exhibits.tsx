import type { ReactNode } from "react";
import { Exhibit } from "@/components/Exhibit";
import { AbsorptionFrontier, CorridorScale, YieldHeadroom } from "@/components/charts";
import {
  CarrierCapability,
  CaskBridge,
  OptionMatrix,
  PaxVsRevenue,
  ShareTrend,
  SizingBand,
} from "@/components/frameworks-charts";
import {
  CargoAsymmetry,
  DomesticShare,
  EntitlementUse,
  FleetGap,
  FuelFxSensitivity,
  GatewayFlows,
  LoadFactorSlope,
  ProfitPool,
  Scenarios,
  ValueAtStake,
  WhoCarriesIndia,
} from "@/components/restored-charts";
import {
  BlockHourReconciliation,
  CapitalScale,
  CompetitivePosition,
  CostStack,
  MarginLadder,
  UnitSpread,
} from "@/components/company-charts";
import {
  access,
  carriers,
  company,
  corridors,
  economics,
  fleet,
  market,
  story,
} from "@/lib/data";

// ONE registry, keyed by the same chart id `docs/index.html` uses.
//
// Two things this fixes at once.
//
// **Parity.** The app shipped 11 exhibits against the static site's 18, and
// nobody could tell, because the two surfaces had no shared vocabulary to
// compare. Keying on the static site's own `data-chart` ids makes the gap
// countable, and `tests/test_delivery.py` counts it on every run.
//
// **Grammar.** Every exhibit is rendered by the same component with the same
// four-tab vocabulary, so a reader learns the interaction once. The alternative,
// which is what the app had, is each page inventing its own disclosure.
//
// The Evidence tab is NOT written here. It is read out of the narrative export,
// which is parsed from `docs/index.html`, so the argument for an exhibit exists
// in exactly one place in the repo and every surface relays it. Only the two
// tabs that have no home in the prose are written here: how a number was
// computed, and what would falsify it.

const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;
const dubai = access.entitlements.find((e) => e.foreign_point === "DUBAI")!;
const abudhabi = access.entitlements.find((e) => e.foreign_point === "ABUDHABI")!;
const indigo = carriers.international_summary.find((c) => c.airline === "IndiGo")!;
const airIndia = carriers.international_summary.find((c) => c.airline === "Air India")!;
const firstYear = carriers.share_trend[0];
const lastYear = carriers.share_trend[carriers.share_trend.length - 1];
const absorption = fleet.absorption_summary;
const vas = economics.value_at_stake;
const headroom = fleet.gulf_headroom;
const band = market.triangulation.estimates
  .map((e) => e.value_m)
  .filter((v): v is number => v !== null);

const pct = (n: number, d = 1) => `${n.toFixed(d)}%`;
const sgn = (n: number, d = 1) => `${n > 0 ? "+" : ""}${n.toFixed(d)}%`;
const n0 = (n: number) => Math.round(n).toLocaleString();

const DGCA = "DGCA monthly traffic statistics, computed in-repo. See data/data_dictionary.md.";

/** The step prose for one chart id, straight from `docs/index.html`. */
function evidenceFor(id: string): ReactNode {
  const step = story.find((s) => s.chart === id);
  if (!step) return null;
  return (
    <>
      {step.paragraphs.map((p, i) => (
        <p key={i} className={p.kind === "aside" ? "border-l-2 border-light pl-4 text-grey" : ""}>
          {p.text}
        </p>
      ))}
      {step.pivot && (
        <p className="border-l-2 border-red pl-4">
          <span className="font-semibold text-red">{step.pivot.label}. </span>
          {step.pivot.text}
        </p>
      )}
    </>
  );
}

export type ExhibitSpec = {
  /** The takeaway, never the topic, and computed from the export wherever a
   *  number appears in it. A title typed by hand goes stale silently. */
  title: string;
  source: string;
  chart: ReactNode;
  /** Only for exhibits with no counterpart step in docs/index.html. Everything
   *  that has one reads its argument from the narrative export instead. */
  evidence?: ReactNode;
  computed?: ReactNode;
  breaks?: ReactNode;
};

export const EXHIBITS: Record<string, ExhibitSpec> = {
  domestic_share: {
    title: `IndiGo owns ${pct(carriers.domestic_summary[0].share_pct, 0)} of the domestic market that has to fund the wide-bodies`,
    source: `Share of scheduled domestic passengers, ${lastYear.year}. ${DGCA}`,
    chart: <DomesticShare />,
    computed: (
      <p>
        <code>benchmarking.carrier_operating_summary()</code>, which returns the DOMESTIC table
        unless told otherwise. That default caused a published error once: an international
        exhibit plotted a 943 km domestic stage length. Here domestic is what is wanted, and it
        is named rather than defaulted.
      </p>
    ),
  },

  corridor_scale: {
    title: `Half of India's international traffic touches the Gulf, ${(gulf.pax_total / europe.pax_total).toFixed(1)}x the entire direct Europe market`,
    source: `DGCA Table 3, international country-pair passengers, both directions, ${lastYear.year}. Computed in src/benchmarking.py.`,
    chart: <CorridorScale />,
    computed: (
      <p>
        Country-pair passengers bucketed to corridors through{" "}
        <code>is_gulf_point()</code>, never by membership of a literal list. DGCA writes{" "}
        <code>ABUDHABI</code> and <code>RAS AL-KHAIMAH</code>, and exact matching against a
        tidier list once filed 5.0M passengers a year, a fifth of the Gulf flow, under
        &ldquo;everywhere else&rdquo;.
      </p>
    ),
    breaks: (
      <p>
        Nothing about this number is in dispute, and that is the point: the scale is real. What
        it cannot tell you is where those passengers were going, which is the next exhibit and
        the one the recommendation actually turns on.
      </p>
    ),
  },

  gateway_flows: {
    title: "India's own statistics lose sight of the passenger at the Gulf hub, and that blind spot is the case",
    source: `Passengers from India's six largest international gateways, ${lastYear.year}. DGCA records the first foreign point only. Computed in src/benchmarking.py.`,
    chart: <GatewayFlows />,
    computed: (
      <p>
        <code>benchmarking.gateway_flows()</code>, splitting each gateway&rsquo;s traffic into
        Gulf points and everything else. No modelling: it is a bucketing of the country-pair
        table, and the flows sum to the corridor totals in the exhibit above.
      </p>
    ),
    breaks: (
      <p>
        The diagram shows where the record stops, not where the passenger goes. How many of
        those Gulf-hub passengers continue elsewhere is the one number this project cannot
        verify, because IATA sells origin-destination data. It is gated{" "}
        <span className="text-red">UNVERIFIED_NO_PRIMARY</span> and read in exactly two places.
      </p>
    ),
  },

  value_at_stake: {
    title: `The passengers India cannot see carry INR ${n0(vas.revenue_floor_inr_cr)} to ${n0(vas.revenue_ceiling_inr_cr)} crore, a third to two thirds of IndiGo's revenue`,
    source:
      "Connecting passengers priced over a reference journey at the only two yields this project has verified, IndiGo's and Emirates'. Computed in src/options.py. Modelled.",
    chart: <ValueAtStake />,
    computed: (
      <p>
        <code>options.value_at_stake()</code>. The {vas.gap_pts.toFixed(1)} point gap between
        DGCA&rsquo;s {pct(vas.sector_share_pct)} sector share and a roughly{" "}
        {pct(vas.od_share_pct, 0)} origin-destination share, times total traffic, priced across
        a {n0(vas.reference_stage_km)} km reference journey. Reported as a band because the
        floor and ceiling are two different carriers&rsquo; realised yields.
      </p>
    ),
    breaks: (
      <p>
        <strong>This is the likeliest reason the case is wrong.</strong> The whole figure rests
        on <code>gulf_od_share_pct</code>, which carries{" "}
        <span className="text-red">UNVERIFIED_NO_PRIMARY</span> and can never clear: IATA sells
        that data and publishes no free table. If the true connecting share is materially
        smaller than eleven points, the contested pool shrinks with it.
      </p>
    ),
  },

  who_carries_india: {
    title: `Indian carriers fly ${pct(lastYear.Indian)} of India's own international passengers, still short of half`,
    source: `Share of India international sector passengers by carrier home region, ${lastYear.year}. ${DGCA}`,
    chart: <WhoCarriesIndia />,
    computed: (
      <p>
        <code>benchmarking.who_carries_india()</code>. Carrier names are matched through a
        normaliser rather than exactly: DGCA&rsquo;s own file contains{" "}
        <code>QATAR AIRWATYS</code>, and a <code>GRAND TOTAL</code> row worth 17.53M passengers
        was once counted as a foreign airline.
      </p>
    ),
  },

  carrier_share_trend: {
    title: `The premise reverses: Indian carriers went ${pct(firstYear.Indian)} to ${pct(lastYear.Indian)} while Gulf carriers fell ${pct(firstYear.Gulf)} to ${pct(lastYear.Gulf)}`,
    source: `DGCA international carrier-wise, ${firstYear.year} to ${lastYear.year}. 2020 and 2021 excluded as covid distortion. Computed in src/benchmarking.py.`,
    chart: <ShareTrend />,
    computed: (
      <p>
        Two years are dropped and the reason is stated rather than the gap left unexplained:
        repatriation and air-bubble flying put Indian carriers above 50% in 2020 and 2021 on a
        fifth of the usual traffic, which is a lockdown artefact and not a trend.
      </p>
    ),
    breaks: (
      <p>
        If the trend is read as &ldquo;the problem solves itself&rdquo;, the case collapses into
        doing nothing. It does not: the share taken back is short-haul, flyable with aircraft
        India already has. Watch the split by corridor, not the headline.
      </p>
    ),
  },

  stage_length_gap: {
    title: `IndiGo carries more international passengers than Air India over ${(airIndia.stage_length_km / indigo.stage_length_km).toFixed(1)}x shorter sectors`,
    source: `Average international stage length and load factor, ${lastYear.year}. Bubble area is available seat kilometres. ${DGCA}`,
    chart: <CarrierCapability />,
    computed: (
      <p>
        International table, named explicitly. <code>carrier_operating_summary()</code> returns
        domestic by default, and reading that default here would show 943 km instead of{" "}
        {n0(indigo.stage_length_km)} km and reverse what the exhibit claims.
      </p>
    ),
  },

  pax_vs_revenue_share: {
    title: `The Gulf is ${pct(gulf.pax_share_pct!, 0)} of passengers and ${pct(gulf.revenue_share_pct!, 0)} of revenue, the widest gap of any corridor`,
    source:
      "Passenger counts, great circle distances and one published yield. Computed in src/profit_pools.py.",
    chart: <PaxVsRevenue />,
    computed: (
      <p>
        <strong>No margin assumption enters this exhibit at all.</strong> It is passengers times
        distance times IndiGo&rsquo;s published yield per RPK. It exists so the point survives a
        reader who rejects the modelled margin in the exhibit that follows.
      </p>
    ),
  },

  profit_pool: {
    title: `Volume sits in the Gulf and margin sits in long-haul, a ${(gulf.pax_share_pct! - gulf.revenue_share_pct!).toFixed(0)} point gap the wide-bodies exist to close`,
    source:
      "Width is a revenue proxy, height is a modelled margin anchored on IndiGo's FY2026 EBITDAR margin excluding forex of 27.3%, against 17.8% as reported. Computed in src/profit_pools.py. Modelled.",
    chart: <ProfitPool />,
    computed: (
      <p>
        Margin is spread across stage length by <code>MARGIN_STAGE_SENSITIVITY</code>, a module
        constant with a <code>sensitivity()</code> beside it, and anchored so the
        revenue-weighted mean equals the ex-forex figure. Both FY2026 margins are stated: 27.3%
        excluding forex, 17.8% as reported. Publishing either alone is the error this project
        has already made once, in the opposite direction.
      </p>
    ),
    breaks: (
      <p>
        The margin axis is the most heavily modelled thing in the repo, because no Indian
        carrier publishes margin by corridor. Reject it and the exhibit before this one carries
        the same point with no margin assumption at all. That redundancy is deliberate.
      </p>
    ),
  },

  yield_headroom: {
    title: `Gulf sectors clear at ${sgn(gulf.yield_headroom_pct!)} yield headroom, the least of any corridor, against Europe at ${sgn(europe.yield_headroom_pct!)}`,
    source:
      "IndiGo published unit cost scaled by stage length. CASK_STAGE_ELASTICITY = -0.25, a labelled modelled knob with a sensitivity beside it. Computed in src/options.py.",
    chart: <YieldHeadroom />,
    computed: (
      <p>
        Headroom, not breakeven against a flat yield. Yield per RPK falls with stage length, so
        holding it constant across an 11,766 km sector flatters long-haul. Reporting the
        tolerance instead leaves the unknown on the reader&rsquo;s side of the line. There is no
        net present value anywhere in this project for the same reason.
      </p>
    ),
    breaks: (
      <p>
        The result moves with the load factor chosen. At the international 81.1% the Gulf sits
        about four points under cost; at IndiGo&rsquo;s system 84.8% it comes out near
        breakeven. The ordering across corridors does not change either way, and the ordering is
        what the recommendation uses.
      </p>
    ),
  },

  cargo_asymmetry: {
    title: "Belly freight does not follow stage length, so it does not argue for long-haul on its own",
    source: `Belly freight per passenger by corridor, ${lastYear.year}, physical units only. Computed in src/cargo.py.`,
    chart: <CargoAsymmetry />,
    computed: (
      <p>
        Physical units and no revenue leg, because no Indian carrier publishes a freight yield.
        The correlation between sector length and freight per passenger is -0.10, which is
        nothing, so this is presented as a caveat against an easy argument rather than as
        support for one.
      </p>
    ),
  },

  market_sizing: {
    title: `Three independent methods put 2030 between ${Math.round(Math.min(...band))}M and ${Math.round(Math.max(...band))}M, and capacity is the binding leg`,
    source:
      "Trend extrapolation, an income-elasticity fit across twelve peer countries, and a capacity count from published order books. Computed in src/market_sizing.py.",
    chart: <SizingBand />,
    computed: (
      <p>
        Reported as a band and never averaged: the spread is the useful output. The capacity leg
        was withheld for most of this project&rsquo;s life because its seat and utilisation
        inputs had not cleared the gate. Unblocking it widened the band <em>downward</em>.
      </p>
    ),
  },

  scenarios: {
    title: "Every demand path, including the pessimistic one, needs materially more long-haul capacity than exists today",
    source:
      "Three growth paths anchored on rates India has actually recorded, capped at 12% where the constraint stops being demand. Computed in src/scenario.py.",
    chart: <Scenarios />,
    computed: (
      <p>
        The bear case is the slowest sustained three-year stretch in the clean data, not a round
        number chosen for symmetry. The bull case is capped because beyond 12% the binding
        constraint becomes how fast aircraft, crew and slots arrive, which is a different model.
      </p>
    ),
  },

  absorption_frontier: {
    title: `The order book is ${absorption.book_vs_growth_ratio.toFixed(2)}x the growth needed to hold share, and clears only at ${Math.round(absorption.stage_uplift_pct)}% longer sectors or ${Math.round(absorption.share_pct_to_absorb)}% of the market`,
    source:
      "Firm wide-body order book converted to ASK at block speed and seats per departure computed from DGCA. Computed in src/fleet_gap.py.",
    chart: <AbsorptionFrontier />,
    computed: (
      <p>
        Capacity in ASK, not seats: a seat is not capacity until you say how far and how often it
        flies, and this case turns on how far. Block speed is computed from DGCA&rsquo;s own
        aircraft-kilometre and aircraft-hour columns rather than assumed.
      </p>
    ),
    breaks: (
      <p>
        The book is treated as net additional capacity, which overstates it: some aircraft
        replace retirements already inside the baseline. No public retirement schedule exists for
        either carrier, so the overstatement cannot be sized, and the absorption requirement is
        therefore a floor rather than a ceiling.
      </p>
    ),
  },

  fleet_gap: {
    title: "Timing changes when the shortfall lands, not whether the order book is enough",
    source:
      "Capacity needed against capacity available on three delivery-start assumptions. No primary source states a delivery schedule. Computed in src/fleet_gap.py.",
    chart: <FleetGap />,
    computed: (
      <p>
        No start year is asserted anywhere. The Airbus release confirming the sixty firm A350s
        states no schedule, so three plausible starts are run and the spread is the output rather
        than a single line implying knowledge nobody has.
      </p>
    ),
  },

  cask_bridge: {
    title: "The rupee added more to unit cost than the entire net rise, so the cost problem is a currency problem",
    source:
      "IndiGo FY2025 to FY2026 CASK bridge from the published results release. Computed in src/scenario.py.",
    chart: <CaskBridge />,
    computed: (
      <p>
        4.66 to 5.00, bridged: fuel -0.18, genuine non-fuel inflation +0.11, currency +0.41.
        Currency alone exceeds the net +0.34. Use CASK ex-fuel ex-forex of 3.00 rather than 3.52
        whenever an FX lever runs, or the forex effect is counted twice.
      </p>
    ),
    breaks: (
      <p>
        This exhibit exists because an earlier version of this page claimed IndiGo&rsquo;s
        operating margin had halved. It had not; the claim came from a convention the company
        does not publish and was withdrawn. The pressure is real, and it sits in unit cost.
      </p>
    ),
  },

  fuel_fx_sensitivity: {
    title: "Between a tenth and two fifths of unit cost moves with the rupee, and every line starts above breakeven",
    source:
      "Fuel and currency shocks against FY2026 unit economics. India publishes no domestic and international fuel split, so exposure is a band. Computed in src/scenario.py.",
    chart: <FuelFxSensitivity />,
    computed: (
      <p>
        The exposure is reported as a floor and a ceiling because the share of fuel bought at the
        dollar international price rather than the rupee domestic one is not published. The
        interactive version of this exhibit is on the dashboard, where a control indexes a
        precomputed cube.
      </p>
    ),
  },

  load_factor_slope: {
    // Computed, and it argues against the obvious reading. Two of the four
    // majors sit BELOW their 2019 load factor, so "recovered past pre-pandemic"
    // is not what this data says, and the title must not repeat it.
    title: `Every major carrier flies above 80% full, but the two largest sit below their ${carriers.load_factor_slope[0]?.start_year ?? 2019} load factor, not above it`,
    source: `Scheduled domestic passenger load factor, ${carriers.load_factor_slope[0]?.start_year ?? 2019} against ${carriers.load_factor_slope[0]?.end_year ?? lastYear.year}. ${DGCA}`,
    chart: <LoadFactorSlope />,
    computed: (
      <p>
        Two points per carrier, four carriers, from{" "}
        <code>app_export.load_factor_slope()</code>, which uses the same window and the same four
        names as the static site&rsquo;s version.
      </p>
    ),
    breaks: (
      <p>
        The conclusion the exhibit supports is narrow: the aircraft that exist are full, so
        demand is not the constraint. It does <em>not</em> support the stronger claim that load
        factors have recovered past their pre-pandemic level, which this data contradicts for
        IndiGo and SpiceJet.
      </p>
    ),
  },

  // --------------------------------------------------------------------------
  // The client's own numbers. New with /company: the analysis was always
  // IndiGo-anchored and no surface showed the airline's own P&L.
  // --------------------------------------------------------------------------

  unit_spread: {
    title: `IndiGo did not cover its unit cost in ${company.spread.year}: RASK ${company.spread.rask.toFixed(2)} against CASK ${company.spread.cask.toFixed(2)}`,
    source:
      "IndiGo Q4 and FY2026 results release, unit cost and unit revenue tables. Both rows verified in data/manual/assumptions.csv. Computed in src/financials.py.",
    chart: <UnitSpread />,
    evidence: (
      <>
        <p>
          The spread is {Math.abs(company.spread.spread).toFixed(2)} INR per available seat
          kilometre, which is {Math.abs(company.spread.spread_pct_of_rask).toFixed(1)}% of unit
          revenue. Small, and on the wrong side of zero. This is the balance sheet the wide-bodies
          are being bought onto, and it appeared on no surface of this project until now.
        </p>
        <p>
          Read it beside the currency line rather than alone. The rupee added{" "}
          {company.spread.currency_contribution.toFixed(2)} to unit cost in the same year, roughly{" "}
          {Math.round(company.spread.currency_vs_gap)} times the gap, so the inversion is a
          treasury outcome on dollar-denominated lease liabilities rather than an operating
          collapse.
        </p>
      </>
    ),
    computed: (
      <p>
        <code>financials.unit_spread()</code>, from two gated rows. The cost-side equivalence, the
        sector length at which IndiGo&rsquo;s own cost curve reaches today&rsquo;s unit revenue, is{" "}
        {n0(company.spread.stage_km_to_close)} km against a reference network of{" "}
        {n0(company.spread.reference_stage_km)} km. That figure is reported because it is small,
        not because it is a plan: unit revenue falls with stage length too, and this project
        refuses to compare corridor economics against a flat yield for exactly that reason.
      </p>
    ),
    breaks: (
      <p>
        It is one paisa. A single year of ordinary cost control, or a rupee that stops
        depreciating, closes it, and then the sharpest line on this page stops being true. The
        durable claim is not that IndiGo loses money on every seat kilometre; it is that there is
        no margin cushion under a commitment this size.
      </p>
    ),
  },

  margin_ladder: {
    title: `Both FY2026 margins are true and they tell opposite stories: ${company.margin_ladder.find((r) => r.year === "FY2026" && r.basis === "As reported")!.margin_pct.toFixed(1)}% reported against ${company.margin_ladder.find((r) => r.year === "FY2026" && r.basis === "Excluding forex")!.margin_pct.toFixed(1)}% excluding forex`,
    source:
      "InterGlobe Aviation Annual Report FY26 financial highlights, and the FY2026 results release. Computed in src/financials.py.",
    chart: <MarginLadder />,
    evidence: (
      <>
        <p>
          As reported, EBITDAR margin fell from 26.3% to 17.8%, a drop of 8.5 points. Excluding
          forex on dollar lease liabilities it rose, 26.3% to 27.3%. The gap between the two is
          about nine and a half points of revenue and it is entirely non-operating.
        </p>
        <p>
          Both are published here because publishing either alone is an error this project has
          already committed once. An earlier version of the site claimed the operating margin had
          halved, from a convention the company does not publish; that claim was withdrawn and the
          retraction is still in the methodology. Quoting only the flattering ex-forex figure would
          be the same mistake pointing the other way.
        </p>
      </>
    ),
    computed: (
      <p>
        <code>financials.margin_ladder()</code> returns four rows, both bases across both years, so
        neither figure can be read out of the module without the other. A test asserts it.
      </p>
    ),
  },

  cost_stack: {
    title: "Strip fuel and currency and genuine non-fuel inflation was 0.11 per ASK, against a 0.52 rise",
    source:
      "IndiGo FY2025 and FY2026 unit cost comparatives, four verified rows. Computed in src/financials.py.",
    chart: <CostStack />,
    evidence: (
      <p>
        Three bases, because the middle one is where the year hides. All-in unit cost rose 0.34.
        Ex-fuel it rose 0.52, which looks worse. Ex-fuel and ex-forex it rose 0.11, which is what
        the airline actually did to its own cost base. The 0.41 in between is the rupee.
      </p>
    ),
    computed: (
      <p>
        Two different quantities in this project both equal 3.00: FY2025 CASK ex-fuel, and FY2026
        CASK ex-fuel ex-forex. Confusing them collapses the bridge, which is why the exhibit names
        the basis on every bar rather than relying on the reader to track it.
      </p>
    ),
  },

  capital_scale: {
    title: `The client's own sixty aircraft would produce revenue equal to ${company.capital_scale.pct_of_fy2026_revenue.toFixed(0)}% of the entire FY2026 top line`,
    source:
      "60 A350-900s at the verified two-class seat count, flown at computed block speed and the owned-fleet utilisation basis, valued at FY2026 realised RASK. Computed in src/financials.py.",
    chart: <CapitalScale />,
    evidence: (
      <p>
        The commitment is roughly a year of earnings expressed as annual revenue potential, which
        is the honest order of magnitude for a decision of this size. It is scale, not a financing
        plan: how the aircraft are funded changes who owns the metal, not where it should fly.
      </p>
    ),
    computed: (
      <p>
        <strong>No aircraft price appears anywhere in this exhibit</strong>, and a test fails if
        one ever does. A list price is not a transaction price and transaction prices are
        commercially confidential, so scale is expressed in capacity and in revenue at realised
        unit revenue instead. The seat count is read off the same gated order-book table the
        capacity sizing leg uses, so the two cannot diverge.
      </p>
    ),
    breaks: (
      <p>
        The utilisation basis is the owned fleet,{" "}
        {company.capital_scale.utilisation_hours_per_day.toFixed(2)} hours a day. An active-fleet
        basis would be higher and would raise this figure by roughly a third. The conservative
        basis is used and named, because the widely quoted 13 hours a day does not survive
        arithmetic: it requires 100 of 441 aircraft grounded.
      </p>
    ),
  },

  competitive_position: {
    title: `Emirates earns ${company.competitive_position.find((c) => c.carrier === "Emirates")!.yield_vs_indigo!.toFixed(2)}x IndiGo's yield per passenger kilometre on the journeys they both want`,
    source:
      "IndiGo FY2026 yield and Emirates Group 2025-26 published passenger yield, converted at the FBIL reference rate. Both verified. Computed in src/financials.py.",
    chart: <CompetitivePosition />,
    evidence: (
      <p>
        These are the only two yields this project has verified against a primary source, and they
        are what the contested-pool band is built from: the floor prices the leaked traffic at
        IndiGo&rsquo;s own realisation, the ceiling at Emirates&rsquo;.
      </p>
    ),
    computed: (
      <p>
        Emirates publishes passenger yield directly, at 38.1 fils per revenue passenger kilometre,
        converted at a dated reference rate. IndiGo&rsquo;s is from its own results release. No
        proxy, no blend.
      </p>
    ),
    breaks: (
      <p>
        The gap bounds the prize; it does not measure a connect premium. Emirates carries
        substantial premium cabins where IndiGo is all-economy, and yield per kilometre normally
        falls with stage length, so some of the difference is cabin mix and network shape rather
        than pricing power. Air India, the third carrier that matters here, publishes nothing.
      </p>
    ),
  },

  operations: {
    title: `DGCA and IndiGo's own block hours differ by ${Math.abs(company.operations.dgca_all_services_hours - company.operations.published_block_hours).toFixed(1)} hours in ${n0(company.operations.published_block_hours)} once the same services are compared`,
    source:
      "IndiGo Annual Report FY26 operational highlights against DGCA aircraft-hours, financial year basis. Computed in src/financials.py.",
    chart: <BlockHourReconciliation />,
    evidence: (
      <p>
        The second both-ends cross-check in this project, after DGCA against Eurostat. It matters
        because the utilisation figure it underwrites is what converts an order book into capacity,
        and capacity is what the whole absorption argument runs on.
      </p>
    ),
    computed: (
      <p>
        Run on the financial year, April to March, not the calendar year, because DGCA publishes
        monthly and IndiGo reports to March. Comparing two different twelve-month windows would
        have produced a spurious gap.
      </p>
    ),
    breaks: (
      <p>
        The published headline is {company.operations.reconciliation_pct.toFixed(2)}%, on scheduled
        services alone. That residual turned out not to be measurement error but non-scheduled
        international flying sitting outside the filter. Both bases are reported rather than the
        flattering one alone.
      </p>
    ),
  },

  // Two exhibits with no counterpart on the static site. They are additions, and
  // they are listed here so the parity count is honest in both directions.
  option_menu: {
    title:
      "Only one option is both available this decade and value-creating, and it is not the one that follows the traffic",
    source:
      "Option menu parsed from docs/recommendation.md rather than retyped. Axes are ordinal scales over the table's own wording.",
    chart: <OptionMatrix />,
    computed: (
      <p>
        The placements can be checked against the source table cell by cell, which is why the
        ordinal mapping is stated rather than hidden. Two options land on the same cell, because
        owning wide-bodies for long-haul and for the Gulf differ by corridor rather than by
        capital or timing, and coincident points are spread by a fixed offset so neither
        disappears.
      </p>
    ),
    breaks: (
      <p>
        The damp-lease bridge sits at low capital and immediate availability and its economics
        are <strong>explicitly unquantified</strong>, because wide-body transaction lease rates
        are paywalled trade press. It is the largest named unresolved input in the project.
      </p>
    ),
  },

  entitlement_use: {
    title: `India-Dubai is at ${pct(dubai.utilisation_pct)} of its entitlement and Abu Dhabi at ${pct(abudhabi.utilisation_pct)}, together absorbing about ${Math.round(headroom.pct_of_order_book_absorbed)}% of the order book`,
    source:
      "Implied seats from DGCA passenger counts at the international load factor, against entitlements reported in secondary sources. Computed in src/benchmarking.py.",
    chart: <EntitlementUse />,
    computed: (
      <p>
        Seats implied from traffic, not from a schedule: India publishes no bilateral entitlement
        table at all. Never quote 66,504 seats a week as the India-UAE cap. That is one emirate
        and one side; India-UAE runs roughly 255,000 one-way seats a week across three separate
        agreements.
      </p>
    ),
    breaks: (
      <p>
        Both entitlement figures carry{" "}
        <span className="text-red">UNVERIFIED_NO_PRIMARY</span>. They are corroborated from the
        traffic end and from a second secondary source, and they are load-bearing for the
        recommendation, which makes them the weakest link in it. Abu Dhabi at{" "}
        {pct(abudhabi.utilisation_pct)} is why the case does not claim the Gulf is uniformly
        capped.
      </p>
    ),
  },
};

/** Render one registry entry. Pages name an id; they never rebuild the grammar. */
export function RegisteredExhibit({
  id,
  chart,
  className,
}: {
  id: keyof typeof EXHIBITS;
  /** Override for exhibits whose chart lives on an interactive page. */
  chart?: ReactNode;
  className?: string;
}) {
  const spec = EXHIBITS[id];
  const body = chart ?? spec.chart;
  if (!body) return null;
  return (
    <Exhibit
      anchor={`exhibit-${id}`}
      title={spec.title}
      source={spec.source}
      evidence={spec.evidence ?? evidenceFor(id)}
      computed={spec.computed}
      breaks={spec.breaks}
      className={className}
    >
      {body}
    </Exhibit>
  );
}

/** Ids with a chart, in the order the argument runs. Used by /story and the deck
 *  so neither keeps its own list. */
export const EXHIBIT_ORDER = story
  .map((s) => s.chart)
  .filter((id) => EXHIBITS[id]?.chart)
  .concat(["option_menu"]);
