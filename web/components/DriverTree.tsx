import Link from "next/link";
import { carriers, company, corridors, access, fleet } from "@/lib/data";

// The value-driver tree, used as NAVIGATION rather than as decoration.
//
// Most driver trees on consulting sites are a box diagram nobody clicks. This
// one is the index: every leaf carries its computed number and links to the
// exhibit that proves it, and a test asserts no leaf points at an anchor that
// does not render.
//
// It is one identity decomposed, not four frameworks stacked. Revenue and profit
// share the same ASK term; reach is what sets the stage length inside yield; and
// competitive position decides whether the yield holds at all. Each branch fails
// for a different reason, and the recommendation is the branch that survives.

const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;
const indigo = carriers.international_summary.find((c) => c.airline === "IndiGo")!;
const dubai = access.entitlements.find((e) => e.foreign_point === "DUBAI")!;
const spread = company.spread;
const emirates = company.competitive_position.find((c) => c.carrier === "Emirates")!;
const baseline = fleet.baseline;

type Leaf = { metric: string; value: string; verdict: "fails" | "holds" | "mixed"; href: string };

const BRANCHES: {
  branch: string;
  question: string;
  identity: string;
  leaves: Leaf[];
}[] = [
  {
    branch: "Profit",
    question: "Can it earn?",
    identity: "(RASK - CASK) x ASK",
    leaves: [
      {
        metric: "Unit revenue against unit cost, FY2026",
        value: `${spread.rask.toFixed(2)} against ${spread.cask.toFixed(2)}, inverted`,
        verdict: "fails",
        href: "/company#exhibit-unit_spread",
      },
      {
        metric: "Currency contribution to that inversion",
        value: `+${spread.currency_contribution.toFixed(2)} per ASK, ${Math.round(spread.currency_vs_gap)}x the gap`,
        verdict: "mixed",
        href: "/story#exhibit-cask_bridge",
      },
    ],
  },
  {
    branch: "Revenue",
    question: "Can it fill the aircraft?",
    identity: "ASK x load factor x yield",
    leaves: [
      {
        metric: "International load factor",
        value: `${(baseline.load_factor * 100).toFixed(1)}%`,
        verdict: "holds",
        href: "/story#exhibit-load_factor_slope",
      },
      {
        metric: "Corridor with the most fare headroom",
        value: `Europe, +${europe.yield_headroom_pct!.toFixed(1)}%`,
        verdict: "holds",
        href: "/#exhibit-yield_headroom",
      },
      {
        metric: "Share of revenue the Gulf carries",
        value: `${gulf.revenue_share_pct!.toFixed(0)}% of revenue on ${gulf.pax_share_pct!.toFixed(0)}% of passengers`,
        verdict: "fails",
        href: "/story#exhibit-profit_pool",
      },
    ],
  },
  {
    branch: "Reach",
    question: "Can it fly there at all?",
    identity: "stage length, and treaty entitlement",
    leaves: [
      {
        metric: "IndiGo international stage length",
        value: `${Math.round(indigo.stage_length_km).toLocaleString()} km`,
        verdict: "fails",
        href: "/story#exhibit-stage_length_gap",
      },
      {
        metric: "India-Dubai entitlement used",
        value: `${dubai.utilisation_pct.toFixed(1)}%`,
        verdict: "fails",
        href: "/frameworks#exhibit-entitlement_use",
      },
    ],
  },
  {
    branch: "Competitive",
    question: "Can it win the passenger?",
    identity: "yield against the carrier selling the same journey",
    leaves: [
      {
        metric: "IndiGo yield against Emirates, per RPK",
        value: `${spread.rask ? emirates.yield_vs_indigo!.toFixed(2) : "?"}x against IndiGo`,
        verdict: "fails",
        href: "/company#exhibit-competitive_position",
      },
      {
        metric: "Indian carrier share of the home market",
        value: `${carriers.share_trend[carriers.share_trend.length - 1].Indian.toFixed(1)}%, rising`,
        verdict: "holds",
        href: "/story#exhibit-carrier_share_trend",
      },
    ],
  },
];

const MARK = {
  fails: { glyph: "x", label: "fails today", className: "text-red" },
  holds: { glyph: "/", label: "holds", className: "text-ink" },
  mixed: { glyph: "~", label: "mixed", className: "text-grey" },
} as const;

export function DriverTree() {
  return (
    <div>
      <p className="max-w-[62ch] font-serif text-[clamp(1.15rem,2vw,1.5rem)] leading-snug">
        Does the wide-body order create value for IndiGo?
      </p>
      <p className="mt-2 max-w-[70ch] text-[13.5px] leading-relaxed text-grey">
        Four branches of one identity, not four frameworks stacked. Every leaf carries the number
        that decides it and links to the exhibit that proves it. Three branches fail as things
        stand, and the recommendation is what is left.
      </p>

      <ol className="mt-8 grid gap-px bg-light lg:grid-cols-2">
        {BRANCHES.map((b) => (
          <li key={b.branch} className="bg-paper p-6">
            <div className="flex items-baseline gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red">
                {b.branch}
              </span>
              <span className="font-serif text-lg font-semibold">{b.question}</span>
            </div>
            <p className="tnum mt-1 text-[12.5px] text-grey">{b.identity}</p>

            <ul className="mt-4 space-y-3">
              {b.leaves.map((leaf) => {
                const mark = MARK[leaf.verdict];
                return (
                  <li key={leaf.metric}>
                    <Link
                      href={leaf.href}
                      className="group flex gap-3 focus-visible:outline-2 focus-visible:outline-red"
                    >
                      <span
                        aria-label={mark.label}
                        className={`mt-0.5 w-3 shrink-0 text-center font-semibold ${mark.className}`}
                      >
                        {mark.glyph}
                      </span>
                      <span className="min-w-0">
                        <span className="block text-[13.5px] leading-snug text-ink/70">
                          {leaf.metric}
                        </span>
                        <span
                          className={`tnum block text-[15px] font-medium leading-snug group-hover:text-red ${
                            leaf.verdict === "fails" ? "text-red" : "text-ink"
                          }`}
                        >
                          {leaf.value}{" "}
                          <span aria-hidden className="text-grey group-hover:text-red">
                            &rarr;
                          </span>
                        </span>
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </li>
        ))}
      </ol>
    </div>
  );
}

/** Every href the tree emits, for the test that asserts none of them dangle. */
export const DRIVER_TREE_TARGETS = BRANCHES.flatMap((b) => b.leaves.map((l) => l.href));
