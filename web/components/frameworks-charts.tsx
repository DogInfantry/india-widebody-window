"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ErrorBar,
  Label,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { carriers, corridors, market, narrative, scenarioCube } from "@/lib/data";

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

/** 1. Market sizing. Three independent methods, reported as a band. The house
 *  rule is that the spread IS the output, so the average is never drawn. */
export function SizingBand() {
  const data = market.triangulation.estimates
    .filter((e) => e.value_m !== null)
    .map((e) => ({ method: e.method, value: e.value_m as number }));
  const lowest = Math.min(...data.map((d) => d.value));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 40 }}>
        <CartesianGrid horizontal={false} stroke={LIGHT} />
        <XAxis type="number" domain={[0, "dataMax + 10"]} {...AXIS} unit="M" />
        <YAxis type="category" dataKey="method" width={96} {...AXIS} />
        <ReferenceLine x={market.triangulation.base_m} stroke={INK} strokeDasharray="4 3">
          <Label value="2025 actual" position="top" fill={INK} fontSize={11} />
        </ReferenceLine>
        <Tooltip {...TOOLTIP} formatter={(v) => `${Number(v).toFixed(1)}M passengers by 2030`} />
        <Bar dataKey="value" isAnimationActive={false}>
          {data.map((d) => (
            // The binding leg is the red one: capacity is the method that
            // produces the low end, and the low end is what constrains.
            <Cell key={d.method} fill={d.value === lowest ? RED : LIGHT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** 2. External. The premise most people arrive with, reversed by the data. */
export function ShareTrend() {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={carriers.share_trend} margin={{ left: 4, right: 24, top: 8 }}>
        <CartesianGrid stroke={LIGHT} vertical={false} />
        <XAxis dataKey="year" {...AXIS} />
        <YAxis {...AXIS} unit="%" width={48} />
        <Tooltip {...TOOLTIP} formatter={(v, n) => `${Number(v).toFixed(1)}% flown by ${n}`} />
        <Line dataKey="Indian" stroke={RED} strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line dataKey="Gulf" stroke={GREY} strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line
          dataKey="Other foreign"
          stroke={LIGHT}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

/** 3. Internal. Stage length against load factor, bubble area is capacity.
 *  The capability gap is visible as a horizontal distance. */
export function CarrierCapability() {
  // International only. The domestic table is a different question and a
  // different answer.
  const data = carriers.international_summary.map((c) => ({
    ...c,
    ask_bn: c.ask / 1e9,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ScatterChart margin={{ left: 4, right: 28, top: 12, bottom: 20 }}>
        <CartesianGrid stroke={LIGHT} />
        <XAxis type="number" dataKey="stage_length_km" {...AXIS} width={60}>
          <Label value="average stage length, km" position="insideBottom" offset={-12} fill={GREY} fontSize={12} />
        </XAxis>
        <YAxis type="number" dataKey="load_factor_pct" domain={["dataMin - 3", "dataMax + 3"]} {...AXIS} unit="%" width={52} />
        <ZAxis type="number" dataKey="ask_bn" range={[60, 500]} />
        <Tooltip
          {...TOOLTIP}
          formatter={(v, n) =>
            n === "load_factor_pct"
              ? `${Number(v).toFixed(1)}% load factor`
              : `${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })} km`
          }
          labelFormatter={() => ""}
        />
        <Scatter data={data} isAnimationActive={false}>
          {data.map((c) => (
            <Cell key={c.airline} fill={c.airline === "IndiGo" ? RED : LIGHT} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}

/** 4a. The profit-pool gap: share of passengers against share of revenue. */
export function PaxVsRevenue() {
  const data = corridors
    .filter((c) => c.revenue_share_pct !== null)
    .map((c) => ({
      region: c.region,
      gap: (c.revenue_share_pct as number) - (c.pax_share_pct as number),
    }))
    .sort((a, b) => a.gap - b.gap);

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 32 }}>
        <CartesianGrid horizontal={false} stroke={LIGHT} />
        <XAxis type="number" {...AXIS} unit="pts" />
        <YAxis type="category" dataKey="region" width={100} {...AXIS} />
        <ReferenceLine x={0} stroke={INK} />
        <Tooltip
          {...TOOLTIP}
          formatter={(v) =>
            `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(1)} points of revenue share against passenger share`
          }
        />
        <Bar dataKey="gap" isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.region} fill={d.region === "Gulf" ? RED : LIGHT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** 4b. The cost bridge as a real waterfall: a transparent riser carries each
 *  step up to where the previous one ended. `go.Waterfall` colours totals red,
 *  which is why the Python version uses measure="absolute" for the opening bar;
 *  the same discipline applies here, so only ONE bar is red. */
export function CaskBridge() {
  let running = 0;
  const data = scenarioCube.cask_bridge.map((s) => {
    if (s.measure === "absolute") {
      running = s.inr_per_ask;
      return { step: s.step, base: 0, delta: s.inr_per_ask, kind: "absolute" as const };
    }
    if (s.measure === "total") {
      return { step: s.step, base: 0, delta: s.inr_per_ask, kind: "total" as const };
    }
    const base = s.inr_per_ask >= 0 ? running : running + s.inr_per_ask;
    const row = {
      step: s.step,
      base,
      delta: Math.abs(s.inr_per_ask),
      kind: s.step === "Currency" ? ("currency" as const) : ("step" as const),
    };
    running += s.inr_per_ask;
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 4, right: 16, bottom: 4 }}>
        <CartesianGrid stroke={LIGHT} vertical={false} />
        <XAxis dataKey="step" {...AXIS} interval={0} angle={-20} textAnchor="end" height={62} />
        <YAxis {...AXIS} width={48} domain={[0, "dataMax + 0.5"]} />
        <Tooltip
          {...TOOLTIP}
          formatter={(v, n) => (n === "delta" ? `${Number(v).toFixed(2)} INR per ASK` : "")}
        />
        <Bar dataKey="base" stackId="w" fill="transparent" isAnimationActive={false} />
        <Bar dataKey="delta" stackId="w" isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.step} fill={d.kind === "currency" ? RED : d.kind === "step" ? GREY : LIGHT} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// 5. The option menu as a 2x2. The source table is prose, so the axes are
// ordinal scales declared here and the mapping is stated on the page rather
// than hidden: a reader can check every placement against the table.
const TIME: Record<string, number> = {
  Immediate: 1,
  "Near term": 2,
  "2027 at the earliest": 3,
  "n/a": 0,
};
const CAPITAL: Record<string, number> = {
  None: 0,
  "Low, recurring": 1,
  Medium: 2,
  High: 3,
};

export function OptionMatrix() {
  const data = narrative.options
    .map((o) => ({
      label: o.Option.replace(" (recommended)", ""),
      recommended: o.Option.includes("(recommended)"),
      x: TIME[o["Time to capacity"]] ?? 0,
      y: CAPITAL[o.Capital] ?? 0,
    }))
    .filter((o) => o.x > 0);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ left: 8, right: 24, top: 16, bottom: 24 }}>
        <CartesianGrid stroke={LIGHT} />
        <XAxis
          type="number"
          dataKey="x"
          domain={[0.5, 3.5]}
          ticks={[1, 2, 3]}
          tickFormatter={(v) => ["", "Immediate", "Near term", "2027+"][v]}
          {...AXIS}
        >
          <Label value="time to capacity" position="insideBottom" offset={-14} fill={GREY} fontSize={12} />
        </XAxis>
        <YAxis
          type="number"
          dataKey="y"
          domain={[-0.5, 3.5]}
          ticks={[0, 1, 2, 3]}
          tickFormatter={(v) => ["None", "Low", "Medium", "High"][v]}
          width={72}
          {...AXIS}
        >
          <Label value="capital" angle={-90} position="insideLeft" fill={GREY} fontSize={12} />
        </YAxis>
        <Tooltip
          {...TOOLTIP}
          formatter={(_v, _n, item) => (item?.payload as { label: string })?.label}
          labelFormatter={() => ""}
        />
        <Scatter data={data} isAnimationActive={false} shape="square">
          {data.map((d) => (
            <Cell key={d.label} fill={d.recommended ? RED : LIGHT} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}
