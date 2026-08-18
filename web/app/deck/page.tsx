"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AbsorptionFrontier, CorridorScale, YieldHeadroom } from "@/components/charts";
import {
  CarrierCapability,
  CaskBridge,
  OptionMatrix,
  PaxVsRevenue,
  ShareTrend,
  SizingBand,
} from "@/components/frameworks-charts";
import { access, carriers, corridors, economics, fleet, kpis, market, narrative } from "@/lib/data";

// Fifteen slides, one action title and one exhibit each, in the order a partner
// would hear the argument. Arrow keys, Page Up and Down, Home and End, plus
// scroll-snap for anyone who would rather scroll.
//
// The container is a FLEX COLUMN, not a grid. Chrome does not honour a forced
// page break between grid items, which is what silently voided the print layout
// of docs/brief.html for two commits. Print here puts one slide per sheet.

const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;
const dubai = access.entitlements.find((e) => e.foreign_point === "DUBAI")!;
const abudhabi = access.entitlements.find((e) => e.foreign_point === "ABUDHABI")!;
const indigo = carriers.international_summary.find((c) => c.airline === "IndiGo")!;
const airIndia = carriers.international_summary.find((c) => c.airline === "Air India")!;
const first = carriers.share_trend[0];
const last = carriers.share_trend[carriers.share_trend.length - 1];
const abs = fleet.absorption_summary;
const vas = economics.value_at_stake;
const headroom = fleet.gulf_headroom;
// Computed. This read "between 96M and 109M" as a literal for one commit.
const band = market.triangulation.estimates
  .map((e) => e.value_m)
  .filter((v): v is number => v !== null);

const n1 = (x: number) => x.toFixed(1);
const n0 = (x: number) => Math.round(x).toLocaleString();
const sgn = (x: number) => `${x > 0 ? "+" : ""}${x.toFixed(1)}%`;

type Slide = { kicker: string; title: string; body?: React.ReactNode; exhibit?: React.ReactNode };

const SLIDES: Slide[] = [
  {
    kicker: "Commercial aviation · India and the Gulf",
    title: "Where should Indian carriers deploy their next 100 long-haul aircraft, and can the India-Gulf corridor absorb them?",
    body: (
      <p className="mt-8 max-w-[46ch] font-serif text-[clamp(1.5rem,3vw,2.25rem)] font-semibold leading-tight text-red">
        Compete with the Gulf hubs. Do not fly more aircraft to them.
      </p>
    ),
  },
  {
    kicker: "The case in six numbers",
    title: "Every figure here is computed in-repo from DGCA, Eurostat and World Bank data",
    body: (
      <div className="mt-8 grid w-full gap-px bg-light sm:grid-cols-2 lg:grid-cols-3">
        {kpis.map((k) => (
          <div key={k.label} className="bg-paper p-5">
            <p className="tnum font-serif text-[2rem] font-semibold leading-none text-red">
              {k.value}
            </p>
            <p className="mt-2 text-[14px] font-medium leading-snug">{k.label}</p>
          </div>
        ))}
      </div>
    ),
  },
  {
    kicker: "1. Size the prize",
    title: `Half of India's international traffic touches the Gulf, ${n1(gulf.pax_total / europe.pax_total)}x the entire direct Europe market`,
    exhibit: <CorridorScale />,
  },
  {
    kicker: "1. Size the prize",
    title: `Three independent methods put 2030 between ${Math.round(Math.min(...band))}M and ${Math.round(Math.max(...band))}M, and capacity is the binding leg`,
    exhibit: <SizingBand />,
  },
  {
    kicker: "2. The premise reverses",
    title: `India is winning its own market: Indian carriers went ${n1(first.Indian)}% to ${n1(last.Indian)}% while the Gulf fell ${n1(first.Gulf)}% to ${n1(last.Gulf)}%`,
    exhibit: <ShareTrend />,
  },
  {
    kicker: "3. The capability gap",
    title: `IndiGo flies ${n0(indigo.stage_length_km)} km on average against Air India's ${n0(airIndia.stage_length_km)} km. The wide-body order exists to close that`,
    exhibit: <CarrierCapability />,
  },
  {
    kicker: "4. Can the aircraft be absorbed",
    title: `The order book is ${abs.book_vs_growth_ratio.toFixed(2)}x the growth needed to hold share, and clears only at ${Math.round(abs.stage_uplift_pct)}% longer sectors or ${Math.round(abs.share_pct_to_absorb)}% of the market`,
    exhibit: <AbsorptionFrontier />,
  },
  {
    kicker: "5. The Gulf has no room",
    title: `India-Dubai is at ${n1(dubai.utilisation_pct)}% of its entitlement and Abu Dhabi at ${n1(abudhabi.utilisation_pct)}%. Together they absorb about ${Math.round(headroom.pct_of_order_book_absorbed)}% of the order book`,
    body: (
      <div className="mt-10 grid w-full max-w-3xl gap-6">
        {[dubai, abudhabi].map((e) => (
          <div key={e.foreign_point}>
            <div className="flex items-baseline justify-between text-[15px]">
              <span className="font-medium">{e.foreign_point}</span>
              <span className="tnum text-grey">
                {n0(e.implied_seats_per_week)} of {n0(e.reported_entitlement_both_sides)} seats a week
              </span>
            </div>
            <div className="mt-2 h-7 w-full bg-light">
              <div
                className={e.utilisation_pct > 85 ? "h-7 bg-red" : "h-7 bg-grey"}
                style={{ width: `${e.utilisation_pct}%` }}
              />
            </div>
            <p className="tnum mt-1 text-[13px] text-grey">{n1(e.utilisation_pct)}% used</p>
          </div>
        ))}
      </div>
    ),
  },
  {
    kicker: "6. And the worst economics",
    title: `Gulf sectors clear at ${sgn(gulf.yield_headroom_pct!)} yield headroom against Europe at ${sgn(europe.yield_headroom_pct!)}`,
    exhibit: <YieldHeadroom />,
  },
  {
    kicker: "7. The profit pool says the same",
    title: `The Gulf is ${Math.round(gulf.pax_share_pct!)}% of passengers and ${Math.round(gulf.revenue_share_pct!)}% of revenue, the widest gap of any corridor`,
    exhibit: <PaxVsRevenue />,
  },
  {
    kicker: "8. The cost problem",
    title: "The rupee added more to unit cost than the entire net rise, and wide-body obligations are dollar-denominated",
    exhibit: <CaskBridge />,
  },
  {
    kicker: "9. The prize, quantified",
    title: `${n1(vas.connecting_pax_m)}M passengers a year connect through a Gulf hub rather than stopping there, worth INR ${n0(vas.revenue_floor_inr_cr)} to ${n0(vas.revenue_ceiling_inr_cr)} crore`,
    body: (
      <p className="mt-8 max-w-[60ch] text-[17px] leading-relaxed text-ink/75">
        Banded between IndiGo&rsquo;s realised yield and Emirates&rsquo;, because the true
        origin-destination split is sold by IATA rather than published. The band is the honest
        statement of what is knowable, and the gap it rests on is the single likeliest reason
        this case is wrong.
      </p>
    ),
  },
  {
    kicker: "10. The options",
    title: "Only one option is both available this decade and value-creating, and it is not the one that follows the traffic",
    exhibit: <OptionMatrix />,
  },
  {
    kicker: "11. What would break it",
    title: "Nine risks, and the two that are high on both axes are outside the airline's control",
    body: (
      <ul className="mt-8 grid w-full gap-px bg-light sm:grid-cols-3">
        {narrative.risks.slice(0, 6).map((r) => (
          <li key={r.Risk} className="bg-paper p-4">
            <p className="text-[14px] font-semibold leading-snug">{r.Risk}</p>
            <p className="mt-1.5 text-[12px] uppercase tracking-wide text-grey">
              {r.Likelihood} likelihood · {r.Impact} impact
            </p>
            <p className="mt-2 text-[12.5px] leading-snug text-ink/70">{r["Leading indicator"]}</p>
          </li>
        ))}
      </ul>
    ),
  },
  {
    kicker: "The recommendation",
    title: "Compete with the Gulf hubs. Europe first, North America second, Gulf capacity roughly flat",
    body: (
      <ol className="mt-8 grid w-full gap-px bg-light sm:grid-cols-3">
        {[
          {
            phase: "Now",
            what: "Europe direct, where headroom is widest",
            why: `${sgn(europe.yield_headroom_pct!)} headroom and reachable by the committed fleet`,
          },
          {
            phase: "Next",
            what: "North America as deliveries arrive",
            why: "Highest headroom on the map, and only a wide-body reaches it",
          },
          {
            phase: "Hold",
            what: "Gulf capacity roughly flat",
            why: `${n1(dubai.utilisation_pct)}% of entitlement used and negative headroom`,
          },
        ].map((p) => (
          <li key={p.phase} className="bg-paper p-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red">
              {p.phase}
            </p>
            <p className="mt-2 font-serif text-lg font-semibold leading-snug">{p.what}</p>
            <p className="mt-2 text-[13px] leading-relaxed text-ink/70">{p.why}</p>
          </li>
        ))}
      </ol>
    ),
  },
];

export default function Deck() {
  const refs = useRef<(HTMLElement | null)[]>([]);
  const [current, setCurrent] = useState(0);

  const go = useCallback((i: number) => {
    const clamped = Math.max(0, Math.min(SLIDES.length - 1, i));
    refs.current[clamped]?.scrollIntoView({ behavior: "smooth", block: "start" });
    setCurrent(clamped);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const next: Record<string, number> = {
        ArrowRight: current + 1,
        ArrowDown: current + 1,
        PageDown: current + 1,
        " ": current + 1,
        ArrowLeft: current - 1,
        ArrowUp: current - 1,
        PageUp: current - 1,
        Home: 0,
        End: SLIDES.length - 1,
      };
      if (e.key in next) {
        e.preventDefault();
        go(next[e.key]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [current, go]);

  // Which slide is on screen, so the counter is honest when someone scrolls
  // rather than using the keys.
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setCurrent(Number((visible.target as HTMLElement).dataset.index));
      },
      { threshold: [0.5] },
    );
    refs.current.forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <>
      <div className="fixed right-6 bottom-5 z-40 flex items-center gap-3 border border-light bg-paper/95 px-3 py-1.5 text-[13px] backdrop-blur print:hidden">
        <button
          type="button"
          onClick={() => go(current - 1)}
          disabled={current === 0}
          aria-label="Previous slide"
          className="px-1 text-grey hover:text-red disabled:opacity-30"
        >
          &larr;
        </button>
        <span className="tnum">
          {current + 1} / {SLIDES.length}
        </span>
        <button
          type="button"
          onClick={() => go(current + 1)}
          disabled={current === SLIDES.length - 1}
          aria-label="Next slide"
          className="px-1 text-grey hover:text-red disabled:opacity-30"
        >
          &rarr;
        </button>
        <button
          type="button"
          onClick={() => window.print()}
          className="ml-1 border-l border-light pl-3 text-grey hover:text-red"
        >
          Print
        </button>
      </div>

      {/* Flex column, deliberately: a grid container makes Chrome ignore the
          forced page break and the print layout silently collapses. */}
      <div className="flex snap-y snap-mandatory flex-col print:block">
        {SLIDES.map((s, i) => (
          <section
            key={s.title}
            data-index={i}
            ref={(el) => {
              refs.current[i] = el;
            }}
            className="flex min-h-[calc(100svh-49px)] snap-start flex-col justify-center border-b border-light px-8 py-14 print:min-h-0 print:break-after-page print:border-0"
          >
            <div className="mx-auto w-full max-w-[1000px]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
                {s.kicker}
              </p>
              <h2 className="mt-4 max-w-[24ch] font-serif text-[clamp(1.5rem,3.2vw,2.6rem)] font-semibold leading-[1.15]">
                {s.title}
              </h2>
              {s.body}
              {s.exhibit && <div className="mt-8">{s.exhibit}</div>}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
