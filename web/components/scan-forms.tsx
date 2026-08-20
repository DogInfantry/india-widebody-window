"use client";

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { GREY, INK, LIGHT, RED } from "@/lib/chart-theme";
import { corridors, orderBookFleet } from "@/lib/data";

// Four forms the site did not have, added 2026-08-20 after a set of AI-generated
// infographics of this same case were compared against it.
//
// **What the comparison actually showed.** Not colour, and not illustration.
// Form monotony: eleven of the app's twenty charts were bar charts, and there was
// no part-to-whole, no part-of-count and no sequence visual anywhere on the site.
// The infographics changed form on nearly every panel, which is why they scan
// faster, and it had nothing to do with their gradients.
//
// **What was deliberately NOT taken.** The balance scales, padlocks, eyes,
// aircraft illustrations, gradient globes and green-for-good/red-for-bad pairing.
// Green is not in this palette, one red element per exhibit is a rule with a test
// behind it, and the illustration is most of why those images read as marketing
// rather than as a deliverable.
//
// **And the reason to take forms rather than content:** those infographics got
// six numbers wrong about this case. 98.8% where the entitlement figure is 88.8%,
// 33.7M and 35.7M where the Gulf carries 39.7M, -6.3% and -4.2% where headroom is
// -4.3%, RASK 4.95 where it is 4.99, one pane labelling CASK as RASK, and a stage
// length of 2,645 km where it is 2,643. Every number below is read from the
// export, which is the whole point of the export.

const gulf = corridors.find((c) => c.region === "Gulf")!;

/** Part-to-whole, which nothing on the site did.
 *
 *  `corridor_scale` is a bar chart across nine corridors and answers "how do the
 *  corridors compare". It does not answer "how much of India's international
 *  flying touches a Gulf point at all", which is the case's opening fact and is a
 *  share. A share should look like a share. */
export function ShareRing({
  pct = gulf.share_pct,
  caption = "of India's international passengers touch a Gulf point",
  sub,
}: {
  pct?: number;
  caption?: string;
  sub?: string;
}) {
  const data = [
    { name: "share", value: pct },
    { name: "rest", value: 100 - pct },
  ];

  return (
    <figure className="flex flex-wrap items-center gap-x-10 gap-y-4">
      <div className="relative h-[190px] w-[190px] shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              innerRadius={66}
              outerRadius={92}
              startAngle={90}
              endAngle={-270}
              stroke="none"
              isAnimationActive={false}
            >
              <Cell fill={RED} />
              <Cell fill={LIGHT} />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <span className="tnum font-serif text-stat font-semibold leading-none">
            {pct.toFixed(1)}%
          </span>
        </div>
      </div>
      <figcaption className="max-w-[30ch]">
        <p className="text-lead font-medium leading-snug">{caption}</p>
        {sub && <p className="mt-2 text-small leading-relaxed text-grey">{sub}</p>}
      </figcaption>
    </figure>
  );
}

/** Part-of-count, which nothing on the site did either.
 *
 *  The order book is expressed in ASK everywhere else in this project, and that
 *  is correct for the absorption arithmetic: a seat is not capacity until you say
 *  how far and how often it flies. It is useless to a reader. "1.94x the growth
 *  needed" is a ratio nobody pictures and 119.3 billion ASK is a number nobody
 *  has an intuition for. One hundred and forty aeroplanes is a quantity you can
 *  count, and seeing 68 of them with nothing to do is the argument.
 *
 *  The marks are plain squares rather than aircraft silhouettes. A unit mark only
 *  has to be countable, and a drawing of an aeroplane here would be decoration. */
export function OrderBookPictogram() {
  const { total_aircraft, needed_to_hold_share, surplus, book_vs_growth_ratio } = orderBookFleet;
  const perRow = 20;
  const rows = Math.ceil(total_aircraft / perRow);
  const size = 9;
  const gap = 4;
  const w = perRow * (size + gap) - gap;
  const h = rows * (size + gap) - gap;

  return (
    <figure>
      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${w} ${h}`}
          className="w-full min-w-[380px] max-w-[560px]"
          role="img"
          aria-label={`${total_aircraft} wide-body aircraft on firm order. ${needed_to_hold_share} are needed for Indian carriers to hold today's market share; ${surplus} are surplus to it.`}
        >
          {Array.from({ length: total_aircraft }, (_, i) => (
            <rect
              key={i}
              x={(i % perRow) * (size + gap)}
              y={Math.floor(i / perRow) * (size + gap)}
              width={size}
              height={size}
              fill={i < needed_to_hold_share ? LIGHT : RED}
            />
          ))}
        </svg>
      </div>
      <figcaption className="mt-4 flex flex-wrap gap-x-8 gap-y-2 text-small">
        <span className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5" style={{ background: LIGHT }} />
          <span className="tnum">
            <strong>{needed_to_hold_share}</strong> hold today&rsquo;s share
          </span>
        </span>
        <span className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5" style={{ background: RED }} />
          <span className="tnum text-red">
            <strong>{surplus}</strong> are surplus to it
          </span>
        </span>
        <span className="tnum text-grey">
          {total_aircraft} on firm order, {book_vs_growth_ratio.toFixed(2)}x the growth needed
        </span>
      </figcaption>
    </figure>
  );
}

/** The recommendation is a SEQUENCE, and it existed only as a sentence.
 *
 *  "Europe first, North America second, Gulf capacity roughly flat" is the answer
 *  to the case. Order is the whole content of it, and order is the one thing
 *  prose conveys worst and a diagram conveys best. */
const PHASES = [
  {
    n: "1",
    where: "Europe",
    why: `+${corridors.find((c) => c.region === "Europe")!.yield_headroom_pct!.toFixed(1)}% fare headroom`,
    tone: "first" as const,
  },
  {
    n: "2",
    where: "North America",
    why: "Most headroom, smallest market, reachable only by wide-body",
    tone: "second" as const,
  },
  {
    n: "0",
    where: "Gulf, held flat",
    why: `${gulf.yield_headroom_pct!.toFixed(1)}% headroom and bilaterally capped`,
    tone: "hold" as const,
  },
];

export function SequenceRibbon() {
  return (
    <ol className="mt-8 grid gap-px bg-light sm:grid-cols-3">
      {PHASES.map((p) => {
        const first = p.tone === "first";
        return (
          <li
            key={p.where}
            className="bg-paper p-5"
            style={{ borderTop: `3px solid ${first ? RED : p.tone === "second" ? INK : GREY}` }}
          >
            <p className="text-micro font-semibold uppercase tracking-[0.14em] text-grey">
              {p.tone === "hold" ? "Not a move" : `Move ${p.n}`}
            </p>
            <p
              className={`mt-2 font-serif text-h3 font-semibold leading-snug ${
                first ? "text-red" : "text-ink"
              }`}
            >
              {p.where}
            </p>
            <p className="tnum mt-2 text-small leading-relaxed text-grey">{p.why}</p>
          </li>
        );
      })}
    </ol>
  );
}

/** A signed figure whose sign is the point.
 *
 *  Corridor headroom is read as "does this corridor clear its own cost", and a
 *  leading minus sign in body text is the weakest possible way to say no. Red for
 *  adverse and ink for favourable, because green is not in this palette: the
 *  green-up/red-down pairing the infographics use would need a second accent
 *  colour and there is a test that says there is only one. */
export function Delta({ pct, className = "" }: { pct: number; className?: string }) {
  const adverse = pct < 0;
  return (
    <span className={`tnum whitespace-nowrap ${adverse ? "text-red" : "text-ink"} ${className}`}>
      <span aria-hidden>{adverse ? "▼" : "▲"}</span> {adverse ? "" : "+"}
      {pct.toFixed(1)}%
    </span>
  );
}
