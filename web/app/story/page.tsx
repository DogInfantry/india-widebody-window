import type { Metadata } from "next";
import Link from "next/link";
import { RegisteredExhibit } from "@/lib/exhibits";
import { brief, story } from "@/lib/data";

export const metadata: Metadata = { title: "The argument, in order" };

// The narrative spine, restored.
//
// **This reverses a recommendation made in an earlier session.** When the app was
// built the 22-step scrollytelling narrative was dropped, on the argument that a
// deck and a dashboard covered it. They did not. The action titles WERE the
// argument: eighteen of them, in a deliberate order, each one the claim its
// exhibit supports. Losing all of them is most of why the app read as a
// collection of charts rather than as a case.
//
// **Not a second copy of the prose.** Every step here is parsed out of
// `docs/index.html` by `src/app_export.py`, which is the rule the report and the
// deck already follow: index.html holds the words, every other surface re-lays
// them out. Nothing on this page is typed.
//
// The static mirror uses a sticky graphic and scrollama. This uses a two-column
// layout with the exhibit sticky beside its step on wide screens and stacked
// below it on narrow ones, which needs no scroll listener, no observer and no
// third script, and degrades to a readable document when printed.

const ACTS = [
  {
    n: "01",
    title: "The base, and the prize",
    steps: ["domestic_share", "corridor_scale", "gateway_flows", "value_at_stake"],
    lead: "Where the volume is, and where India stops being able to see it.",
  },
  {
    n: "02",
    title: "Who flies it, and with what",
    steps: ["who_carries_india", "carrier_share_trend", "stage_length_gap"],
    lead: "The premise most people arrive with, reversed, and the capability gap that survives the reversal.",
  },
  {
    n: "03",
    title: "Where the money actually is",
    steps: ["pax_vs_revenue_share", "profit_pool", "yield_headroom", "cargo_asymmetry"],
    lead: "Half the passengers, a third of the revenue, and the corridor with the least room of any to absorb a fare decline.",
  },
  {
    n: "04",
    title: "What is being bought into",
    steps: ["market_sizing", "scenarios", "absorption_frontier", "fleet_gap"],
    lead: "The market to 2030, and an order book sized for a network a quarter longer than the one that exists.",
  },
  {
    n: "05",
    title: "The cost base it lands on",
    steps: ["cask_bridge", "fuel_fx_sensitivity", "load_factor_slope"],
    lead: "A currency problem wearing a cost problem's clothes, and the constraint that is not demand.",
  },
];

const BY_ID = Object.fromEntries(story.map((s) => [s.chart, s]));

const STEP_COUNT = ACTS.reduce((n, a) => n + a.steps.length, 0);
const PIVOT_COUNT = ACTS.flatMap((a) => a.steps).filter((id) => BY_ID[id]?.pivot).length;

export default function Story() {
  return (
    <main className="mx-auto max-w-[1180px] px-8 py-14">
      <header className="max-w-[64ch]">
        <p className="text-micro font-semibold uppercase tracking-[0.14em] text-grey">
          The argument, in order
        </p>
        <h1 className="mt-4 font-serif text-h1 font-bold leading-[1.1]">
          Eighteen steps, each one a claim, in the order a partner would hear them
        </h1>
        <p className="mt-5 text-lead leading-relaxed text-ink/75">
          Every heading below is the takeaway rather than the topic, so the page can be read by
          its headings alone and still carry the case. The client is {brief.client.replace(/\.$/, "")};
          the decision is where the first tranche of a firm wide-body order goes.
        </p>
        <p className="mt-4 text-small leading-relaxed text-grey">
          Each exhibit opens on its chart. The tabs behind it hold the argument, how the number was
          computed, and what would falsify it. Same four tabs everywhere on this site.
        </p>
      </header>

      {/* A contents list, because eighteen steps without one is a scroll and not
          a document. Every entry is the action title, not a section name. */}
      {/* The argument map, and it used to be eighteen faded links in two columns.
          Four things were wrong with that and all four were fixable from data
          this file already held:

            `ACTS.flatMap(...)` threw the act structure away. Five acts, each with
            a title and a lead, collapsed into one undifferentiated run, so the
            only place all eighteen headings appear together said nothing about
            the shape of the argument beneath it.

            `text-ink/70` is literally the faded look, and a `decoration-light`
            underline on white is close to invisible, so the rows did not read as
            links at all.

            The order is the argument and the order was invisible.

            FIVE of the eighteen steps carry a `pivot`, the points where the
            answer changed, and the index discarded them. That is the strongest
            reason anyone would click into a step.

          This project's own position is that the action titles ARE the argument.
          This block should be the clearest thing on the page. Both counts below
          are derived, never typed. */}
      <nav aria-label="Contents" className="mt-14 border-t-2 border-ink pt-8">
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
          <h2 className="font-serif font-semibold">The argument, in five moves</h2>
          <p className="text-micro font-semibold uppercase tracking-[0.14em] text-grey">
            {STEP_COUNT} steps &middot;{" "}
            <span className="text-red">{PIVOT_COUNT} changed the answer</span>
          </p>
        </div>

        <ol className="mt-8 grid gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-5">
          {ACTS.map((act, actIndex) => (
            <li key={act.n}>
              <p className="flex items-baseline gap-2 border-b border-light pb-2">
                <span className="tnum font-serif text-h3 font-semibold text-red">{act.n}</span>
                <span className="text-small font-semibold leading-snug">{act.title}</span>
              </p>

              <ol className="mt-1">
                {act.steps.map((id, i) => {
                  const step = BY_ID[id];
                  // Numbered by position across every act, so the numeral is the
                  // argument's own order and cannot drift from it.
                  const ordinal =
                    ACTS.slice(0, actIndex).reduce((n, a) => n + a.steps.length, 0) + i + 1;
                  return (
                    <li key={id}>
                      <Link href={`#exhibit-${id}`} className="block-link group py-2.5 pl-3 pr-2">
                        <span className="flex items-baseline gap-2">
                          <span className="tnum text-micro font-semibold text-grey">
                            {String(ordinal).padStart(2, "0")}
                          </span>
                          <span className="min-w-0">
                            <span className="block text-small leading-snug">
                              {step?.title ?? id}{" "}
                              <span aria-hidden className="go">
                                &rarr;
                              </span>
                            </span>
                            {step?.pivot && (
                              <span className="mt-1 block text-micro font-semibold uppercase tracking-[0.1em] text-red">
                                {step.pivot.label} &middot; the answer changed here
                              </span>
                            )}
                          </span>
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ol>
            </li>
          ))}
        </ol>
      </nav>

      <div className="mt-16 space-y-24">
        {ACTS.map((act) => (
          <section key={act.n} aria-labelledby={`act-${act.n}`}>
            {/* The act opener, full-bleed and loud.
                Eighteen steps ran at one rhythm before this: sticky prose left,
                exhibit right, eighteen times, with nothing to mark where an
                argument ended and the next began. Five openers over twenty-four
                screens is a cadence; a numeral at display scale against 15px body
                is what makes a reader look up. */}
            <div className="relative left-1/2 w-screen -translate-x-1/2 border-y border-light bg-wash">
              <div className="mx-auto flex max-w-[1180px] flex-wrap items-baseline gap-x-8 gap-y-2 px-8 py-10">
                <span className="tnum display leading-none text-red">{act.n}</span>
                <div className="min-w-0 flex-1">
                  <h2 id={`act-${act.n}`} className="font-serif font-semibold">
                    {act.title}
                  </h2>
                  <p className="mt-2 max-w-[62ch] text-body leading-relaxed text-grey">
                    {act.lead}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-12 space-y-20">
              {act.steps.map((id) => {
                const step = BY_ID[id];
                return (
                  <div key={id} className="grid gap-10 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
                    {/* The step prose, sticky beside its exhibit on wide screens.
                        This is the sticky-graphic pattern inverted: the words hold
                        still and the reader's eye moves to the chart, which is the
                        right way round when the chart is the taller element. */}
                    <div className="lg:sticky lg:top-24 lg:self-start">
                      <h3 className="max-w-[26ch] font-serif text-h3 font-semibold leading-snug">
                        {step.title}
                      </h3>
                      {step.paragraphs
                        .filter((p) => p.kind !== "aside")
                        .slice(0, 1)
                        .map((p, i) => (
                          <p key={i} className="mt-4 text-body leading-relaxed text-ink/75">
                            {p.text}
                          </p>
                        ))}
                      {step.paragraphs.length > 1 && (
                        <p className="mt-3 text-caption text-grey">
                          The rest of the argument is on the Evidence tab.
                        </p>
                      )}
                      {step.pivot && (
                        <p className="mt-5 border-l-2 border-red pl-4 text-small leading-relaxed text-ink/75">
                          <span className="font-semibold text-red">{step.pivot.label}. </span>
                          The answer changed here.
                        </p>
                      )}
                    </div>

                    <RegisteredExhibit id={id} />
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>

      <section className="mt-24 border-t-2 border-red pt-6">
        <p className="text-micro font-semibold uppercase tracking-[0.14em] text-red">
          Therefore
        </p>
        <p className="mt-4 max-w-[30ch] font-serif text-h1 font-semibold leading-[1.15]">
          Compete with the Gulf hubs. Do not fly more aircraft to them.
        </p>
        <div className="mt-6 max-w-[64ch] space-y-4 text-body leading-relaxed text-ink/75">
          {brief.recommendation.slice(0, 3).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
        <p className="mt-6 text-body">
          <Link
            href="/frameworks"
            className="underline decoration-light underline-offset-4 hover:text-red"
          >
            The option menu, the risk register and what would falsify each option
          </Link>
        </p>
      </section>

      <footer className="mt-16 border-t border-light pt-6 text-small leading-relaxed text-grey">
        Every step above is parsed from the analysis site&rsquo;s own markup rather than rewritten,
        so the two surfaces cannot disagree. A portfolio simulation, not a client engagement.
      </footer>
    </main>
  );
}
