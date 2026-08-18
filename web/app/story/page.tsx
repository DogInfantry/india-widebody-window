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

export default function Story() {
  return (
    <main className="mx-auto max-w-[1180px] px-8 py-14">
      <header className="max-w-[64ch]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          The argument, in order
        </p>
        <h1 className="mt-4 font-serif text-[clamp(2rem,5vw,3.25rem)] font-bold leading-[1.1]">
          Eighteen steps, each one a claim, in the order a partner would hear them
        </h1>
        <p className="mt-5 text-[17px] leading-relaxed text-ink/75">
          Every heading below is the takeaway rather than the topic, so the page can be read by
          its headings alone and still carry the case. The client is {brief.client.replace(/\.$/, "")};
          the decision is where the first tranche of a firm wide-body order goes.
        </p>
        <p className="mt-4 text-[13.5px] leading-relaxed text-grey">
          Each exhibit opens on its chart. The tabs behind it hold the argument, how the number was
          computed, and what would falsify it. Same four tabs everywhere on this site.
        </p>
      </header>

      {/* A contents list, because eighteen steps without one is a scroll and not
          a document. Every entry is the action title, not a section name. */}
      <nav aria-label="Contents" className="mt-12 border-y border-light py-6">
        <ol className="grid gap-x-8 gap-y-2 sm:grid-cols-2">
          {ACTS.flatMap((act) =>
            act.steps.map((id) => (
              <li key={id} className="text-[13.5px] leading-snug">
                <Link
                  href={`#exhibit-${id}`}
                  className="text-ink/70 underline decoration-light underline-offset-4 hover:text-red"
                >
                  {BY_ID[id]?.title ?? id}
                </Link>
              </li>
            )),
          )}
        </ol>
      </nav>

      <div className="mt-16 space-y-24">
        {ACTS.map((act) => (
          <section key={act.n} aria-labelledby={`act-${act.n}`}>
            <div className="flex flex-wrap items-baseline gap-x-5 border-t-2 border-ink pt-5">
              <span className="tnum font-serif text-4xl font-semibold text-red">{act.n}</span>
              <div>
                <h2 id={`act-${act.n}`} className="font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">
                  {act.title}
                </h2>
                <p className="mt-1 max-w-[62ch] text-[14.5px] leading-relaxed text-grey">
                  {act.lead}
                </p>
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
                      <h3 className="max-w-[26ch] font-serif text-[clamp(1.3rem,2.2vw,1.7rem)] font-semibold leading-snug">
                        {step.title}
                      </h3>
                      {step.paragraphs
                        .filter((p) => p.kind !== "aside")
                        .slice(0, 1)
                        .map((p, i) => (
                          <p key={i} className="mt-4 text-[15px] leading-relaxed text-ink/75">
                            {p.text}
                          </p>
                        ))}
                      {step.paragraphs.length > 1 && (
                        <p className="mt-3 text-[12.5px] text-grey">
                          The rest of the argument is on the Evidence tab.
                        </p>
                      )}
                      {step.pivot && (
                        <p className="mt-5 border-l-2 border-red pl-4 text-[13px] leading-relaxed text-ink/75">
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
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red">
          Therefore
        </p>
        <p className="mt-4 max-w-[30ch] font-serif text-[clamp(1.6rem,3.6vw,2.5rem)] font-semibold leading-[1.15]">
          Compete with the Gulf hubs. Do not fly more aircraft to them.
        </p>
        <div className="mt-6 max-w-[64ch] space-y-4 text-[15px] leading-relaxed text-ink/75">
          {brief.recommendation.slice(0, 3).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
        <p className="mt-6 text-[14px]">
          <Link
            href="/frameworks"
            className="underline decoration-light underline-offset-4 hover:text-red"
          >
            The option menu, the risk register and what would falsify each option
          </Link>
        </p>
      </section>

      <footer className="mt-16 border-t border-light pt-6 text-[13px] leading-relaxed text-grey">
        Every step above is parsed from the analysis site&rsquo;s own markup rather than rewritten,
        so the two surfaces cannot disagree. A portfolio simulation, not a client engagement.
      </footer>
    </main>
  );
}
