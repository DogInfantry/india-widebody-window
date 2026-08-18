"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  LabelList,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { corridors, economicCorridors, scenarioCube } from "@/lib/data";

// The Detail level. Two interaction patterns and no more, which is the cap
// Vizro's method sets before a page stops being legible: cross-filter (click a
// corridor anywhere, every exhibit follows) and one parameter (the fuel and
// currency shock).
//
// The filter-state bar and the one-click reset are Superset's rules: the same
// interaction behaves the same way everywhere, what is filtered is always
// visible, and one click returns to the start.
//
// The shock control indexes a cube precomputed in Python. Nothing here does
// model arithmetic, so this page cannot disagree with the report.

const RED = "#CC0000";
const GREY = "#999999";
const LIGHT = "#E6E6E6";
const INK = "#1A1A1A";
const AXIS = { stroke: LIGHT, tick: { fill: GREY, fontSize: 12 }, tickLine: false } as const;
const TOOLTIP = {
  contentStyle: { border: `1px solid ${LIGHT}`, borderRadius: 0, fontSize: 13, boxShadow: "none" },
  labelStyle: { color: INK, fontWeight: 600 },
  cursor: { fill: "#FAFAFA" },
} as const;

const PLOTTABLE = corridors.filter((c) => c.region !== "Other");
const MOVES = [...new Set(scenarioCube.fuel_fx.map((r) => r.move_pct))].sort((a, b) => a - b);

function Panel({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border border-light p-5">
      <h2 className="max-w-[42ch] text-[15px] font-semibold leading-snug">{title}</h2>
      {hint && <p className="mt-1 text-[12px] text-grey">{hint}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function Dashboard() {
  const [selected, setSelected] = useState<string[]>([]);
  const [moveIdx, setMoveIdx] = useState(() => MOVES.indexOf(0) >= 0 ? MOVES.indexOf(0) : 0);

  const move = MOVES[moveIdx];
  const shock = scenarioCube.fuel_fx.find((r) => r.move_pct === move)!;
  const isOn = (region: string) => selected.length === 0 || selected.includes(region);

  // Cross-filter. Clicking a corridor in ANY exhibit toggles it here, and every
  // exhibit reads from the same state, so the behaviour is identical wherever
  // the click happens.
  const toggle = (region: string) =>
    setSelected((prev) =>
      prev.includes(region) ? prev.filter((r) => r !== region) : [...prev, region],
    );

  const shown = useMemo(() => PLOTTABLE.filter((c) => isOn(c.region)), [selected]);

  const totals = useMemo(() => {
    const pax = shown.reduce((s, c) => s + c.pax_total, 0);
    const rev = shown.reduce((s, c) => s + (c.revenue_inr_cr ?? 0), 0);
    const freight = shown.reduce((s, c) => s + (c.freight_t ?? 0), 0);
    const withEcon = shown.filter((c) => c.yield_headroom_pct !== null);
    const worst = withEcon.length
      ? withEcon.reduce((a, b) => (a.yield_headroom_pct! < b.yield_headroom_pct! ? a : b))
      : null;
    return { pax, rev, freight, worst, count: shown.length };
  }, [shown]);

  // LIGHT for bars, which have area. GREY for scatter marks, which do not: a
  // #E6E6E6 point on a white page is invisible.
  const fill = (region: string) =>
    selected.includes(region) ? RED : selected.length === 0 && region === "Gulf" ? RED : LIGHT;
  const markFill = (region: string) =>
    selected.includes(region) ? RED : selected.length === 0 && region === "Gulf" ? RED : GREY;

  return (
    <div className="mx-auto grid max-w-[1180px] gap-8 px-8 py-10 lg:grid-cols-[220px_1fr]">
      {/* Tier 2: page-level controls, in the left panel where the method puts them. */}
      <aside className="lg:sticky lg:top-20 lg:self-start">
        <h1 className="font-serif text-2xl font-semibold">Dashboard</h1>
        <p className="mt-2 text-[13px] leading-relaxed text-grey">
          Click a corridor to filter every exhibit. Move the shock to see what fuel and the
          rupee do to the spread.
        </p>

        <fieldset className="mt-6">
          <legend className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
            Corridor
          </legend>
          <div className="mt-3 flex flex-wrap gap-1.5 lg:flex-col lg:items-start">
            {PLOTTABLE.map((c) => (
              <button
                key={c.region}
                type="button"
                onClick={() => toggle(c.region)}
                aria-pressed={selected.includes(c.region)}
                className={`border px-2.5 py-1 text-[13px] transition-colors focus-visible:outline-2 focus-visible:outline-red ${
                  selected.includes(c.region)
                    ? "border-red bg-red text-paper"
                    : "border-light text-ink hover:border-grey"
                }`}
              >
                {c.region}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset className="mt-8">
          <legend className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
            Fuel and currency shock
          </legend>
          <input
            type="range"
            min={0}
            max={MOVES.length - 1}
            value={moveIdx}
            onChange={(e) => setMoveIdx(Number(e.target.value))}
            aria-label="Fuel and currency shock, per cent"
            className="mt-3 w-full accent-[#CC0000]"
          />
          <p className="tnum mt-1 text-[13px]">
            {move > 0 ? "+" : ""}
            {move}% move
          </p>
        </fieldset>
      </aside>

      <main>
        {/* Filter state, always visible, one click to clear. */}
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-light pb-3 text-[13px]">
          <span className="text-grey">Showing</span>
          <span className="font-medium">
            {selected.length === 0 ? "all nine corridors" : selected.join(", ")}
          </span>
          {selected.length > 0 && (
            <button
              type="button"
              onClick={() => setSelected([])}
              className="text-red underline underline-offset-4 hover:no-underline"
            >
              Clear all filters
            </button>
          )}
        </div>

        <section aria-label="Filtered totals" className="mt-5 grid gap-px bg-light sm:grid-cols-4">
          {[
            { v: `${(totals.pax / 1e6).toFixed(1)}M`, l: "passengers a year" },
            {
              v: `INR ${Math.round(totals.rev / 1000).toLocaleString()}k cr`,
              l: "corridor revenue pool",
            },
            {
              v: totals.worst ? `${totals.worst.yield_headroom_pct!.toFixed(1)}%` : "n/a",
              l: totals.worst ? `least headroom: ${totals.worst.region}` : "no economics",
            },
            { v: `${Math.round(totals.freight / 1000).toLocaleString()}kt`, l: "belly freight" },
          ].map((k) => (
            <div key={k.l} className="bg-paper px-4 py-4">
              <p className="tnum font-serif text-2xl font-semibold text-red">{k.v}</p>
              <p className="mt-1 text-[12.5px] leading-snug text-ink/70">{k.l}</p>
            </div>
          ))}
        </section>

        <div className="mt-6 grid gap-5 xl:grid-cols-2">
          <Panel
            title="The Gulf is half the traffic and under a third of the revenue"
            hint="Click a bar to filter every exhibit"
          >
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={shown} layout="vertical" margin={{ left: 4, right: 24 }}>
                <CartesianGrid horizontal={false} stroke={LIGHT} />
                <XAxis type="number" {...AXIS} unit="%" />
                <YAxis type="category" dataKey="region" width={100} {...AXIS} />
                <Tooltip
                  {...TOOLTIP}
                  formatter={(v, n) => `${Number(v).toFixed(1)}% of ${n === "share_pct" ? "passengers" : "revenue"}`}
                />
                <Bar dataKey="share_pct" isAnimationActive={false} onClick={(d) => toggle((d as unknown as { region: string }).region)}>
                  {shown.map((c) => (
                    <Cell key={c.region} fill={fill(c.region)} cursor="pointer" />
                  ))}
                </Bar>
                <Bar dataKey="revenue_share_pct" isAnimationActive={false} fill={GREY} />
              </BarChart>
            </ResponsiveContainer>
          </Panel>

          <Panel
            title="Yield headroom falls to nothing on the shortest corridors, and the Gulf is one of them"
            hint="Below the line a corridor does not cover its cost at IndiGo's realised yield"
          >
            <ResponsiveContainer width="100%" height={260}>
              <ScatterChart margin={{ left: 4, right: 24, top: 8, bottom: 16 }}>
                <CartesianGrid stroke={LIGHT} />
                <XAxis
                  type="number"
                  dataKey="stage_km"
                  {...AXIS}
                  name="stage"
                  label={{ value: "average sector, km", position: "insideBottom", offset: -8, fill: GREY, fontSize: 12 }}
                />
                <YAxis type="number" dataKey="yield_headroom_pct" {...AXIS} unit="%" width={56} />
                <ZAxis type="number" dataKey="pax_total" range={[40, 420]} />
                <ReferenceLine y={0} stroke={INK} />
                <Tooltip
                  {...TOOLTIP}
                  formatter={(v, n) => (n === "yield_headroom_pct" ? `${Number(v).toFixed(1)}% headroom` : `${Number(v).toLocaleString()} km`)}
                  labelFormatter={() => ""}
                />
                <Scatter
                  data={economicCorridors.filter((c) => isOn(c.region))}
                  isAnimationActive={false}
                  onClick={(d) => toggle((d as unknown as { region: string }).region)}
                >
                  {economicCorridors
                    .filter((c) => isOn(c.region))
                    .map((c) => (
                      <Cell key={c.region} fill={markFill(c.region)} cursor="pointer" />
                    ))}
                  <LabelList dataKey="region" position="top" offset={8} fontSize={11} fill={INK} />
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </Panel>

          <Panel
            // The title states what is true AT THE CURRENT CONTROL POSITION. A
            // fixed claim here would have read "currency costs more spread than
            // fuel" at zero shock, where both are zero and the claim is false.
            // An action title that a control can falsify is worse than a topic
            // title, because it is asserted with confidence.
            title={
              move === 0
                ? "At no shock, the spread is what the airline actually reported"
                : `At a ${move > 0 ? "+" : ""}${move}% move, ${
                    Math.abs(shock.fx_shock_spread) > Math.abs(shock.fuel_shock_spread)
                      ? "currency costs more spread than fuel does"
                      : "fuel costs more spread than currency does"
                  }`
            }
            hint="Every value is precomputed in Python; the control indexes it, it does not calculate"
          >
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={scenarioCube.fuel_fx} margin={{ left: 4, right: 24, top: 8 }}>
                <CartesianGrid stroke={LIGHT} vertical={false} />
                <XAxis dataKey="move_pct" {...AXIS} unit="%" />
                <YAxis {...AXIS} width={56} />
                <ReferenceLine x={move} stroke={INK} strokeDasharray="4 3" />
                <Tooltip {...TOOLTIP} formatter={(v, n) => `${Number(v).toFixed(2)} INR/ASK (${n})`} />
                <Line dataKey="fuel_shock_spread" stroke={GREY} strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line dataKey="fx_shock_spread" stroke={RED} strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
            <p className="tnum mt-3 text-[13px] text-ink/70">
              Fuel spread {shock.fuel_shock_spread.toFixed(2)} against currency{" "}
              {shock.fx_shock_spread.toFixed(2)} INR per ASK.
            </p>
          </Panel>

          <Panel title="Belly freight does not follow stage length, so it does not argue for long-haul on its own">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={shown.filter((c) => c.kg_per_pax !== null)} margin={{ left: 4, right: 16, bottom: 4 }}>
                <CartesianGrid stroke={LIGHT} vertical={false} />
                <XAxis dataKey="region" {...AXIS} interval={0} angle={-25} textAnchor="end" height={64} />
                <YAxis {...AXIS} width={48} unit="kg" />
                <Tooltip {...TOOLTIP} formatter={(v) => `${Number(v).toFixed(1)} kg per passenger`} />
                <Bar dataKey="kg_per_pax" isAnimationActive={false} onClick={(d) => toggle((d as unknown as { region: string }).region)}>
                  {shown
                    .filter((c) => c.kg_per_pax !== null)
                    .map((c) => (
                      <Cell key={c.region} fill={fill(c.region)} cursor="pointer" />
                    ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Panel>
        </div>
      </main>
    </div>
  );
}
