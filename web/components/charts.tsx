"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { corridors, economicCorridors, fleet } from "@/lib/data";

// House rules, carried over from src/charts.py and enforced there by tests:
// ONE red element per chart, everything else grey, minimal gridlines, sans
// labels at every size. The red is the point of the exhibit, so it is applied
// by a predicate rather than by a palette cycle.
const RED = "#CC0000";
const GREY = "#999999";
const LIGHT = "#E6E6E6";
const INK = "#1A1A1A";

const AXIS = { stroke: LIGHT, tick: { fill: GREY, fontSize: 12 }, tickLine: false } as const;

const TOOLTIP = {
  contentStyle: {
    border: `1px solid ${LIGHT}`,
    borderRadius: 0,
    fontSize: 13,
    boxShadow: "none",
  },
  labelStyle: { color: INK, fontWeight: 600 },
  cursor: { fill: "#FAFAFA" },
} as const;

/** Corridor scale. The Gulf is the red because the case is about whether the
 *  aircraft should follow it. */
export function CorridorScale() {
  const data = corridors
    .filter((c) => c.region !== "Other")
    .map((c) => ({ region: c.region, pax_m: c.pax_total / 1e6, share: c.share_pct }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 32, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke={LIGHT} />
        <XAxis type="number" {...AXIS} unit="M" />
        <YAxis type="category" dataKey="region" width={104} {...AXIS} />
        <Tooltip
          {...TOOLTIP}
          formatter={(v, _n, item) =>
            `${Number(v).toFixed(1)}M passengers, ${Number(item?.payload?.share).toFixed(1)}% of the market`
          }
        />
        <Bar dataKey="pax_m" isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.region} fill={d.region === "Gulf" ? RED : LIGHT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Yield headroom. Diverging, with zero as the line that matters: below it a
 *  corridor does not cover its own cost at IndiGo's realised yield. */
export function YieldHeadroom() {
  const data = [...economicCorridors]
    .sort((a, b) => a.yield_headroom_pct - b.yield_headroom_pct)
    .map((c) => ({ region: c.region, headroom: c.yield_headroom_pct }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 32, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke={LIGHT} />
        <XAxis type="number" {...AXIS} unit="%" />
        <YAxis type="category" dataKey="region" width={104} {...AXIS} />
        <ReferenceLine x={0} stroke={INK} />
        <Tooltip
          {...TOOLTIP}
          formatter={(v) => `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(1)}% yield headroom`}
        />
        <Bar dataKey="headroom" isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.region} fill={d.region === "Gulf" ? RED : LIGHT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** The absorption frontier: what share of the market Indian carriers would have
 *  to hold, at each average sector length, for the order book to clear. */
export function AbsorptionFrontier() {
  const frontier = fleet.absorption_frontier;
  const summary = fleet.absorption_summary;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={frontier} margin={{ left: 8, right: 24, top: 8, bottom: 4 }}>
        <CartesianGrid stroke={LIGHT} vertical={false} />
        <XAxis
          dataKey="share_pct"
          {...AXIS}
          unit="%"
          label={{
            value: "Indian carrier share of the market",
            position: "insideBottom",
            offset: -2,
            fill: GREY,
            fontSize: 12,
          }}
        />
        <YAxis {...AXIS} width={64} tickFormatter={(v: number) => `${(v / 1000).toFixed(1)}k`} />
        <ReferenceLine
          x={Math.round(summary.share_held_pct)}
          stroke={GREY}
          strokeDasharray="4 3"
          label={{ value: "share held today", fill: GREY, fontSize: 11, position: "top" }}
        />
        <Tooltip
          {...TOOLTIP}
          formatter={(v) => `${Number(v).toLocaleString()} km average sector needed`}
          labelFormatter={(v) => `At ${v}% market share`}
        />
        <Line
          type="monotone"
          dataKey="required_stage_km"
          stroke={RED}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
