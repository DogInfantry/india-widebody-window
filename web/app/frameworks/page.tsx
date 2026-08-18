import type { Metadata } from "next";
import { Exhibit } from "@/components/Exhibit";
import {
  CarrierCapability,
  CaskBridge,
  OptionMatrix,
  PaxVsRevenue,
  ShareTrend,
  SizingBand,
} from "@/components/frameworks-charts";
import { CorridorScale } from "@/components/charts";
import { access, carriers, corridors, economics, fleet, market, narrative } from "@/lib/data";

export const metadata: Metadata = { title: "How the answer was reached" };

// Five frameworks, in a chain rather than a gallery.
//
// The rule this page is built on: no framework appears without the question it
// answers, and each answer is what forces the next one. A framework that could
// be deleted without breaking the argument does not belong here, which is why
// there is no BCG matrix, no SWOT and no PESTEL wheel. The three PESTEL forces
// that are actually live appear inside the external section as evidence rather
// than as a diagram with twenty empty cells.
//
// Framework definitions are cited to DogInfantry/claude-skill-management-consultant-B1,
// not rewritten. That is an existing working agreement in CLAUDE.md.

const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;
const dubai = access.entitlements.find((e) => e.foreign_point === "DUBAI")!;
const abudhabi = access.entitlements.find((e) => e.foreign_point === "ABUDHABI")!;
const indigo = carriers.international_summary.find((c) => c.airline === "IndiGo")!;
const airIndia = carriers.international_summary.find((c) => c.airline === "Air India")!;
const firstYear = carriers.share_trend[0];
const lastYear = carriers.share_trend[carriers.share_trend.length - 1];
const vas = economics.value_at_stake;
// Computed, not typed. This read "+78% ASK committed" as a string literal for
// one commit, which is exactly the drift the rest of the project forbids.
const bookUplift = (100 * fleet.order_book.ask) / fleet.baseline.ask;

const pct = (n: number, d = 1) => `${n.toFixed(d)}%`;
const signed = (n: number, d = 1) => `${n > 0 ? "+" : ""}${n.toFixed(d)}%`;

/** Porter, adapted. Every force carries a computed number rather than an
 *  adjective, which is the only thing that makes a five-forces exhibit worth
 *  drawing: otherwise it is five opinions in boxes. */
const FORCES = [
  {
    force: "Barriers to entry",
    verdict: "Binding",
    evidence: `India-Dubai runs at ${pct(dubai.utilisation_pct)} of its reported entitlement, Abu Dhabi at ${pct(abudhabi.utilisation_pct)}. Together they leave room for about 4% of the order book.`,
  },
  {
    force: "Substitutes",
    verdict: "Strong",
    evidence: `The Gulf hub connection is the substitute for a direct flight, and ${vas.connecting_pax_m.toFixed(1)}M passengers a year choose it.`,
  },
  {
    force: "Rivalry",
    verdict: "Shifting",
    evidence: `Indian carriers went ${pct(firstYear.Indian)} to ${pct(lastYear.Indian)} of international sectors since ${firstYear.year} while Gulf carriers fell ${pct(firstYear.Gulf)} to ${pct(lastYear.Gulf)}.`,
  },
  {
    force: "Supplier power",
    verdict: "High, unpriced",
    evidence:
      "Wide-body lease rates are set by a handful of lessors and published only through paywalled trade press, so the bridge option cannot be costed here and says so.",
  },
  {
    force: "Buyer power",
    verdict: "High",
    evidence: `India long-haul is a price-led, diaspora-weighted market. It shows up as yield: the Gulf clears at ${signed(gulf.yield_headroom_pct!)} headroom against Europe at ${signed(europe.yield_headroom_pct!)}.`,
  },
];

/** The value chain, with the computed metric that governs each stage. */
const VALUE_CHAIN = [
  { stage: "Fleet", metric: `+${bookUplift.toFixed(0)}% ASK committed`, note: "order book against today's international capacity" },
  { stage: "Network", metric: `${Math.round(indigo.stage_length_km).toLocaleString()} km`, note: "IndiGo international stage length, against Air India's 2x" },
  { stage: "Crew and MRO", metric: "Not published", note: "type-rated pilot numbers are unavailable; carried as a risk" },
  { stage: "Distribution", metric: `${pct(lastYear.Indian)}`, note: "Indian carrier share of international sectors" },
  { stage: "Yield", metric: `${signed(europe.yield_headroom_pct!)}`, note: "Europe headroom, the widest on the map" },
];

const LEVELS = ["High", "Medium", "Low"] as const;

function Section({
  n,
  framework,
  question,
  children,
  therefore,
}: {
  n: number;
  framework: string;
  question: string;
  children: React.ReactNode;
  therefore: string;
}) {
  return (
    <section className="border-t-2 border-ink pt-6">
      <div className="flex flex-wrap items-baseline gap-x-4">
        <span className="tnum font-serif text-4xl font-semibold text-red">{n}</span>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
            {framework}
          </p>
          <h2 className="font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">{question}</h2>
        </div>
      </div>

      <div className="mt-8 space-y-12">{children}</div>

      <p className="mt-10 border-l-2 border-red bg-wash py-4 pl-5 pr-4 text-[15px] leading-relaxed">
        <span className="font-semibold">Therefore. </span>
        {therefore}
      </p>
    </section>
  );
}

export default function Frameworks() {
  return (
    <main className="mx-auto max-w-[1180px] px-8 py-14">
      <header className="max-w-[62ch]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          How the answer was reached
        </p>
        <h1 className="mt-4 font-serif text-[clamp(2rem,5vw,3.25rem)] font-bold leading-[1.1]">
          Five frameworks, in a chain
        </h1>
        <p className="mt-5 text-[17px] leading-relaxed text-ink/75">
          No framework appears without the question it answers, and each answer is what forces
          the next. A framework that could be removed without breaking the argument is not on
          this page, which is why there is no SWOT and no PESTEL wheel: the three regulatory
          forces that are actually live show up as evidence inside the second link instead.
        </p>
      </header>

      <div className="mt-16 space-y-20">
        <Section
          n={1}
          framework="Market sizing and segmentation"
          question="Is the demand there?"
          therefore={`Yes, and ${pct(gulf.share_pct, 0)} of it touches the Gulf, ${(gulf.pax_total / europe.pax_total).toFixed(1)}x the entire direct Europe market. So can the aircraft reach it?`}
        >
          <Exhibit
            title={`Three independent methods put 2030 between ${Math.round(Math.min(...market.triangulation.estimates.filter((e) => e.value_m).map((e) => e.value_m as number)))}M and ${Math.round(Math.max(...market.triangulation.estimates.filter((e) => e.value_m).map((e) => e.value_m as number)))}M, and capacity is the binding leg`}
            source="Trend extrapolation, income-elasticity fit and a capacity count, computed in src/market_sizing.py. Reported as a band; the average is never drawn."
            evidence={
              <>
                <p>
                  The three methods do not agree, and that is the useful output. The spread is
                  the honest statement of what is knowable, so this project reports the band and
                  refuses to average it into a single false number.
                </p>
                <p>
                  The red bar is the capacity method, which produces the low end. When capacity
                  is the constraint rather than demand, more aircraft do not create more
                  passengers, they create more empty seats.
                </p>
              </>
            }
          >
            <SizingBand />
          </Exhibit>

          <Exhibit
            title={`Half of India's international traffic touches the Gulf, ${(gulf.pax_total / europe.pax_total).toFixed(1)}x the entire direct Europe market`}
            source="DGCA Table 3, international country-pair passengers, both directions, 2025."
            evidence={
              <p>
                DGCA counts flight sectors, not origin and destination. A passenger flying Delhi
                to Dubai to London is counted here as a Gulf passenger, and separating the two is
                what the rest of this case is about.
              </p>
            }
          >
            <CorridorScale />
          </Exhibit>
        </Section>

        <Section
          n={2}
          framework="External analysis"
          question="Can the aircraft get access?"
          therefore={`Barely. Dubai is at ${pct(dubai.utilisation_pct)} of entitlement and Abu Dhabi at ${pct(abudhabi.utilisation_pct)}, so the corridor is not uniformly capped but has room for roughly 4% of the order book. So can Indian carriers operate the alternative?`}
        >
          <Exhibit
            title="Five forces on the India long-haul corridor, each carrying a number rather than an adjective"
            source="Porter's five forces as set out in DogInfantry/claude-skill-management-consultant-B1. Every cell's evidence is computed in-repo or explicitly marked unavailable."
            evidence={
              <p>
                A five-forces chart with five opinions in boxes is decoration. Each force here
                names the figure that decides it, and where no figure exists, as with wide-body
                lease rates, the cell says so instead of guessing.
              </p>
            }
          >
            <ul className="grid gap-px bg-light sm:grid-cols-2 lg:grid-cols-3">
              {FORCES.map((f) => (
                <li key={f.force} className="bg-paper p-5">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
                    {f.force}
                  </p>
                  <p className="mt-1.5 font-serif text-xl font-semibold text-red">{f.verdict}</p>
                  <p className="mt-2 text-[13.5px] leading-relaxed text-ink/75">{f.evidence}</p>
                </li>
              ))}
            </ul>
          </Exhibit>

          <Exhibit
            title={`The premise reverses: Indian carriers went ${pct(firstYear.Indian)} to ${pct(lastYear.Indian)} of international sectors while the Gulf fell ${pct(firstYear.Gulf)} to ${pct(lastYear.Gulf)}`}
            source={`DGCA international carrier-wise, ${firstYear.year} to ${lastYear.year}. Computed in src/benchmarking.py.`}
            evidence={
              <p>
                Most versions of this question assume India is losing its own international
                market. It is winning it. The deficit is specifically long-haul and specifically
                range-bound, which is a different problem with a different answer.
              </p>
            }
          >
            <ShareTrend />
          </Exhibit>
        </Section>

        <Section
          n={3}
          framework="Internal analysis"
          question="Can Indian carriers operate it?"
          therefore={`The capability is short-haul shaped. IndiGo flies ${Math.round(indigo.stage_length_km).toLocaleString()} km on average against Air India's ${Math.round(airIndia.stage_length_km).toLocaleString()} km, at a higher load factor and far more capacity. So does the long-haul version pay?`}
        >
          <Exhibit
            title="IndiGo fills more seats over shorter distances, which is the capability the wide-body order has to change"
            source="DGCA carrier-wise, latest complete year. Bubble area is available seat kilometres."
            evidence={
              <p>
                The horizontal distance between the bubbles is the capability gap. Load factor is
                not the problem: the network shape is. A fleet optimised for high-frequency short
                sectors does not become a long-haul operation by buying aircraft.
              </p>
            }
          >
            <CarrierCapability />
          </Exhibit>

          <Exhibit
            title="The value chain has one stage nobody publishes, and it is carried as a risk rather than filled in"
            source="Each stage labelled with the computed metric that governs it. Crew and MRO is genuinely unavailable: type-rated pilot numbers are not published."
            evidence={
              <p>
                Four of five stages have a number. The fifth does not, and inventing one would
                have been the easiest thing on this page. It appears in the risk register instead,
                with the leading indicator that would resolve it.
              </p>
            }
          >
            <ol className="grid gap-px bg-light sm:grid-cols-3 lg:grid-cols-5">
              {VALUE_CHAIN.map((v) => (
                <li key={v.stage} className="bg-paper p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
                    {v.stage}
                  </p>
                  <p className="tnum mt-2 font-serif text-lg font-semibold">{v.metric}</p>
                  <p className="mt-1.5 text-[12.5px] leading-snug text-ink/70">{v.note}</p>
                </li>
              ))}
            </ol>
          </Exhibit>
        </Section>

        <Section
          n={4}
          framework="Profitability and profit pools"
          question="Does the long-haul version pay?"
          therefore={`Not on the Gulf. It is ${pct(gulf.pax_share_pct!, 0)} of passengers and ${pct(gulf.revenue_share_pct!, 0)} of revenue, and its yield headroom is ${signed(gulf.yield_headroom_pct!)} against Europe at ${signed(europe.yield_headroom_pct!)}. So where do the aircraft go?`}
        >
          <Exhibit
            title={`The Gulf carries ${pct(gulf.pax_share_pct!, 0)} of the passengers and ${pct(gulf.revenue_share_pct!, 0)} of the revenue, the widest gap of any corridor`}
            source="Corridor revenue modelled from stage length and RPK, every seam labelled. Computed in src/profit_pools.py."
            evidence={
              <p>
                Short sectors earn less per passenger. The Gulf is the only corridor where the
                revenue share falls this far below the passenger share, and it is the corridor
                the order book would most naturally be pointed at.
              </p>
            }
          >
            <PaxVsRevenue />
          </Exhibit>

          <Exhibit
            title="The cost problem is a currency problem: the rupee added more to unit cost than the entire net rise"
            source="IndiGo FY2025 to FY2026 CASK bridge from the published filings. Computed in src/scenario.py."
            evidence={
              <>
                <p>
                  Fuel fell. Real non-fuel cost rose slightly. Currency added +0.41 INR per ASK
                  against a net rise of +0.34, so without the rupee the airline&rsquo;s unit cost
                  would have fallen.
                </p>
                <p>
                  This matters for the recommendation because wide-body ownership and lease
                  obligations are dollar-denominated, which makes the currency exposure worse
                  exactly where the capacity is being added.
                </p>
              </>
            }
          >
            <CaskBridge />
          </Exhibit>
        </Section>

        <Section
          n={5}
          framework="Go to market and market entry"
          question="So what should be done?"
          therefore="Compete with the Gulf hubs rather than flying more aircraft to them. Europe first, North America second, Gulf capacity roughly flat."
        >
          <Exhibit
            title="Only one option is both available this decade and value-creating, and it is not the one that follows the traffic"
            source="Option menu from docs/recommendation.md, parsed rather than retyped. Axes are ordinal: time to capacity from the table's own wording, capital likewise."
            evidence={
              <>
                <p>
                  The axes are ordinal scales over the table&rsquo;s own words, stated here so
                  every placement can be checked against it. The damp-lease bridge sits at low
                  capital and immediate availability, and its economics are explicitly
                  unquantified because transaction lease rates are paywalled.
                </p>
                <p>
                  There is no net present value on this page. A discounted cash flow per option
                  would need a discount rate, a capital cost, a residual value and a corridor
                  yield, and not one of the four can be verified here.
                </p>
              </>
            }
          >
            <OptionMatrix />
          </Exhibit>

          <Exhibit
            title={`Nine risks, and the two that are high on both axes are the ones outside the airline's control`}
            source="Risk register from docs/recommendation.md, parsed rather than retyped, so the page and the written recommendation cannot disagree."
            evidence={
              <p>
                Every row carries what would falsify it and the leading indicator that would show
                it moving first. A risk register without a falsifier is a list of worries.
              </p>
            }
          >
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] border-collapse text-[13px]">
                <thead>
                  <tr>
                    <th className="w-24 border-b border-light p-2 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-grey">
                      Likelihood
                    </th>
                    {LEVELS.map((impact) => (
                      <th
                        key={impact}
                        className="border-b border-light p-2 text-left text-[11px] font-semibold uppercase tracking-[0.1em] text-grey"
                      >
                        {impact} impact
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {LEVELS.map((likelihood) => (
                    <tr key={likelihood}>
                      <th className="border-b border-light p-2 text-left align-top font-semibold">
                        {likelihood}
                      </th>
                      {LEVELS.map((impact) => {
                        const cell = narrative.risks.filter(
                          (r) => r.Likelihood === likelihood && r.Impact === impact,
                        );
                        const hot = likelihood === "High" && impact === "High";
                        return (
                          <td
                            key={impact}
                            className={`border-b border-light p-2 align-top ${hot ? "bg-red text-paper" : cell.length ? "bg-wash" : ""}`}
                          >
                            <ul className="space-y-1">
                              {cell.map((r) => (
                                <li key={r.Risk} className="leading-snug">
                                  {r.Risk}
                                </li>
                              ))}
                            </ul>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Exhibit>
        </Section>
      </div>

      <footer className="mt-20 border-t border-light pt-6 text-[13px] leading-relaxed text-grey">
        Framework definitions are cited to{" "}
        <a
          className="underline decoration-light underline-offset-4 hover:text-red"
          href="https://github.com/DogInfantry/claude-skill-management-consultant-B1"
        >
          claude-skill-management-consultant-B1
        </a>{" "}
        rather than rewritten. Every figure on this page is computed in-repo, or marked
        unavailable where no primary source exists.
      </footer>
    </main>
  );
}
