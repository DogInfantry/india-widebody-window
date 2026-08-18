"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { company } from "@/lib/data";
import { AXIS, GREY, INK, LIGHT, RED, TOOLTIP, n0 } from "@/lib/chart-theme";

// The client's own numbers. Every figure comes from src/financials.py, which
// reads only rows that have already cleared the assumption gate.

const spread = company.spread;

/** The inverted spread, drawn at the scale the gap actually has. Two bars a
 *  hundredth apart look identical, so the exhibit is a zoomed axis with the
 *  breakeven line drawn: the point is that the gap is TINY and still negative,
 *  not that it is dramatic. Drawing it dramatically would be a lie. */
export function UnitSpread() {
  const data = [
    { label: "Unit revenue, RASK", value: spread.rask, kind: "revenue" as const },
    { label: "Unit cost, CASK", value: spread.cask, kind: "cost" as const },
  ];
  const lo = Math.min(spread.rask, spread.cask) - 0.06;
  const hi = Math.max(spread.rask, spread.cask) + 0.06;

  return (
    <div>
      <ResponsiveContainer width="100%" height={190}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 64, top: 8, bottom: 8 }}>
          <CartesianGrid horizontal={false} stroke={LIGHT} />
          <XAxis
            type="number"
            domain={[lo, hi]}
            {...AXIS}
            tickFormatter={(v: number) => v.toFixed(2)}
          />
          <YAxis type="category" dataKey="label" width={148} {...AXIS} />
          <ReferenceLine x={spread.rask} stroke={INK} strokeDasharray="4 3" />
          <Tooltip {...TOOLTIP} formatter={(v) => `${Number(v).toFixed(2)} INR per ASK`} />
          <Bar dataKey="value" isAnimationActive={false} barSize={34}>
            {data.map((d) => (
              <Cell key={d.label} fill={d.kind === "cost" ? RED : LIGHT} />
            ))}
            <LabelList
              dataKey="value"
              position="right"
              fontSize={13}
              fill={INK}
              formatter={(v: unknown) => Number(v).toFixed(2)}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* The one annotation, and it is the whole exhibit: the gap is one paisa,
          and the currency movement in the same year was forty-one. */}
      <p className="mt-3 max-w-[60ch] text-[13px] leading-relaxed">
        Cost sits <span className="tnum font-semibold text-red">
          {Math.abs(spread.spread).toFixed(2)}
        </span>{" "}
        above revenue, {Math.abs(spread.spread_pct_of_rask).toFixed(1)}% of unit revenue. In the
        same year the rupee added{" "}
        <span className="tnum font-semibold">{spread.currency_contribution.toFixed(2)}</span> to
        unit cost, <span className="tnum font-semibold">{Math.round(spread.currency_vs_gap)}x</span>{" "}
        the gap. The inversion is a treasury outcome on dollar lease liabilities, not a route one.
      </p>
    </div>
  );
}

/** Both margins, side by side, in one exhibit. Publishing either alone is the
 *  error this project has already made once, in the opposite direction, and the
 *  component cannot render one without the other because the data comes as a
 *  single table. */
export function MarginLadder() {
  const bases = ["As reported", "Excluding forex"] as const;
  const years = [...new Set(company.margin_ladder.map((r) => r.year))].sort();
  const data = years.map((year) => {
    const row: Record<string, string | number> = { year };
    for (const r of company.margin_ladder) {
      if (r.year === year) row[r.basis] = r.margin_pct;
    }
    return row;
  });

  return (
    <div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ left: 4, right: 16, top: 20, bottom: 4 }}>
          <CartesianGrid stroke={LIGHT} vertical={false} />
          <XAxis dataKey="year" {...AXIS} />
          <YAxis {...AXIS} width={52} unit="%" domain={[0, 32]} />
          <Tooltip {...TOOLTIP} formatter={(v, n) => `${Number(v).toFixed(1)}% EBITDAR margin, ${n}`} />
          {bases.map((b) => (
            <Bar key={b} dataKey={b} isAnimationActive={false} fill={b === "As reported" ? RED : LIGHT}>
              <LabelList
                dataKey={b}
                position="top"
                fontSize={12}
                fill={b === "As reported" ? RED : GREY}
                formatter={(v: unknown) => `${Number(v).toFixed(1)}%`}
              />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 text-[12.5px] text-grey">
        Red is what IndiGo reported. Grey is the same year excluding forex on dollar lease
        liabilities. Both are true and they tell opposite stories.
      </p>
    </div>
  );
}

/** Three cost bases, two years. A grouped bar rather than a waterfall, because
 *  the waterfall of the same data already exists as the CASK bridge and drawing
 *  it twice would be a form chosen by habit. */
export function CostStack() {
  const data = company.cost_stack.map((r) => ({
    basis: r.basis,
    FY2025: r.fy2025,
    FY2026: r.fy2026,
    change: r.change,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ left: 4, right: 16, top: 20, bottom: 4 }}>
          <CartesianGrid stroke={LIGHT} vertical={false} />
          <XAxis dataKey="basis" {...AXIS} interval={0} fontSize={11.5} />
          <YAxis {...AXIS} width={48} tickFormatter={(v: number) => v.toFixed(1)} />
          <Tooltip {...TOOLTIP} formatter={(v, n) => `${Number(v).toFixed(2)} INR per ASK, ${n}`} />
          <Bar dataKey="FY2025" fill={LIGHT} isAnimationActive={false} />
          <Bar dataKey="FY2026" isAnimationActive={false}>
            {data.map((d) => (
              // One red: the basis where genuine inflation lives. Everything
              // above it is fuel and currency, which are not operating choices.
              <Cell key={d.basis} fill={d.basis.includes("ex-forex") ? RED : GREY} />
            ))}
            <LabelList
              dataKey="change"
              position="top"
              fontSize={11.5}
              fill={INK}
              formatter={(v: unknown) => `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(2)}`}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 max-w-[64ch] text-[12.5px] leading-relaxed text-grey">
        Light is FY2025, solid is FY2026, and the label is the change. Strip fuel and cost rose
        0.52. Strip currency as well, in red, and genuine non-fuel inflation was 0.11. The other
        0.41 is the rupee.
      </p>
    </div>
  );
}

/** Yield per RPK, the client against the carrier selling the same journey. The
 *  gap is a BOUND on the prize, not a measurement of a connect premium, and the
 *  chart says so rather than leaving the reader to over-read it. */
export function CompetitivePosition() {
  const data = company.competitive_position
    .filter((c) => c.yield_inr_per_rpk !== null)
    .map((c) => ({ carrier: c.carrier, yield_: c.yield_inr_per_rpk as number }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 72, top: 8, bottom: 8 }}>
          <CartesianGrid horizontal={false} stroke={LIGHT} />
          <XAxis type="number" {...AXIS} tickFormatter={(v: number) => v.toFixed(0)} />
          <YAxis type="category" dataKey="carrier" width={100} {...AXIS} />
          <Tooltip {...TOOLTIP} formatter={(v) => `${Number(v).toFixed(2)} INR per RPK`} />
          <Bar dataKey="yield_" isAnimationActive={false} barSize={34}>
            {data.map((d) => (
              <Cell key={d.carrier} fill={d.carrier === "Emirates" ? RED : LIGHT} />
            ))}
            <LabelList
              dataKey="yield_"
              position="right"
              fontSize={13}
              fill={INK}
              formatter={(v: unknown) => Number(v).toFixed(2)}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 max-w-[66ch] text-[12.5px] leading-relaxed text-grey">
        Air India is absent because it is unlisted and files nothing, which is a NOT_AVAILABLE
        row rather than a gap filled with a proxy. Do not read the whole difference as a connect
        premium: Emirates carries substantial premium cabins where IndiGo is all-economy, and
        yield per kilometre normally falls with stage length, so a long-haul carrier earning
        double a short-haul one is a wide gap even after cabin mix.
      </p>
    </div>
  );
}

/** Scale without a price. Revenue at realised RASK, against the top line and one
 *  year of earnings, because no aircraft price has cleared the assumption gate
 *  and inventing one would put an unverifiable number at the centre of the
 *  client page. */
export function CapitalScale() {
  const cap = company.capital_scale;
  const rows = [
    { label: "FY2026 revenue", value: cap.fy2026_revenue_inr_cr, red: false },
    { label: "The 60 A350s, at FY2026 RASK", value: cap.revenue_potential_inr_cr, red: true },
    { label: "FY2026 EBITDAR, excluding forex", value: cap.fy2026_ebitdar_exforex_inr_cr, red: false },
  ];
  const max = Math.max(...rows.map((r) => r.value));

  return (
    <div className="space-y-5">
      {rows.map((r) => (
        <div key={r.label}>
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 text-[13.5px]">
            <span className={r.red ? "font-medium" : "text-ink/75"}>{r.label}</span>
            <span className="tnum text-grey">INR {n0(r.value)} crore</span>
          </div>
          <div className="mt-1.5 h-8 w-full bg-wash">
            <div
              className="h-8"
              style={{ width: `${(r.value / max) * 100}%`, background: r.red ? RED : LIGHT }}
            />
          </div>
        </div>
      ))}
      <p className="max-w-[66ch] text-[13px] leading-relaxed">
        Flown at the owned-fleet utilisation basis of {cap.utilisation_hours_per_day.toFixed(2)}{" "}
        hours a day, the client&rsquo;s own sixty aircraft produce{" "}
        <span className="tnum font-semibold">{cap.ask_bn.toFixed(1)}bn</span> ASK, which at
        FY2026&rsquo;s realised unit revenue is{" "}
        <span className="tnum font-semibold text-red">
          {cap.pct_of_fy2026_revenue.toFixed(0)}%
        </span>{" "}
        of the entire top line and{" "}
        <span className="tnum font-semibold">
          {cap.multiple_of_fy2026_ebitdar.toFixed(2)}x
        </span>{" "}
        a year of earnings. A further {cap.purchase_rights_not_converted} purchase rights are
        unconverted and are not counted here, because a purchase right is not capacity.
      </p>
    </div>
  );
}

/** The second both-ends cross-check in the project, on two bases. */
export function BlockHourReconciliation() {
  const ops = company.operations;
  const rows = [
    { label: "IndiGo published block hours, FY2026", value: ops.published_block_hours, red: false },
    { label: "DGCA, scheduled services only", value: ops.dgca_scheduled_hours, red: true },
    { label: "DGCA, all services, like for like", value: ops.dgca_all_services_hours, red: false },
  ];
  const max = Math.max(...rows.map((r) => r.value));
  const lo = Math.min(...rows.map((r) => r.value)) * 0.985;

  return (
    <div className="space-y-4">
      {rows.map((r) => (
        <div key={r.label}>
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 text-[13.5px]">
            <span className="text-ink/75">{r.label}</span>
            <span className="tnum font-medium">{n0(r.value)} hours</span>
          </div>
          {/* Axis starts near the values, not at zero, because these three
              numbers agree to within a third of a per cent and a zero-based bar
              would draw three identical rectangles. */}
          <div className="mt-1.5 h-7 w-full bg-wash">
            <div
              className="h-7"
              style={{
                width: `${((r.value - lo) / (max - lo)) * 100}%`,
                background: r.red ? RED : LIGHT,
              }}
            />
          </div>
        </div>
      ))}
      <p className="max-w-[66ch] text-[13px] leading-relaxed">
        Two organisations counting the same fleet from opposite ends. On scheduled services they
        differ by{" "}
        <span className="tnum font-semibold text-red">{ops.reconciliation_pct.toFixed(2)}%</span>,
        which is the figure this project publishes everywhere. Add DGCA&rsquo;s non-scheduled
        international rows, which IndiGo&rsquo;s own total includes, and the two land within{" "}
        <span className="tnum font-semibold">
          {Math.abs(ops.dgca_all_services_hours - ops.published_block_hours).toFixed(1)} hours
        </span>{" "}
        of each other. Given in hours rather than as a percentage, because the percentage rounds
        to zero and a printed zero reads as a formatting error rather than as agreement. The
        residual was never measurement error. It was a filter.
      </p>
    </div>
  );
}
