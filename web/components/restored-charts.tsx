"use client";

import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Label,
  LabelList,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Sankey,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { access, carriers, company, corridors, economics, fleet, scenarioCube } from "@/lib/data";
import { AXIS, GREY, INK, LIGHT, RED, TOOLTIP, n0 } from "@/lib/chart-theme";

// The eight exhibits the Next.js app dropped when it was built, restored against
// the same export the rest of the app reads. Three of them are the most
// distinctive forms in the project and none of them existed in React: the Sankey
// that shows where the passenger vanishes, the Mekko that shows where the profit
// sits, and the slope that shows load factors moving.
//
// Form is chosen by the question, not by habit:
//   how big, ranked?        -> horizontal bar     (domestic share)
//   what share, of one whole? -> stacked single bar (who carries India)
//   where does it go?       -> Sankey             (gateway flows)
//   what share, of what size? -> Mekko            (profit pool)
//   a range against a benchmark? -> range bar     (value at stake)
//   a path over time?       -> line               (scenarios)
//   two paths and the gap between them? -> area   (fleet gap)
//   same measure, two dates, many groups? -> slope (load factor)
//
// Every one carries exactly one annotated point: the place where the so-what
// happens, labelled on the chart face rather than in a caption.

// --------------------------------------------------------------------------
// 1. Domestic share. How big, ranked.
// --------------------------------------------------------------------------

/** The cash engine. IndiGo is red because it is the client and the exhibit is
 *  about what funds the wide-bodies. */
export function DomesticShare() {
  const data = carriers.domestic_summary
    .slice(0, 6)
    .map((c) => ({ airline: c.airline, share: c.share_pct }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke={LIGHT} />
        <XAxis type="number" {...AXIS} unit="%" />
        <YAxis type="category" dataKey="airline" width={132} {...AXIS} />
        <Tooltip {...TOOLTIP} formatter={(v) => `${Number(v).toFixed(1)}% of domestic passengers`} />
        <Bar dataKey="share" isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.airline} fill={d.airline === "IndiGo" ? RED : LIGHT} />
          ))}
          {/* The one annotated point: the client's own share, and nothing else.
              Labelling all six would be six numbers standing in for one idea. */}
          <LabelList
            dataKey="share"
            position="right"
            fontSize={12}
            fill={INK}
            formatter={(v: unknown) =>
              Number(v) > 50 ? `${Number(v).toFixed(1)}% of every domestic passenger` : ""
            }
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// --------------------------------------------------------------------------
// 2. Who carries India. What share, of one whole.
// --------------------------------------------------------------------------

/** One bar, three segments, because the question is composition rather than
 *  ranking and three bars side by side would hide that they sum to everything. */
export function WhoCarriesIndia() {
  const order = ["Indian", "Gulf", "Other foreign"] as const;
  const rows = order
    .map((g) => carriers.who_carries_india.find((r) => r.carrier_group === g))
    .filter((r): r is NonNullable<typeof r> => Boolean(r));

  return (
    <div>
      <div className="flex h-16 w-full">
        {rows.map((r) => (
          <div
            key={r.carrier_group}
            className="flex items-center justify-center border-r border-paper last:border-0"
            style={{
              width: `${r.share_pct}%`,
              background: r.carrier_group === "Indian" ? RED : LIGHT,
            }}
          >
            <span
              className="tnum text-[15px] font-semibold"
              style={{ color: r.carrier_group === "Indian" ? "#fff" : INK }}
            >
              {r.share_pct.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>

      {/* Direct labelling under each segment, so nothing sends the reader to a
          legend and back. */}
      <div className="mt-2 flex w-full text-[12.5px] leading-snug">
        {rows.map((r) => (
          <div key={r.carrier_group} className="pr-3" style={{ width: `${r.share_pct}%` }}>
            <span className={r.carrier_group === "Indian" ? "font-medium text-ink" : "text-grey"}>
              {r.carrier_group === "Indian" ? "Indian carriers" : r.carrier_group}
            </span>
            <span className="tnum block text-grey">{(r.pax_total / 1e6).toFixed(1)}M</span>
          </div>
        ))}
      </div>

      {/* The annotated point: the half-way line the home carriers still sit
          under. It is the whole reason this exhibit is in the deck. */}
      <div className="relative mt-4 h-6">
        <div className="absolute top-0 h-6 border-l border-dashed border-ink" style={{ left: "50%" }}>
          <span className="ml-2 whitespace-nowrap text-[12px] text-ink">
            half the market. Indian carriers are still under it
          </span>
        </div>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------
// 3. Gateway flows. Where does it go.
// --------------------------------------------------------------------------

const GATEWAY_ORDER = ["DELHI", "MUMBAI", "BENGALURU", "KOCHI", "HYDERABAD", "CHENNAI"];

/** The Sankey. India's own statistics record the first foreign point and nothing
 *  beyond, so the "Gulf hub" node is where the passenger disappears. That node is
 *  the red one, and it is the only red on the chart. */
export function GatewayFlows() {
  const gateways = GATEWAY_ORDER.filter((g) =>
    access.gateway_flows.some((f) => f.gateway === g),
  );
  const destinations = ["Gulf hub", "Everywhere else, direct"];
  const names = [...gateways, ...destinations];

  const nodes = names.map((name) => ({ name }));
  const links = access.gateway_flows
    .map((f) => ({
      source: names.indexOf(f.gateway),
      target: names.indexOf(f.destination),
      value: f.pax,
    }))
    .filter((l) => l.source >= 0 && l.target >= 0);

  const gulfIndex = names.indexOf("Gulf hub");

  return (
    <ResponsiveContainer width="100%" height={340}>
      <Sankey
        data={{ nodes, links }}
        nodePadding={18}
        nodeWidth={12}
        margin={{ left: 4, right: 148, top: 8, bottom: 8 }}
        link={{ stroke: LIGHT, strokeOpacity: 0.55 }}
        node={<SankeyNode gulfIndex={gulfIndex} />}
      >
        <Tooltip
          {...TOOLTIP}
          formatter={(v) => `${(Number(v) / 1e6).toFixed(1)}M passengers`}
        />
      </Sankey>
    </ResponsiveContainer>
  );
}

/** Recharts draws Sankey nodes as anonymous rectangles, so the labels have to be
 *  written here. Labelling in place is the point: a legend on a flow diagram
 *  makes the reader trace a colour back and forth. */
function SankeyNode(props: {
  gulfIndex?: number;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  index?: number;
  payload?: { name: string; value: number };
}) {
  const { x = 0, y = 0, width = 0, height = 0, index, payload, gulfIndex } = props;
  const isGulf = index === gulfIndex;
  const isDestination = x > 200;

  return (
    <g>
      <rect x={x} y={y} width={width} height={height} fill={isGulf ? RED : GREY} />
      <text
        x={isDestination ? x + width + 8 : x + width + 8}
        y={y + height / 2}
        textAnchor="start"
        dominantBaseline="middle"
        fontSize={12}
        fill={isGulf ? INK : GREY}
        fontWeight={isGulf ? 600 : 400}
      >
        {payload?.name}
        {payload?.value ? ` ${(payload.value / 1e6).toFixed(1)}M` : ""}
      </text>
      {isGulf && (
        <text
          x={x + width + 8}
          y={y + height / 2 + 16}
          fontSize={11}
          fill={RED}
        >
          the record stops here
        </text>
      )}
    </g>
  );
}

// --------------------------------------------------------------------------
// 4. Profit pool. What share, of what size. The Mekko.
// --------------------------------------------------------------------------

/** Width is revenue, height is modelled margin, so each block's AREA is that
 *  corridor's profit. No charting library here draws a Mekko, and adding one for
 *  a single exhibit is not worth a dependency: it is a cumulative-x bar chart and
 *  the SVG is shorter than the adapter would be.
 *
 *  Adapted in shape from `src/charts.py::mekko`, which is itself adapted from
 *  Vizro (Apache-2.0, see NOTICE). */
export function ProfitPool() {
  const rows = corridors
    .filter((c) => c.revenue_inr_cr !== null && c.margin_pct !== null)
    .sort((a, b) => b.margin_pct! - a.margin_pct!);

  const totalRevenue = rows.reduce((s, c) => s + c.revenue_inr_cr!, 0);
  const maxMargin = Math.max(...rows.map((c) => c.margin_pct!));

  const W = 100; // per cent of the container width
  const H = 260; // px of plot area, below the label band
  const scaleY = (m: number) => (m / (maxMargin * 1.12)) * H;

  let cursor = 0;
  const blocks = rows.map((c) => {
    const w = (c.revenue_inr_cr! / totalRevenue) * W;
    const block = { ...c, x: cursor, w, h: scaleY(c.margin_pct!) };
    cursor += w;
    return block;
  });

  return (
    <div>
      <div className="relative" style={{ height: H }}>
        {blocks.map((b) => {
          const isGulf = b.region === "Gulf";
          // Only blocks wide enough to hold a word get one inside. The rest are
          // named on the axis strip below, never in a legend.
          const roomy = b.w > 11;
          return (
            <div
              key={b.region}
              className="absolute bottom-0 border-r border-paper"
              style={{
                left: `${b.x}%`,
                width: `${b.w}%`,
                height: b.h,
                background: isGulf ? RED : LIGHT,
              }}
              title={`${b.region}: INR ${n0(b.revenue_inr_cr!)} cr revenue at a modelled ${b.margin_pct!.toFixed(1)}% margin`}
            >
              {roomy && (
                <span
                  className="tnum absolute left-1.5 top-1.5 text-[11.5px] font-medium"
                  style={{ color: isGulf ? "#fff" : INK }}
                >
                  {b.margin_pct!.toFixed(0)}%
                </span>
              )}
            </div>
          );
        })}

        {/* The one annotation: the Gulf is the widest block and the shortest of
            the corridors that matter, which is the exhibit in one sentence. */}
        {blocks
          .filter((b) => b.region === "Gulf")
          .map((b) => (
            <div
              key="ann"
              className={`absolute text-[12px] leading-snug text-ink ${
                b.x + b.w > 60 ? "text-right" : ""
              }`}
              // Anchored from whichever side leaves room. The Gulf block is the
              // widest and finishes near the right edge, so anchoring left of it
              // ran the annotation off the container on a narrow screen.
              style={
                b.x + b.w > 60
                  ? { right: `${Math.max(0, 100 - (b.x + b.w))}%`, bottom: b.h + 8, maxWidth: "62%" }
                  : { left: `${b.x + b.w + 1}%`, bottom: b.h + 8, maxWidth: "34%" }
              }
            >
              <span className="font-medium text-red">widest, and the lowest margin of any</span>
              <br />
              volume is real, margin is not
            </div>
          ))}
      </div>

      <div className="relative mt-1 h-12 border-t border-light">
        {blocks.map((b) => (
          <span
            key={b.region}
            className="absolute top-1 origin-top-left -rotate-[38deg] whitespace-nowrap text-[11.5px]"
            style={{ left: `${b.x + b.w / 2}%`, color: b.region === "Gulf" ? INK : GREY }}
          >
            {b.region}
          </span>
        ))}
      </div>
      <p className="mt-8 text-[12px] text-grey">
        Width is revenue share, height is modelled margin, so area is profit.
        <span className="ml-2 border border-light px-1.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-red">
          modelled
        </span>
      </p>
    </div>
  );
}

// --------------------------------------------------------------------------
// 5. Value at stake. A range against a benchmark.
// --------------------------------------------------------------------------

/** The contested pool as a band, never a point, because the origin-destination
 *  share underneath it cannot be verified at all. Drawn against IndiGo's own
 *  annual revenue so the size means something without a second chart. */
export function ValueAtStake() {
  const v = economics.value_at_stake;
  // Read, never typed. This was a literal 84962 for one edit, which is exactly
  // the drift the rest of the project forbids: the figure is a gated assumption
  // and it already travels through src/financials.py.
  const revenue = company.capital_scale.fy2026_revenue_inr_cr;
  const scale = Math.max(v.revenue_ceiling_inr_cr, revenue) * 1.08;
  const w = (x: number) => `${(x / scale) * 100}%`;

  return (
    <div className="space-y-7">
      <div>
        <div className="flex items-baseline justify-between text-[13px]">
          <span className="font-medium">Contested connecting revenue</span>
          <span className="tnum text-grey">
            INR {n0(v.revenue_floor_inr_cr)} to {n0(v.revenue_ceiling_inr_cr)} crore
          </span>
        </div>
        <div className="relative mt-2 h-9 w-full bg-wash">
          {/* The band, drawn as a band. A single bar here would assert a
              precision the underlying O-D share does not have. */}
          <div
            className="absolute top-0 h-9 bg-light"
            style={{ left: 0, width: w(v.revenue_ceiling_inr_cr) }}
          />
          <div className="absolute top-0 h-9 bg-red" style={{ left: 0, width: w(v.revenue_floor_inr_cr) }} />
          <div
            className="absolute -top-1 h-11 border-l-2 border-ink"
            style={{ left: w(v.revenue_floor_inr_cr) }}
          />
        </div>
        <p className="mt-1.5 text-[12px] text-grey">
          at IndiGo&rsquo;s realised yield, up to Emirates&rsquo;. {v.connecting_pax_m.toFixed(1)}M
          passengers a year
        </p>
      </div>

      <div>
        <div className="flex items-baseline justify-between text-[13px]">
          <span className="font-medium">IndiGo FY2026 revenue, for scale</span>
          <span className="tnum text-grey">INR {n0(revenue)} crore</span>
        </div>
        <div className="mt-2 h-9 w-full bg-wash">
          <div className="h-9 bg-grey" style={{ width: w(revenue) }} />
        </div>
        {/* The one annotation. */}
        <p className="mt-1.5 text-[12px] text-ink">
          the contested pool is{" "}
          <span className="tnum font-medium text-red">
            {(v.revenue_floor_inr_cr / revenue).toFixed(2)}x to{" "}
            {(v.revenue_ceiling_inr_cr / revenue).toFixed(2)}x
          </span>{" "}
          the airline&rsquo;s entire annual revenue
        </p>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------
// 6. Scenarios. A path over time.
// --------------------------------------------------------------------------

/** Three demand paths, direct-labelled at the right edge. The bear case is the
 *  red one: if even the pessimistic path needs the capacity, the argument does
 *  not rest on optimism. */
export function Scenarios() {
  const years = [...new Set(scenarioCube.demand_paths.map((r) => r.year))].sort();
  const data = years.map((year) => {
    const row: Record<string, number> = { year };
    for (const r of scenarioCube.demand_paths) {
      if (r.year === year) row[r.scenario] = r.pax_m;
    }
    return row;
  });
  const last = data[data.length - 1];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ left: 4, right: 92, top: 12, bottom: 4 }}>
        <CartesianGrid stroke={LIGHT} vertical={false} />
        <XAxis dataKey="year" {...AXIS} />
        <YAxis {...AXIS} width={52} unit="M" domain={["dataMin - 5", "dataMax + 5"]} />
        <Tooltip {...TOOLTIP} formatter={(v, n) => `${Number(v).toFixed(0)}M passengers, ${n} case`} />
        {(["Bull", "Base", "Bear"] as const).map((s) => (
          <Line
            key={s}
            dataKey={s}
            stroke={s === "Bear" ? RED : GREY}
            strokeWidth={s === "Bear" ? 2.5 : 1.75}
            strokeDasharray={s === "Bull" ? "4 3" : undefined}
            dot={false}
            isAnimationActive={false}
          >
            {/* Direct labels at the end of each line, so there is no legend. */}
            <LabelList
              dataKey={s}
              position="right"
              fontSize={11.5}
              fill={s === "Bear" ? RED : GREY}
              formatter={(v: unknown) =>
                Number(v) === last?.[s] ? `${s} ${Number(v).toFixed(0)}M` : ""
              }
            />
          </Line>
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

// --------------------------------------------------------------------------
// 7. Fleet gap. Two paths, and the gap between them.
// --------------------------------------------------------------------------

/** Capacity needed against capacity available, with the shortfall shaded. The
 *  shape is the finding: a gap opens in the bridge years and closes as aircraft
 *  arrive, and slipping the first delivery moves the curve without changing
 *  where it ends. */
export function FleetGap() {
  const data = fleet.gap_path.map((r) => ({
    year: r.year,
    needed: r.ask_needed_bn,
    available: r.ask_available_bn,
    // Only the SHORTFALL is shaded. Shading the surplus too would draw the eye
    // to the years the argument is not about.
    shortfall: r.gap_bn > 0 ? r.gap_bn : 0,
  }));
  const worst = data.reduce((a, b) => (a.shortfall > b.shortfall ? a : b));

  return (
    <ResponsiveContainer width="100%" height={290}>
      <ComposedChart data={data} margin={{ left: 4, right: 136, top: 16, bottom: 4 }}>
        <CartesianGrid stroke={LIGHT} vertical={false} />
        <XAxis dataKey="year" {...AXIS} />
        <YAxis {...AXIS} width={58} tickFormatter={(v: number) => `${v.toFixed(0)}bn`}>
          <Label
            value="ASK"
            angle={-90}
            position="insideLeft"
            fill={GREY}
            fontSize={12}
          />
        </YAxis>
        <Tooltip
          {...TOOLTIP}
          formatter={(v, n) => `${Number(v).toFixed(1)}bn ASK ${n}`}
          labelFormatter={(y) => `${y}`}
        />
        <Area
          dataKey="shortfall"
          stroke="none"
          fill={RED}
          fillOpacity={0.14}
          isAnimationActive={false}
          baseValue={0}
        />
        <Line dataKey="needed" stroke={INK} strokeWidth={2} dot={false} isAnimationActive={false}>
          <LabelList
            dataKey="needed"
            position="right"
            fontSize={11.5}
            fill={INK}
            formatter={(v: unknown) =>
              Number(v) === data[data.length - 1].needed ? "what the market asks for" : ""
            }
          />
        </Line>
        <Line
          dataKey="available"
          stroke={GREY}
          strokeWidth={2}
          strokeDasharray="5 3"
          dot={false}
          isAnimationActive={false}
        >
          <LabelList
            dataKey="available"
            position="right"
            fontSize={11.5}
            fill={GREY}
            formatter={(v: unknown) =>
              Number(v) === data[data.length - 1].available ? "what the fleet can fly" : ""
            }
          />
        </Line>
        {/* The one annotation: the widest bridge year. */}
        <ReferenceLine
          x={worst.year}
          stroke={RED}
          strokeDasharray="3 3"
          label={{
            value: `gap widest, ${worst.shortfall.toFixed(0)}bn ASK short`,
            fill: RED,
            fontSize: 11,
            position: "top",
          }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// --------------------------------------------------------------------------
// 8. Load factor slope. Same measure, two dates, many groups.
// --------------------------------------------------------------------------

/** A slope chart, which is the only form that makes a two-point comparison
 *  across groups readable at a glance: the SLOPE is the message and a grouped
 *  bar chart hides it.
 *
 *  Read the direction before the level. Two of these four sit BELOW their 2019
 *  load factor, which is not what "recovered past pre-pandemic" would predict,
 *  and the title says what the data says. */
export function LoadFactorSlope() {
  const rows = carriers.load_factor_slope;
  if (!rows.length) return null;
  const startYear = rows[0].start_year;
  const endYear = rows[0].end_year;

  const values = rows.flatMap((r) => [r.load_factor_pct_start, r.load_factor_pct_end]);
  const lo = Math.min(...values) - 4;
  const hi = Math.max(...values) + 4;
  const y = (v: number) => `${(1 - (v - lo) / (hi - lo)) * 100}%`;

  return (
    <div className="relative h-[280px] w-full">
      <div className="absolute inset-y-0 left-[16%] w-px bg-light" />
      <div className="absolute inset-y-0 left-[62%] w-px bg-light" />

      {rows.map((r) => {
        const isClient = r.airline === "IndiGo";
        const colour = isClient ? RED : GREY;
        return (
          <div key={r.airline} className="absolute inset-0">
            <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="none">
              <line
                x1="16%"
                y1={y(r.load_factor_pct_start)}
                x2="62%"
                y2={y(r.load_factor_pct_end)}
                stroke={colour}
                strokeWidth={isClient ? 2.5 : 1.5}
              />
            </svg>
            <span
              className="tnum absolute -translate-x-full -translate-y-1/2 pr-2 text-[12px]"
              style={{ left: "16%", top: y(r.load_factor_pct_start), color: GREY }}
            >
              {r.load_factor_pct_start.toFixed(1)}
            </span>
            <span
              className="tnum absolute -translate-y-1/2 whitespace-nowrap pl-2 text-[12px]"
              style={{ left: "62%", top: y(r.load_factor_pct_end), color: colour }}
            >
              <span className={isClient ? "font-semibold" : ""}>
                {r.load_factor_pct_end.toFixed(1)}
              </span>{" "}
              <span className={isClient ? "font-medium text-ink" : "text-grey"}>{r.airline}</span>
            </span>
          </div>
        );
      })}

      <span className="absolute -top-1 left-[16%] -translate-x-1/2 text-[11px] font-semibold uppercase tracking-[0.1em] text-grey">
        {startYear}
      </span>
      <span className="absolute -top-1 left-[62%] -translate-x-1/2 text-[11px] font-semibold uppercase tracking-[0.1em] text-grey">
        {endYear}
      </span>
      {/* The one annotation, and it argues against the obvious reading. */}
      <p className="absolute bottom-0 left-0 max-w-[46ch] text-[12px] leading-snug text-ink">
        Every carrier clears 80%, so the aircraft that exist are full. But the two
        largest are <span className="font-medium text-red">below</span> their {startYear} level,
        not above it.
      </p>
    </div>
  );
}

// --------------------------------------------------------------------------
// 9-11. Three exhibits that existed only inside an interactive page.
// --------------------------------------------------------------------------
//
// The dashboard and the deck each had a private copy of a chart the static site
// publishes as an exhibit in its own right. Private copies are why the parity
// count was wrong and unnoticed, so they are components now and the registry
// names them like everything else.

/** Belly freight per passenger, ordered by CORRIDOR DISTANCE rather than by
 *  freight, because the exhibit's point is that the two do not track. Ordering
 *  by freight would draw the exact conclusion the chart exists to refuse. */
export function CargoAsymmetry() {
  const data = corridors
    .filter((c) => c.kg_per_pax !== null && c.stage_km !== null)
    .sort((a, b) => a.stage_km! - b.stage_km!)
    .map((c) => ({ region: c.region, kg: c.kg_per_pax!, stage: c.stage_km! }));
  const most = data.reduce((a, b) => (a.kg > b.kg ? a : b));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ left: 4, right: 16, top: 28, bottom: 4 }}>
        <CartesianGrid stroke={LIGHT} vertical={false} />
        <XAxis dataKey="region" {...AXIS} interval={0} angle={-28} textAnchor="end" height={86}>
          <Label
            value="corridors ordered by sector length, shortest first"
            position="insideBottom"
            offset={-4}
            fill={GREY}
            fontSize={11}
          />
        </XAxis>
        <YAxis {...AXIS} width={52} unit="kg" />
        <Tooltip
          {...TOOLTIP}
          formatter={(v, _n, item) =>
            `${Number(v).toFixed(1)} kg per passenger over ${n0(Number(item?.payload?.stage))} km`
          }
        />
        <Bar dataKey="kg" isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.region} fill={d.region === most.region ? RED : LIGHT} />
          ))}
          {/* The one annotation, and it is the counter-example: the densest
              freight corridor is not the longest one. */}
          <LabelList
            dataKey="kg"
            position="top"
            fontSize={11.5}
            fill={RED}
            formatter={(v: unknown) =>
              Number(v) === most.kg ? `${most.region}: densest freight, thinnest passenger market` : ""
            }
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Which shock hurts more. Two lines, direct-labelled, with the breakeven line
 *  drawn because every path starts above it: FY2026 opened with unit cost at
 *  5.00 against unit revenue of 4.99. */
export function FuelFxSensitivity() {
  const data = scenarioCube.fuel_fx;
  const rask = data[0]?.rask_actual;

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ left: 4, right: 158, top: 12, bottom: 8 }}>
        <CartesianGrid stroke={LIGHT} vertical={false} />
        <XAxis dataKey="move_pct" {...AXIS} unit="%">
          <Label value="shock" position="insideBottom" offset={-4} fill={GREY} fontSize={12} />
        </XAxis>
        <YAxis {...AXIS} width={56} tickFormatter={(v: number) => v.toFixed(2)} />
        {rask !== undefined && (
          <ReferenceLine
            y={rask}
            stroke={INK}
            strokeDasharray="4 3"
            label={{
              value: `unit revenue ${rask.toFixed(2)}. Every path starts above it`,
              fill: INK,
              fontSize: 11,
              position: "insideTopLeft",
            }}
          />
        )}
        <Tooltip {...TOOLTIP} formatter={(v) => `${Number(v).toFixed(2)} INR per ASK`} />
        <Line
          dataKey="cask_fuel_shock"
          stroke={GREY}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        >
          <LabelList
            dataKey="cask_fuel_shock"
            position="right"
            fontSize={11.5}
            fill={GREY}
            formatter={(v: unknown) =>
              Number(v) === data[data.length - 1].cask_fuel_shock ? "fuel shock" : ""
            }
          />
        </Line>
        <Line
          dataKey="cask_fx_shock_ceiling"
          stroke={RED}
          strokeWidth={2.5}
          dot={false}
          isAnimationActive={false}
        >
          <LabelList
            dataKey="cask_fx_shock_ceiling"
            position="right"
            fontSize={11.5}
            fill={RED}
            formatter={(v: unknown) =>
              Number(v) === data[data.length - 1].cask_fx_shock_ceiling
                ? "currency, at the top of the band"
                : ""
            }
          />
        </Line>
      </LineChart>
    </ResponsiveContainer>
  );
}

/** Entitlement utilisation as a bullet, which is the right form for "position on
 *  a scale against a target" and the wrong form for almost anything else.
 *  Dubai is the red one because it is the binding point. */
export function EntitlementUse() {
  return (
    <div className="space-y-6">
      {access.entitlements.map((e) => {
        const binding = e.utilisation_pct > 85;
        return (
          <div key={e.foreign_point}>
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 text-[14px]">
              <span className="font-medium">{e.foreign_point}</span>
              <span className="tnum text-[12.5px] text-grey">
                {n0(e.implied_seats_per_week)} of {n0(e.reported_entitlement_both_sides)} seats a
                week
              </span>
            </div>
            <div className="relative mt-2 h-7 w-full bg-light">
              <div
                className="h-7"
                style={{
                  width: `${Math.min(100, e.utilisation_pct)}%`,
                  background: binding ? RED : GREY,
                }}
              />
              <div
                className="absolute -top-1 h-9 border-l border-dashed border-ink"
                style={{ left: "100%" }}
              />
            </div>
            <p className="tnum mt-1 text-[12.5px]" style={{ color: binding ? RED : GREY }}>
              {e.utilisation_pct.toFixed(1)}% used
              {binding && <span className="text-ink">, effectively no room left</span>}
            </p>
          </div>
        );
      })}
      <p className="text-[12px] leading-relaxed text-grey">
        The dashed line is the reported entitlement. Both figures carry
        UNVERIFIED_NO_PRIMARY: India publishes no entitlement table at all.
      </p>
    </div>
  );
}
