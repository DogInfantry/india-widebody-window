import Link from "next/link";
import { DriverTree } from "@/components/DriverTree";
import { PastTheGulf } from "@/components/PastTheGulf";
import { CorridorMap } from "@/components/CorridorMap";
import { OrderBookPictogram, SequenceRibbon, ShareRing } from "@/components/scan-forms";
import { CountUp, Reveal } from "@/components/motion-primitives";
import { RegisteredExhibit } from "@/lib/exhibits";
import { brief, company, corridors, kpis } from "@/lib/data";

// The executive answer, and nothing that is not evidence for it.
//
// **Rebuilt 2026-08-19, because the page was measurably a wall of text.** It ran
// 1,722 words against three exhibits, 574 words per exhibit, the worst ratio on
// the site, and the first chart did not appear until the sixth of eight
// sections. A reader giving this two minutes never reached one. The written case
// was strong and the page made them dig for it.
//
// Three changes, in order of how much each was worth:
//
//   1. The answer is now followed IMMEDIATELY by a picture of itself. The
//      governing thought is "fly past the Gulf, not to it", which is a geometry,
//      and it had never been drawn on any surface.
//   2. `gateway_flows` moved here from `/story`. It is the Sankey where the
//      passenger disappears into a Gulf hub, which is to say it is the argument,
//      and it was three pages away from the answer it supports.
//   3. Four exhibits instead of three, and the closing paragraphs that asserted
//      in words what the exhibits now show are cut.
//
// **The word count is NOT much lower, and the plan said it would be.** It is
// about level: prose came out, and diagram labels, a second exhibit and two
// section headings went in. That is worth recording rather than quietly
// restating the goal, because the metric that actually moved is a different one.
// The first visual used to arrive in the sixth of eight sections, roughly 60 per
// cent of the way down; it now arrives at **6 per cent**, and the first exhibit
// at 14. Words before the first picture was always the real complaint. Raw word
// count was a proxy for it and turned out to be a poor one.
//
// Order is deliberate: who and what is being decided, then the answer, then the
// answer as a picture, then the same thing measured, then the proof numbers,
// then the case in four moves, then how it is judged, then the tree that indexes
// everything else.

const spread = company.spread;
const gulfPax = corridors.find((c) => c.region === "Gulf")!.pax_total;

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

        {/* The answer, drawn, before the answer is explained. */}
        <PastTheGulf />

        {/* The answer is a SEQUENCE and it existed only as a sentence. Order is
            the whole content of the recommendation and the one thing prose
            carries worst. */}
        <SequenceRibbon />

        <p className="mt-8 max-w-[54ch] text-[13.5px] leading-relaxed text-grey">
          <span className="font-medium text-ink">What this deliberately is not.</span>{" "}
          {brief.not_this}
        </p>
      </div>
    </header>

    {/* The same claim, measured. This is the exhibit the argument turns on and
        it used to live three pages away on /story. */}
    <Reveal className="mt-20">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
        The prize is real, and it is mis-located
      </p>
      <h2 className="mt-3 max-w-[30ch] font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">
        Every corridor India flies, and the two the wide-bodies should take
      </h2>

      {/* The schematic above states the thesis; this is the same thesis on real
          geography, with every corridor the analysis covers rather than only the
          one it argues about. */}
      <CorridorMap />

      {/* A share should look like a share. Nothing on this site showed one:
          `corridor_scale` compares nine corridors, which is a different question
          from how much of India's flying touches the Gulf at all. */}
      <div className="mt-10">
        <ShareRing
          sub={`${(gulfPax / 1e6).toFixed(1)}M passengers a year, and roughly four times India's entire direct Europe market. The corridor is the prize. The hub is not the destination.`}
        />
      </div>

      <div className="mt-14 space-y-16">
        <RegisteredExhibit id="corridor_scale" />
        <RegisteredExhibit id="gateway_flows" />
      </div>
    </Reveal>

    <Reveal className="mt-20">
      <section aria-label="Key figures" className="grid gap-px bg-light sm:grid-cols-2 lg:grid-cols-3">
        {kpis.map((k) => (
          <div key={k.label} className="bg-paper p-6">
            <p className="tnum font-serif text-[2.5rem] font-semibold leading-none text-red">
              <CountUp value={k.value} />
            </p>
            <p className="mt-3 text-[15px] font-medium leading-snug">{k.label}</p>
            {k.note && <p className="mt-2 text-[12.5px] leading-relaxed text-grey">{k.note}</p>}
          </div>
        ))}
      </section>
    </Reveal>

    {/* SCQA, one claim per box. The full argument is on /story; this is the
        four-sentence version a partner hears first. */}
    <Reveal className="mt-20">
      <section aria-labelledby="scqa">
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
    </Reveal>

    {/* The scorecard. Four metrics written as the success measures of this
        engagement, two of which are adverse and say so. */}
    <Reveal className="mt-20">
      <section aria-labelledby="metrics">
        <h2 id="metrics" className="font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">
          How this decision will be judged, and where it stands today
        </h2>

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

        {/* The one figure that states the client's problem in a single line. */}
        <p className="mt-8 max-w-[64ch] border-l-2 border-red pl-5 text-[15px] leading-relaxed">
          IndiGo did not cover its unit cost in {spread.year}: RASK{" "}
          <span className="tnum font-semibold">{spread.rask.toFixed(2)}</span> against CASK{" "}
          <span className="tnum font-semibold">{spread.cask.toFixed(2)}</span>, and the rupee
          added{" "}
          <span className="tnum font-semibold">
            {spread.currency_contribution.toFixed(2)}
          </span>{" "}
          to unit cost in the same year, {Math.round(spread.currency_vs_gap)} times the gap.
          This is the balance sheet the wide-bodies are being bought onto.
        </p>
      </section>
    </Reveal>

    <Reveal className="mt-20">
      <section aria-labelledby="tree">
        <h2 id="tree" className="sr-only">
          Value driver tree
        </h2>
        <DriverTree />
      </section>
    </Reveal>

    <Reveal className="mt-20">
      <section className="space-y-16">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          Two more exhibits, and the answer follows
        </p>
        <RegisteredExhibit id="yield_headroom" />

        <div>
          <h3 className="max-w-[36ch] font-serif text-[clamp(1.2rem,2.2vw,1.6rem)] font-semibold">
            The firm order is 140 wide-bodies, and 68 of them have nothing to do at today&rsquo;s
            sector length
          </h3>
          <p className="mt-3 max-w-[62ch] text-[14px] leading-relaxed text-grey">
            Everywhere else this project counts the order book in available seat kilometres,
            because a seat is not capacity until you say how far and how often it flies. That is
            right for the arithmetic and useless to a reader. Counted as aeroplanes, the surplus
            is visible.
          </p>
          <div className="mt-6">
            <OrderBookPictogram />
          </div>
        </div>

        <RegisteredExhibit id="absorption_frontier" />
        <p className="max-w-[62ch] text-[15px] leading-relaxed text-ink/75">
          <Link
            href="/story"
            className="underline decoration-light underline-offset-4 hover:text-red"
          >
            The full argument runs in order on the narrative page
          </Link>
          , eighteen steps, each heading a claim.
        </p>
      </section>
    </Reveal>

    <nav
      aria-label="Continue"
      className="mt-20 grid gap-px border-t border-light bg-light sm:grid-cols-2"
    >
      {DOORS.map((d) => (
        <Link
          key={d.href}
          href={d.href}
          className="block-link group bg-paper py-7 pl-5 pr-6"
        >
          <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
            {d.time}
          </span>
          <span className="mt-2 block font-serif text-2xl font-semibold group-hover:text-red">
            {d.label} <span aria-hidden className="go">&rarr;</span>
          </span>
        </Link>
      ))}
    </nav>

    <footer className="mt-16 border-t border-light pt-6 text-[13px] leading-relaxed text-grey">
      A self-directed case in the style of Bain Capability Network Advanced Manufacturing
      &amp; Services work. <strong>Not a client engagement</strong>: IndiGo has not
      commissioned, seen or endorsed it. Every figure is computed in-repo from DGCA,
      Eurostat, IATA and World Bank data.{" "}
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
