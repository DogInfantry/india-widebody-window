import Link from "next/link";
import { Exhibit } from "@/components/Exhibit";
import { AbsorptionFrontier, CorridorScale, YieldHeadroom } from "@/components/charts";
import { corridors, economics, fleet, kpis } from "@/lib/data";

// The executive answer, and nothing that is not evidence for it. Vizro's
// dashboard method puts this at the Overview level: view-only, no cross-filter,
// five to nine metrics. Interaction lives one level down on /dashboard, because
// an executive view that needs to be operated is not an executive view.
//
// Every figure below is read from the export. None is written by hand.

// No casts: the JSON imports carry their own types, so a shape change in the
// Python export becomes a TypeScript error here rather than a blank page.
const vas = economics.value_at_stake;
const absorption = fleet.absorption_summary;
const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;

const DOORS = [
  { href: "/dashboard", label: "Explore it", time: "Interactive" },
  { href: "/frameworks", label: "How it was reached", time: "The analysis" },
  { href: "/methodology", label: "Check it", time: "For the sceptic" },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-[1180px] px-8 py-16 md:py-24">
      <header>
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          Commercial aviation &middot; India and the Gulf
        </p>
        <h1 className="mt-5 text-[clamp(2.5rem,6vw,4.25rem)] font-bold">
          India&rsquo;s Wide-Body Window
        </h1>
        <p className="mt-6 max-w-[36ch] font-serif text-[clamp(1.15rem,2vw,1.5rem)] leading-snug text-ink/75">
          Where should Indian carriers deploy their next 100 long-haul aircraft, and can the
          India-Gulf corridor absorb them?
        </p>

        <div className="mt-12 border-t-2 border-red pt-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red">
            The answer
          </p>
          <p className="mt-4 max-w-[28ch] font-serif text-[clamp(1.75rem,4vw,2.75rem)] font-semibold leading-[1.15]">
            Compete with the Gulf hubs. Do not fly more aircraft to them.
          </p>
          <p className="mt-4 max-w-[54ch] text-ink/70">
            Europe first, North America second, Gulf capacity roughly flat. The corridor is
            still the prize:{" "}
            <strong className="tnum font-semibold text-ink">
              {vas.connecting_pax_m.toFixed(1)}M
            </strong>{" "}
            passengers a year connect through a Gulf hub rather than stopping there, worth{" "}
            <strong className="tnum font-semibold text-ink">
              INR {Math.round(vas.revenue_floor_inr_cr).toLocaleString()} to{" "}
              {Math.round(vas.revenue_ceiling_inr_cr).toLocaleString()} crore
            </strong>
            . It is won by flying past the Gulf, not to it.
          </p>
        </div>
      </header>

      <section aria-label="Key figures" className="mt-16 grid gap-px bg-light sm:grid-cols-2 lg:grid-cols-3">
        {kpis.map((k) => (
          <div key={k.label} className="bg-paper p-6">
            <p className="tnum font-serif text-[2.5rem] font-semibold leading-none text-red">
              {k.value}
            </p>
            <p className="mt-3 text-[15px] font-medium leading-snug">{k.label}</p>
            {k.note && <p className="mt-2 text-[12.5px] leading-relaxed text-grey">{k.note}</p>}
          </div>
        ))}
      </section>

      <section className="mt-20 space-y-16">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          Three exhibits, and the answer follows from them
        </p>

        <Exhibit
          title={`Half of India's international traffic touches the Gulf, ${(gulf.pax_total / europe.pax_total).toFixed(1)}x the entire direct Europe market`}
          source="DGCA Table 3, international country-pair passengers, both directions, 2025. Computed in src/benchmarking.py."
          evidence={
            <>
              <p>
                {(gulf.pax_total / 1e6).toFixed(1)}M passengers a year touch a Gulf point against{" "}
                {(europe.pax_total / 1e6).toFixed(1)}M flying to Europe directly. That is why every
                version of this case started with the Gulf, and why the first answer was to
                reclaim it.
              </p>
              <p>
                DGCA counts flight sectors, not origin and destination. A passenger flying Delhi
                to Dubai to London appears here as a Gulf passenger. That distinction is the whole
                case, and the gap between the two measures is quantified rather than assumed.
              </p>
            </>
          }
        >
          <CorridorScale />
        </Exhibit>

        <Exhibit
          title="Gulf sectors have the least room of any corridor to absorb a yield decline, and Europe has the most"
          source="IndiGo published unit cost scaled by stage length (CASK_STAGE_ELASTICITY = -0.25, a labelled modelled knob with a sensitivity beside it). Computed in src/options.py."
          evidence={
            <>
              <p>
                Headroom is how far the fare can fall before a corridor stops covering its own
                cost. The Gulf sits at {gulf.yield_headroom_pct!.toFixed(1)}%, so at IndiGo&rsquo;s
                realised yield those sectors do not cover their cost. Europe sits at +
                {europe.yield_headroom_pct!.toFixed(1)}%.
              </p>
              <p>
                This is reported as headroom rather than as a net present value on purpose. A
                discounted cash flow per option would need a discount rate, a capital cost, a
                residual value and a corridor yield, none of which can be verified here. Headroom
                leaves the unknown on the reader&rsquo;s side of the line.
              </p>
            </>
          }
        >
          <YieldHeadroom />
        </Exhibit>

        <Exhibit
          title={`The order book clears only if the average sector lengthens about ${Math.round(absorption.stage_uplift_pct)}%, or Indian carriers take ${Math.round(absorption.share_pct_to_absorb)}% of the market`}
          source="Firm wide-body order book converted to ASK at block speed and seats per departure computed from DGCA. Computed in src/fleet_gap.py."
          evidence={
            <>
              <p>
                The curve is the average sector length Indian carriers would need to fly, at each
                possible share of the market, for the committed capacity to be absorbed. Today
                they hold {absorption.share_held_pct.toFixed(1)}%.
              </p>
              <p>
                The order book is {absorption.book_vs_growth_ratio.toFixed(2)}x the growth needed
                to hold that share. Capacity is measured in ASK rather than seats because a seat
                is not capacity until you say how far and how often it flies, and this case turns
                on how far.
              </p>
            </>
          }
        >
          <AbsorptionFrontier />
        </Exhibit>
      </section>

      <nav
        aria-label="Continue"
        className="mt-20 grid gap-px border-t border-light bg-light sm:grid-cols-3"
      >
        {DOORS.map((d) => (
          <Link
            key={d.href}
            href={d.href}
            className="group bg-paper py-7 pr-6 transition-colors hover:bg-wash focus-visible:bg-wash focus-visible:outline-2 focus-visible:outline-red"
          >
            <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
              {d.time}
            </span>
            <span className="mt-2 block font-serif text-2xl font-semibold group-hover:text-red">
              {d.label} <span aria-hidden>&rarr;</span>
            </span>
          </Link>
        ))}
      </nav>

      <footer className="mt-16 border-t border-light pt-6 text-[13px] leading-relaxed text-grey">
        A self-directed case in the style of Bain Capability Network Advanced Manufacturing &amp;
        Services commercial aviation work. Not a client engagement, and it says so. Every figure
        on this page is computed in-repo from DGCA, Eurostat and World Bank data.{" "}
        <a
          className="underline decoration-light underline-offset-4 hover:text-red"
          href="https://doginfantry.github.io/india-widebody-window/"
        >
          The full analysis site
        </a>{" "}
        remains the reproducible mirror.
      </footer>
    </main>
  );
}
