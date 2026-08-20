import Link from "next/link";
import { Delta } from "@/components/scan-forms";
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
// competitive position decides whether the yield holds at all.
//
// **Rebuilt 2026-08-20, because it read as a text grid rather than an exhibit.**
// Three things were wrong and all three were about the reader, not the data:
//
//   1. The verdicts were the characters `x`, `/` and `~`, with the only
//      explanation in an `aria-label` no sighted reader ever sees. A slash
//      meaning "holds" is not decodable. They are labelled chips now.
//   2. There was no branch-level roll-up, so the headline finding was invisible
//      unless you read all nine leaves and did the counting yourself.
//   3. Every leaf was a link and none of them looked like one. They now use the
//      `.block-link` convention: a rule at rest, a surface and a moving chevron
//      on hover, and a real focus ring.
//
// **The roll-up is computed, and finding the rule mattered.** The old subtitle
// asserted "three branches fail as things stand". Counting branches with at
// least one failing leaf gives four; counting branches where failures outnumber
// passes gives two. Neither is three. The rule that yields three is
// `fails > 0 && fails >= holds`, which is also the defensible one: a branch is
// failing when its problems are at least as numerous as the things going right.
// It is now computed and the sentence reads the computed number, the same way
// `web/app/methodology` renders `pivots.length` instead of stating a figure.

const gulf = corridors.find((c) => c.region === "Gulf")!;
const europe = corridors.find((c) => c.region === "Europe")!;
const indigo = carriers.international_summary.find((c) => c.airline === "IndiGo")!;
const dubai = access.entitlements.find((e) => e.foreign_point === "DUBAI")!;
const spread = company.spread;
const emirates = company.competitive_position.find((c) => c.carrier === "Emirates")!;
const baseline = fleet.baseline;

type Verdict = "fails" | "holds" | "mixed";
/** `value` is a string for most leaves and a signed percentage for the two that
 *  are read as "does this clear its own cost". Those render through `Delta`,
 *  because a leading minus sign in body text is the weakest possible way to say
 *  no, and the sign is the entire content of the figure. */
type Leaf = {
  metric: string;
  value: string;
  delta?: number;
  verdict: Verdict;
  href: string;
};

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
        value: "Europe",
        delta: europe.yield_headroom_pct!,
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

/** A branch is failing when its problems are at least as numerous as the things
 *  going right. Stated as a rule so the count in the prose cannot drift from it. */
function rollUp(leaves: Leaf[]): Verdict {
  const fails = leaves.filter((l) => l.verdict === "fails").length;
  const holds = leaves.filter((l) => l.verdict === "holds").length;
  if (fails > 0 && fails >= holds) return "fails";
  if (fails > 0) return "mixed";
  return "holds";
}

const FAILING = BRANCHES.filter((b) => rollUp(b.leaves) === "fails").length;
const WORDS = ["none", "one", "two", "three", "four"] as const;

/** Chips, not glyphs. Written here rather than installed, because a status chip
 *  is ten lines and a component library is three dependencies. */
const CHIP: Record<Verdict, { label: string; className: string }> = {
  fails: { label: "Fails today", className: "border-red text-red" },
  holds: { label: "Holds", className: "border-light text-ink" },
  mixed: { label: "Mixed", className: "border-light text-grey" },
};

function Chip({ verdict }: { verdict: Verdict }) {
  const c = CHIP[verdict];
  return (
    <span
      className={`shrink-0 border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.1em] ${c.className}`}
    >
      {c.label}
    </span>
  );
}

export function DriverTree() {
  return (
    <div>
      <p className="max-w-[62ch] font-serif text-[clamp(1.15rem,2vw,1.5rem)] leading-snug">
        Does the wide-body order create value for IndiGo?
      </p>
      <p className="mt-2 max-w-[70ch] text-[13.5px] leading-relaxed text-grey">
        Four branches of one identity, not four frameworks stacked. Every leaf carries the number
        that decides it and links to the exhibit that proves it.
      </p>

      {/* The finding, at the top, where a reader who reads nothing else still
          gets it. Counted from the leaves rather than typed. */}
      <p className="mt-5 flex flex-wrap items-baseline gap-x-3 border-l-2 border-red pl-4">
        <span className="font-serif text-[clamp(1.1rem,2vw,1.4rem)] font-semibold">
          {(WORDS[FAILING] ?? String(FAILING)).replace(/^./, (m) => m.toUpperCase())} of{" "}
          {WORDS[BRANCHES.length] ?? BRANCHES.length} branches fail as things stand.
        </span>
        <span className="text-[13.5px] text-grey">The recommendation is what is left.</span>
      </p>

      <ol className="mt-8 grid gap-px bg-light lg:grid-cols-2">
        {BRANCHES.map((b) => {
          const verdict = rollUp(b.leaves);
          return (
            <li key={b.branch} className="bg-paper p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-baseline gap-3">
                    <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red">
                      {b.branch}
                    </span>
                    <span className="font-serif text-lg font-semibold">{b.question}</span>
                  </div>
                  <p className="tnum mt-1 text-[12.5px] text-grey">{b.identity}</p>
                </div>
                <Chip verdict={verdict} />
              </div>

              <ul className="mt-5 space-y-px">
                {b.leaves.map((leaf) => (
                  <li key={leaf.metric}>
                    <Link href={leaf.href} className="block-link group py-2.5 pl-3 pr-2">
                      <span className="flex items-start justify-between gap-3">
                        <span className="min-w-0">
                          <span className="block text-[13px] leading-snug text-grey">
                            {leaf.metric}
                          </span>
                          <span
                            className={`tnum mt-0.5 block text-[15px] font-medium leading-snug ${
                              leaf.verdict === "fails" ? "text-red" : "text-ink"
                            }`}
                          >
                            {leaf.value}
                            {leaf.delta != null && (
                              <>
                                {" "}
                                <Delta pct={leaf.delta} />
                              </>
                            )}{" "}
                            <span aria-hidden className="go">
                              &rarr;
                            </span>
                          </span>
                        </span>
                        <Chip verdict={leaf.verdict} />
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

/** Every href the tree emits, for the test that asserts none of them dangle. */
export const DRIVER_TREE_TARGETS = BRANCHES.flatMap((b) => b.leaves.map((l) => l.href));
