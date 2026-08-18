import Link from "next/link";
import { DriverTree } from "@/components/DriverTree";
import { RegisteredExhibit } from "@/lib/exhibits";
import { brief, company, corridors, economics, kpis } from "@/lib/data";

// The executive answer, and nothing that is not evidence for it.
//
// **What changed, and why.** This page used to open on a sector question and
// never name a client. The brief, the decision, the horizon and the success
// metrics had all been written in `docs/storyline.md` from early on; none of it
// reached a delivery surface, which is the single reason the app read as sector
// research. All of it is now parsed into the export and rendered here, so it
// cannot drift from the written case.
//
// Order is deliberate: who and what is being decided, then the answer, then how
// it is being judged, then the tree that indexes the evidence, then three proof
// exhibits, then the doors. A reader should be able to say who the client is,
// what is being decided and what the answer is inside thirty seconds.

const vas = economics.value_at_stake;
const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;
const spread = company.spread;

const DOORS = [
  { href: "/story", label: "Read the argument", time: "The narrative, in order" },
  { href: "/company", label: "The client's own numbers", time: "IndiGo" },
  { href: "/dashboard", label: "Explore it", time: "Interactive" },
  { href: "/frameworks", label: "How it was reached", time: "The analysis" },
];

const FRAME = [
  { term: "Client", value: brief.client },
  { term: "The decision", value: brief.decision },
  { term: "Horizon", value: brief.timeframe },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-[1180px] px-8 py-14 md:py-20">
      <header>
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          Commercial aviation &middot; India and the Gulf &middot; Network and fleet strategy
        </p>
        <h1 className="mt-5 text-[clamp(2.4rem,5.6vw,4rem)] font-bold">
          India&rsquo;s Wide-Body Window
        </h1>
        <p className="mt-6 max-w-[38ch] font-serif text-[clamp(1.15rem,2vw,1.5rem)] leading-snug text-ink/75">
          Where should Indian carriers deploy their next 100 long-haul aircraft, and can the
          India-Gulf corridor absorb them?
        </p>

        {/* The frame, above the fold, because a reader who cannot say whose
            decision this is inside thirty seconds is reading sector research. */}
        <dl className="mt-10 grid gap-px border-y border-light bg-light sm:grid-cols-3">
          {FRAME.map((f) => (
            <div key={f.term} className="bg-paper py-5 pr-6">
              <dt className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
                {f.term}
              </dt>
              <dd className="mt-1.5 max-w-[34ch] text-[14.5px] leading-snug">{f.value}</dd>
            </div>
          ))}
        </dl>

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
          <p className="mt-4 max-w-[54ch] text-[13.5px] leading-relaxed text-grey">
            <span className="font-medium text-ink">What this deliberately is not.</span>{" "}
            {brief.not_this}
          </p>
        </div>
      </header>

      {/* SCQA, in the client's own frame, one claim per box. The full argument is
          on /story; this is the four-sentence version a partner hears first. */}
      <section aria-labelledby="scqa" className="mt-20">
        <h2 id="scqa" className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          The case in four moves
        </h2>
        <ol className="mt-6 grid gap-px bg-light md:grid-cols-2 xl:grid-cols-4">
          {(["situation", "complication", "question", "answer"] as const).map((part) => (
            <li key={part} className="bg-paper p-6">
              <p className="font-serif text-lg font-semibold capitalize text-red">{part}</p>
              <p className="mt-3 text-[14px] leading-relaxed text-ink/80">
                {brief.scqa[part][0]}
              </p>
            </li>
          ))}
        </ol>
      </section>

      {/* The scorecard. Four metrics that were written as the success measures of
          this engagement and never shown on any surface. Two of them are red. */}
      <section aria-labelledby="metrics" className="mt-20">
        <h2 id="metrics" className="font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">
          How this decision will be judged, and where it stands today
        </h2>
        <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
          Four success metrics, all of them measurable in this repository rather than asserted.
          Two are moving the right way. The other two are the reason there is a case at all, and
          the third is the sharpest number in the project.
        </p>

        <ul className="mt-8 grid gap-px bg-light sm:grid-cols-2">
          {brief.success_metrics.map((m, i) => {
            const standing = m["Where it stands today"];
            const adverse = /inverted|against 5,316|31% of revenue/i.test(standing);
            return (
              <li key={m.Metric} className="bg-paper p-6">
                <div className="flex items-baseline gap-3">
                  <span className="tnum font-serif text-2xl font-semibold text-grey">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <p className="text-[14.5px] font-medium leading-snug">{m.Metric}</p>
                </div>
                <p
                  className={`tnum mt-3 pl-10 text-[16px] font-semibold leading-snug ${
                    adverse ? "text-red" : "text-ink"
                  }`}
                >
                  {standing}
                </p>
              </li>
            );
          })}
        </ul>

        {/* Pulled out because it is the one figure that states the client's
            problem in a single line, and it appeared on no surface at all. */}
        <p className="mt-8 max-w-[64ch] border-l-2 border-red pl-5 text-[15px] leading-relaxed">
          IndiGo did not cover its unit cost in {spread.year}: RASK{" "}
          <span className="tnum font-semibold">{spread.rask.toFixed(2)}</span> against CASK{" "}
          <span className="tnum font-semibold">{spread.cask.toFixed(2)}</span>. The gap is one
          paisa per available seat kilometre, and the rupee added{" "}
          <span className="tnum font-semibold">
            {spread.currency_contribution.toFixed(2)}
          </span>{" "}
          to unit cost in the same year, {Math.round(spread.currency_vs_gap)} times the gap. This
          is the balance sheet the wide-bodies are being bought onto.
        </p>
      </section>

      <section aria-labelledby="tree" className="mt-20">
        <h2 id="tree" className="sr-only">
          Value driver tree
        </h2>
        <DriverTree />
      </section>

      <section aria-label="Key figures" className="mt-20 grid gap-px bg-light sm:grid-cols-2 lg:grid-cols-3">
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
        <RegisteredExhibit id="corridor_scale" />
        <RegisteredExhibit id="yield_headroom" />
        <RegisteredExhibit id="absorption_frontier" />
        <p className="max-w-[62ch] text-[15px] leading-relaxed text-ink/75">
          The corridor is four times Europe at{" "}
          <span className="tnum">{(gulf.pax_total / 1e6).toFixed(1)}M</span> passengers, it has
          the least fare headroom of anywhere on the map at{" "}
          <span className="tnum text-red">{gulf.yield_headroom_pct!.toFixed(1)}%</span> against
          Europe&rsquo;s <span className="tnum">+{europe.yield_headroom_pct!.toFixed(1)}%</span>,
          and the order book is sized for a network a quarter longer than the one that exists.
          Those three facts are the recommendation.{" "}
          <Link href="/story" className="underline decoration-light underline-offset-4 hover:text-red">
            The full argument runs in order on the narrative page
          </Link>
          .
        </p>
      </section>

      <nav
        aria-label="Continue"
        className="mt-20 grid gap-px border-t border-light bg-light sm:grid-cols-2"
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
        Services commercial aviation work. <strong>Not a client engagement</strong>, and it says
        so: IndiGo has not commissioned, seen or endorsed any of it. Every figure is computed
        in-repo from DGCA, Eurostat and World Bank data.{" "}
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
