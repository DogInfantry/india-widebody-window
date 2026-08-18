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
import { CapitalScale, MarginLadder, UnitSpread } from "@/components/company-charts";
import {
  EntitlementUse,
  FleetGap,
  GatewayFlows,
  ProfitPool,
  Scenarios,
  ValueAtStake,
} from "@/components/restored-charts";
import {
  access,
  brief,
  carriers,
  company,
  corridors,
  economics,
  fleet,
  kpis,
  market,
  narrative,
} from "@/lib/data";

// A deck that can be put on a screen in front of a client: a cover naming the
// client and the decision, an agenda, an executive summary carrying the SCQA,
// section dividers, page numbers and a source line on every slide.
//
// **Two paths through one deck.** Every slide declares whether it belongs to the
// five-minute path or only to the fifteen. The control filters between them
// rather than hiding a short version in a second file, so there is one deck and
// no chance of the short one going stale. Backup exhibits sit in an appendix
// after the recommendation, which is where a partner expects to find them.
//
// **Presenter notes** are per slide, toggled with N, and always printed on the
// handout. A deck with no notes is a deck only its author can give.
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
const spread = company.spread;
const cap = company.capital_scale;
const reported = company.margin_ladder.find(
  (r) => r.year === "FY2026" && r.basis === "As reported",
)!;
const exforex = company.margin_ladder.find(
  (r) => r.year === "FY2026" && r.basis === "Excluding forex",
)!;
// Computed. This read "between 96M and 109M" as a literal for one commit.
const band = market.triangulation.estimates
  .map((e) => e.value_m)
  .filter((v): v is number => v !== null);

const n1 = (x: number) => x.toFixed(1);
const n0 = (x: number) => Math.round(x).toLocaleString();
const sgn = (x: number) => `${x > 0 ? "+" : ""}${x.toFixed(1)}%`;

const SRC_DGCA =
  "DGCA monthly traffic statistics, computed in-repo. Full provenance in data/data_dictionary.md.";
const SRC_INDIGO =
  "IndiGo FY2026 results release and Annual Report FY26, verified in data/manual/assumptions.csv.";

type Slide = {
  kicker: string;
  title: string;
  body?: React.ReactNode;
  exhibit?: React.ReactNode;
  /** Every content slide carries one. A slide with no source is an assertion. */
  source?: string;
  /** What to say while it is on screen. */
  notes?: string;
  /** Slides in the short path are also in the long one. */
  short?: boolean;
  kind?: "cover" | "divider" | "appendix";
};

const AGENDA = [
  "The decision, and the answer",
  "Where the volume is, and where it disappears",
  "Why the aircraft cannot follow it",
  "The client's own starting position",
  "What to do, and what would break it",
];

const SLIDES: Slide[] = [
  // ------------------------------------------------------------------ cover
  {
    kind: "cover",
    kicker: "Commercial aviation · Network and fleet strategy",
    title: "India's Wide-Body Window",
    short: true,
    body: (
      <div className="mt-10 max-w-[62ch]">
        <p className="font-serif text-[clamp(1.15rem,2.2vw,1.6rem)] leading-snug text-ink/75">
          Where should Indian carriers deploy their next 100 long-haul aircraft, and can the
          India-Gulf corridor absorb them?
        </p>
        <dl className="mt-10 grid gap-x-10 gap-y-4 border-t border-light pt-6 sm:grid-cols-2">
          {[
            ["Client", brief.client],
            ["The decision", brief.decision],
            ["Horizon", brief.timeframe],
            ["Against", "Air India, 80 wide-bodies on firm order"],
          ].map(([term, value]) => (
            <div key={term}>
              <dt className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
                {term}
              </dt>
              <dd className="mt-1 text-[14px] leading-snug">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    ),
    notes:
      "Open on the client and the decision, not on the market. The audience is IndiGo network and fleet strategy, and the question is where the first tranche of sixty firm A350s goes. Say up front that this is a portfolio simulation, not a commissioned engagement.",
    source: "A self-directed case. IndiGo has not commissioned, seen or endorsed any of it.",
  },
  {
    kicker: "Agenda",
    title: "Five moves, and the answer is in the first one",
        body: (
      <ol className="mt-10 max-w-[62ch] space-y-4">
        {AGENDA.map((item, i) => (
          <li key={item} className="flex gap-5 border-b border-light pb-4">
            <span className="tnum font-serif text-2xl font-semibold text-red">
              {String(i + 1).padStart(2, "0")}
            </span>
            <span className="self-center text-[16px]">{item}</span>
          </li>
        ))}
      </ol>
    ),
    notes:
      "Answer first, always. If they only hear the next slide, they have the recommendation and the three reasons behind it.",
  },

  // ---------------------------------------------------- executive summary
  {
    kicker: "Executive summary",
    title: "Compete with the Gulf hubs. Do not fly more aircraft to them",
    short: true,
    body: (
      <div className="mt-8 grid w-full gap-px bg-light lg:grid-cols-4">
        {(["situation", "complication", "question", "answer"] as const).map((part) => (
          <div key={part} className="bg-paper p-5">
            <p className="font-serif text-[15px] font-semibold capitalize text-red">{part}</p>
            <p className="mt-2 text-[13.5px] leading-relaxed text-ink/80">{brief.scqa[part][0]}</p>
          </div>
        ))}
      </div>
    ),
    notes:
      "Europe first, North America second, Gulf capacity roughly flat. Three lines of evidence force it: no treaty room, the worst unit economics on the map, and an order book sized for a longer network. This used to say the opposite and it is recorded as pivot 1.",
    source: "Storyline and recommendation, docs/storyline.md and docs/recommendation.md.",
  },
  {
    kicker: "The case in six numbers",
    title: "Every figure in this deck is computed in-repo from DGCA, Eurostat and World Bank data",
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
    notes:
      "If someone challenges a number, every one of these traces to a module function in one click. Twenty-five of thirty-one hand-entered values cleared a verification gate; the six that did not are named on the methodology page.",
    source: SRC_DGCA,
  },

  // -------------------------------------------------------------- section 1
  {
    kind: "divider",
    kicker: "01",
    title: "Where the volume is, and where it disappears",
    short: true,
  },
  {
    kicker: "1. Size the prize",
    title: `Half of India's international traffic touches the Gulf, ${n1(gulf.pax_total / europe.pax_total)}x the entire direct Europe market`,
    exhibit: <CorridorScale />,
    short: true,
    source: SRC_DGCA,
    notes:
      "Nothing below weakens this. The corridor is real and it is the largest thing on the map. What changes is the conclusion drawn from it.",
  },
  {
    kicker: "1. Size the prize",
    title: "India's own statistics lose sight of the passenger at the Gulf hub",
    exhibit: <GatewayFlows />,
    short: true,
    source: SRC_DGCA,
    notes:
      "DGCA records the first foreign point and nothing beyond. Delhi to Dubai to London is counted as a passenger to the UAE. This blind spot is not an apology, it is the finding.",
  },
  {
    kicker: "1. Size the prize",
    title: `${n1(vas.connecting_pax_m)}M passengers a year connect through a Gulf hub rather than stopping there, worth INR ${n0(vas.revenue_floor_inr_cr)} to ${n0(vas.revenue_ceiling_inr_cr)} crore`,
    exhibit: <ValueAtStake />,
    short: true,
    source:
      "Computed in src/options.py, banded between IndiGo's and Emirates' verified yields. Modelled.",
    notes:
      "A third to two thirds of IndiGo's entire annual revenue, in a pool it does not currently compete for. Be honest that the origin-destination share underneath it cannot be verified: IATA sells that data. It is the single likeliest reason this case is wrong.",
  },
  {
    kicker: "1. Size the prize",
    title: `Three independent methods put 2030 between ${Math.round(Math.min(...band))}M and ${Math.round(Math.max(...band))}M, and capacity is the binding leg`,
    exhibit: <SizingBand />,
    source: "Computed in src/market_sizing.py. Reported as a band; the average is never drawn.",
    notes:
      "Verifying the gated inputs added the LOW leg, so the band widened downward and the recommendation got harder to argue. A gate that only ever unlocks good news is not a gate.",
  },
  {
    kicker: "1. Size the prize",
    title: "Every demand path, including the pessimistic one, needs materially more long-haul capacity",
    exhibit: <Scenarios />,
    source: "Computed in src/scenario.py.",
    notes:
      "The spread between bear and bull is 27 million passengers and every path needs the aircraft. The argument does not rest on optimism.",
  },

  // -------------------------------------------------------------- section 2
  {
    kind: "divider",
    kicker: "02",
    title: "Why the aircraft cannot follow it",
    short: true,
  },
  {
    kicker: "2. The premise reverses",
    title: `India is winning its own market: Indian carriers went ${n1(first.Indian)}% to ${n1(last.Indian)}% while the Gulf fell ${n1(first.Gulf)}% to ${n1(last.Gulf)}%`,
    exhibit: <ShareTrend />,
    source: SRC_DGCA,
    notes:
      "Most versions of this question assume India is losing and needs rescuing. It is not. Correcting the premise is what makes the rest of the recommendation defensible, and it only surfaced after a GRAND TOTAL row worth 17.5M passengers was found being counted as a foreign airline.",
  },
  {
    kicker: "3. The capability gap",
    title: `IndiGo flies ${n0(indigo.stage_length_km)} km on average against Air India's ${n0(airIndia.stage_length_km)} km. The wide-body order exists to close that`,
    exhibit: <CarrierCapability />,
        source: SRC_DGCA,
    notes:
      "Neither airline is doing anything wrong. They are in different businesses, and the order is IndiGo buying into the second one.",
  },
  {
    kicker: "4. Can the aircraft be absorbed",
    title: `The order book is ${abs.book_vs_growth_ratio.toFixed(2)}x the growth needed to hold share, and clears only at ${Math.round(abs.stage_uplift_pct)}% longer sectors or ${Math.round(abs.share_pct_to_absorb)}% of the market`,
    exhibit: <AbsorptionFrontier />,
    short: true,
    source: "Computed in src/fleet_gap.py. Capacity in ASK, not seats.",
    notes:
      "These aircraft are not bought to carry more of the same traffic. They are bought to carry it further. That is the recommendation restated in capacity terms.",
  },
  {
    kicker: "5. The Gulf has no room",
    title: `India-Dubai is at ${n1(dubai.utilisation_pct)}% of its entitlement and Abu Dhabi at ${n1(abudhabi.utilisation_pct)}%. Together they absorb about ${Math.round(headroom.pct_of_order_book_absorbed)}% of the order book`,
    exhibit: <EntitlementUse />,
    short: true,
    source: "Computed in src/benchmarking.py. Entitlements are UNVERIFIED_NO_PRIMARY.",
    notes:
      "Say the caveat out loud: India publishes no entitlement table, so both figures are corroborated rather than verified. Abu Dhabi at 70% is why we do not claim the Gulf is uniformly capped. Never quote 66,504 as the India-UAE cap; that is one emirate and one side.",
  },
  {
    kicker: "6. And the worst economics",
    title: `Gulf sectors clear at ${sgn(gulf.yield_headroom_pct!)} yield headroom against Europe at ${sgn(europe.yield_headroom_pct!)}`,
    exhibit: <YieldHeadroom />,
    short: true,
    source: "Computed in src/options.py. CASK_STAGE_ELASTICITY = -0.25, a labelled modelled knob.",
    notes:
      "Headroom, not a breakeven against flat yield: yield per kilometre falls with stage length, so holding it constant flatters long-haul. There is no NPV anywhere in this project, and the reason is the same.",
  },
  {
    kicker: "7. The profit pool says the same",
    title: `The Gulf is ${Math.round(gulf.pax_share_pct!)}% of passengers and ${Math.round(gulf.revenue_share_pct!)}% of revenue, the widest gap of any corridor`,
    exhibit: <ProfitPool />,
    source: "Computed in src/profit_pools.py. Margin axis is modelled and labelled as such.",
    notes:
      "Two unrelated routes reach the same ordering: this models margin up from an EBITDAR anchor, the headroom chart scales cost down from a published CASK. They share nothing but the corridor distances.",
  },

  // -------------------------------------------------------------- section 3
  {
    kind: "divider",
    kicker: "03",
    title: "The client's own starting position",
    short: true,
  },
  {
    kicker: "8. The starting point",
    title: `IndiGo did not cover its unit cost in ${spread.year}: RASK ${spread.rask.toFixed(2)} against CASK ${spread.cask.toFixed(2)}`,
    exhibit: <UnitSpread />,
    short: true,
    source: SRC_INDIGO,
    notes:
      "This is the sharpest number in the case and it is about the client, not the market. One paisa per seat kilometre, on the wrong side. It is why the sequencing has to be right: there is no margin cushion under a commitment this size.",
  },
  {
    kicker: "8. The starting point",
    title: `Both FY2026 margins are true: ${reported.margin_pct.toFixed(1)}% as reported against ${exforex.margin_pct.toFixed(1)}% excluding forex`,
    exhibit: <MarginLadder />,
    source: SRC_INDIGO,
    notes:
      "Publish both, always. This project once claimed the operating margin had halved, from a convention the company does not publish, and had to retract it. Quoting only the flattering ex-forex figure is the same error pointing the other way.",
  },
  {
    kicker: "9. The cost problem",
    title: "The rupee added more to unit cost than the entire net rise, and wide-body obligations are dollar-denominated",
    exhibit: <CaskBridge />,
        source: SRC_INDIGO,
    notes:
      "Fuel fell. Real non-fuel inflation was 0.11. Currency added 0.41 against a net rise of 0.34. The exposure gets worse exactly where the capacity is being added.",
  },
  {
    kicker: "10. The size of the commitment",
    title: `The sixty A350s would produce revenue equal to ${cap.pct_of_fy2026_revenue.toFixed(0)}% of the entire FY2026 top line`,
    exhibit: <CapitalScale />,
    source: SRC_INDIGO,
    notes:
      "Scale, not financing. No aircraft price appears anywhere: list prices are not transaction prices and transaction prices are confidential. If asked about funding, say financing is explicitly out of scope and the lease-rate data that would settle it is paywalled.",
  },

  // -------------------------------------------------------------- section 4
  {
    kind: "divider",
    kicker: "04",
    title: "What to do, and what would break it",
    short: true,
  },
  {
    kicker: "11. The options",
    title: "Only one option is both available this decade and value-creating, and it is not the one that follows the traffic",
    exhibit: <OptionMatrix />,
    short: true,
    source: "Option menu parsed from docs/recommendation.md rather than retyped.",
    notes:
      "The damp-lease bridge is genuinely unquantified and says so. That is the largest open input in the project.",
  },
  {
    kicker: "12. What would break it",
    title: "Nine risks, and the two that are high on both axes are outside the airline's control",
        body: (
      <ul className="mt-8 grid w-full gap-px bg-light sm:grid-cols-3">
        {narrative.risks.slice(0, 6).map((r) => (
          <li key={r.Risk} className="bg-paper p-4">
            <p className="text-[14px] font-semibold leading-snug">{r.Risk}</p>
            <p className="mt-1.5 text-[12px] uppercase tracking-wide text-grey">
              {r.Likelihood} likelihood &middot; {r.Impact} impact
            </p>
            <p className="mt-2 text-[12.5px] leading-snug text-ink/70">{r["Leading indicator"]}</p>
          </li>
        ))}
      </ul>
    ),
    source: "Risk register parsed from docs/recommendation.md. Nine rows in full there.",
    notes:
      "Every row carries what would falsify it and the leading indicator that moves first. A risk register without a falsifier is a list of worries.",
  },
  {
    kicker: "The recommendation",
    title: "Compete with the Gulf hubs. Europe first, North America second, Gulf capacity roughly flat",
    short: true,
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
    source: "Full roadmap, WWHTBT and leading indicators in docs/recommendation.md.",
    notes:
      "Close here in the five-minute version. Everything after this is appendix and only comes out if asked.",
  },

  // -------------------------------------------------------------- appendix
  {
    kind: "divider",
    kicker: "Appendix",
    title: "Backup exhibits",
  },
  {
    kind: "appendix",
    kicker: "Backup",
    title: `The Gulf carries ${Math.round(gulf.pax_share_pct!)}% of passengers on ${Math.round(gulf.revenue_share_pct!)}% of revenue, with no margin assumption at all`,
    exhibit: <PaxVsRevenue />,
    source: "Passengers, great circle distances and one published yield. src/profit_pools.py.",
    notes:
      "Use this if someone rejects the modelled margin axis. It carries the same point with nothing modelled in it.",
  },
  {
    kind: "appendix",
    kicker: "Backup",
    title: "Timing changes when the shortfall lands, not whether the order book is enough",
    exhibit: <FleetGap />,
    source: "Computed in src/fleet_gap.py. No primary source states a delivery schedule.",
    notes:
      "For the phasing question. The shape is the same on all three delivery starts, which is why the question is what to fly in the bridge years.",
  },
];

const CONTENT_KINDS = new Set([undefined, "appendix"]);

export default function Deck() {
  const refs = useRef<(HTMLElement | null)[]>([]);
  const [current, setCurrent] = useState(0);
  const [showNotes, setShowNotes] = useState(false);
  const [shortPath, setShortPath] = useState(false);

  // Dividers are wayfinding for a long walk-through. In the five-minute path
  // they would be four of ten slides, so the short path drops them.
  const slides = shortPath
    ? SLIDES.filter((s) => s.short && s.kind !== "divider")
    : SLIDES;

  const go = useCallback(
    (i: number) => {
      const clamped = Math.max(0, Math.min(slides.length - 1, i));
      refs.current[clamped]?.scrollIntoView({ behavior: "smooth", block: "start" });
      setCurrent(clamped);
    },
    [slides.length],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "n" || e.key === "N") {
        setShowNotes((v) => !v);
        return;
      }
      const next: Record<string, number> = {
        ArrowRight: current + 1,
        ArrowDown: current + 1,
        PageDown: current + 1,
        " ": current + 1,
        ArrowLeft: current - 1,
        ArrowUp: current - 1,
        PageUp: current - 1,
        Home: 0,
        End: slides.length - 1,
      };
      if (e.key in next) {
        e.preventDefault();
        go(next[e.key]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [current, go, slides.length]);

  // Which slide is on screen, so the counter is honest when someone scrolls
  // rather than using the keys.
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setCurrent(Number((visible.target as HTMLElement).dataset.index));
      },
      { threshold: [0.5] },
    );
    refs.current.forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, [shortPath]);

  return (
    <>
      <div className="fixed right-6 bottom-5 z-40 flex items-center gap-3 border border-light bg-paper/95 px-3 py-1.5 text-[13px] backdrop-blur print:hidden">
        <button
          type="button"
          onClick={() => {
            setShortPath((v) => !v);
            setCurrent(0);
          }}
          aria-pressed={shortPath}
          title="Switch between the five-minute and fifteen-minute paths"
          className={shortPath ? "font-medium text-red" : "text-grey hover:text-red"}
        >
          {shortPath ? "5 min" : "15 min"}
        </button>
        <button
          type="button"
          onClick={() => setShowNotes((v) => !v)}
          aria-pressed={showNotes}
          title="Presenter notes (N)"
          className={showNotes ? "border-l border-light pl-3 font-medium text-red" : "border-l border-light pl-3 text-grey hover:text-red"}
        >
          Notes
        </button>
        <span className="flex items-center gap-2 border-l border-light pl-3">
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
            {current + 1} / {slides.length}
          </span>
          <button
            type="button"
            onClick={() => go(current + 1)}
            disabled={current === slides.length - 1}
            aria-label="Next slide"
            className="px-1 text-grey hover:text-red disabled:opacity-30"
          >
            &rarr;
          </button>
        </span>
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
        {slides.map((s, i) => {
          const divider = s.kind === "divider";
          const cover = s.kind === "cover";
          // Dividers and the cover are not numbered as content pages, which is
          // how a printed deck normally counts itself.
          const page = slides.slice(0, i + 1).filter((x) => CONTENT_KINDS.has(x.kind)).length;

          return (
            <section
              key={s.title}
              data-index={i}
              ref={(el) => {
                refs.current[i] = el;
              }}
              className={`flex min-h-[calc(100svh-49px)] snap-start flex-col justify-center border-b border-light px-8 py-14 print:min-h-0 print:break-after-page print:border-0 ${
                divider ? "bg-wash" : ""
              }`}
            >
              <div className="mx-auto flex w-full max-w-[1000px] flex-1 flex-col justify-center">
                <p
                  className={`text-[11px] font-semibold uppercase tracking-[0.14em] ${
                    divider ? "text-red" : "text-grey"
                  }`}
                >
                  {s.kicker}
                </p>
                <h2
                  className={`mt-4 font-serif font-semibold leading-[1.15] ${
                    cover
                      ? "max-w-[18ch] text-[clamp(2.2rem,6vw,4rem)]"
                      : divider
                        ? "max-w-[20ch] text-[clamp(1.8rem,4.4vw,3rem)]"
                        : "max-w-[24ch] text-[clamp(1.5rem,3.2vw,2.6rem)]"
                  }`}
                >
                  {s.title}
                </h2>
                {s.body}
                {s.exhibit && <div className="mt-8 overflow-x-auto">{s.exhibit}</div>}
              </div>

              {/* Footer strip: source on the left, page number on the right.
                  Every content slide has both, which is what makes the deck
                  checkable rather than merely confident. */}
              {!divider && (
                <div className="mx-auto mt-8 flex w-full max-w-[1000px] items-end justify-between gap-8 border-t border-light pt-3">
                  <p className="max-w-[80ch] text-[11.5px] leading-relaxed text-grey">
                    {s.source ?? " "}
                  </p>
                  {/* A cover is not page one. Numbering starts at the agenda,
                      which is how a printed deck normally counts itself. */}
                  {!cover && (
                    <span className="tnum shrink-0 text-[11.5px] text-grey">{page}</span>
                  )}
                </div>
              )}

              {s.notes && (
                <div
                  className={`mx-auto mt-4 w-full max-w-[1000px] border-l-2 border-red bg-wash py-3 pl-4 pr-4 print:block ${
                    showNotes ? "" : "hidden"
                  }`}
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
                    Presenter note
                  </p>
                  <p className="mt-1.5 max-w-[86ch] text-[13px] leading-relaxed text-ink/80">
                    {s.notes}
                  </p>
                </div>
              )}
            </section>
          );
        })}
      </div>
    </>
  );
}
