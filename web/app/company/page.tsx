import type { Metadata } from "next";
import Link from "next/link";
import { RegisteredExhibit } from "@/lib/exhibits";
import { brief, company } from "@/lib/data";

export const metadata: Metadata = { title: "The client" };

// The page that was missing, and its absence is why the app read as sector
// research. `docs/storyline.md` named IndiGo, the decision and the success
// metrics from early on; no delivery surface showed the client's own numbers.
//
// **Scope is stated at the top and enforced by the module.** This is a P&L, unit
// economics and capital-scale view. It is not a balance sheet, a return on
// invested capital, a cost of capital or a financing plan, because no
// balance-sheet row has cleared the assumption gate and inventing one would put
// an unverifiable number at the centre of the client page. `src/financials.py`
// reads only gated rows, and a test fails if an aircraft price ever appears.

const spread = company.spread;
const cap = company.capital_scale;
const reported = company.margin_ladder.find(
  (r) => r.year === "FY2026" && r.basis === "As reported",
)!;
const exforex = company.margin_ladder.find(
  (r) => r.year === "FY2026" && r.basis === "Excluding forex",
)!;

const HEADLINE = [
  {
    value: `${spread.rask.toFixed(2)} / ${spread.cask.toFixed(2)}`,
    label: "unit revenue against unit cost, FY2026",
    note: "inverted by one paisa per available seat kilometre",
    adverse: true,
  },
  {
    value: `${reported.margin_pct.toFixed(1)}%`,
    label: "EBITDAR margin as reported",
    note: `${exforex.margin_pct.toFixed(1)}% excluding forex. Both are true and both are published here`,
    adverse: true,
  },
  {
    value: `+${spread.currency_contribution.toFixed(2)}`,
    label: "the rupee's contribution to unit cost",
    note: "against a net rise of 0.34. Currency alone exceeds the whole increase",
    adverse: true,
  },
  {
    value: `${cap.pct_of_fy2026_revenue.toFixed(0)}%`,
    label: "of the top line the sixty A350s could produce",
    note: `${cap.ask_bn.toFixed(1)}bn ASK at realised unit revenue, ${cap.multiple_of_fy2026_ebitdar.toFixed(2)}x a year of EBITDAR`,
    adverse: false,
  },
];

export default function Company() {
  return (
    <main className="mx-auto max-w-[1180px] px-8 py-14">
      <header className="max-w-[68ch]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          The client
        </p>
        <h1 className="mt-4 font-serif text-[clamp(2rem,5vw,3.25rem)] font-bold leading-[1.1]">
          IndiGo is buying long-haul capacity from a position with no margin cushion
        </h1>
        <p className="mt-5 text-[17px] leading-relaxed text-ink/75">
          {brief.decision} The rest of this case argues about where those aircraft should fly.
          This page is about the business that has to carry them, and its central fact is that in{" "}
          {spread.year} unit cost sat above unit revenue.
        </p>
      </header>

      <section aria-label="Headline figures" className="mt-12 grid gap-px bg-light sm:grid-cols-2 lg:grid-cols-4">
        {HEADLINE.map((k) => (
          <div key={k.label} className="bg-paper p-6">
            <p
              className={`tnum font-serif text-[2.1rem] font-semibold leading-none ${
                k.adverse ? "text-red" : "text-ink"
              }`}
            >
              {k.value}
            </p>
            <p className="mt-3 text-[14.5px] font-medium leading-snug">{k.label}</p>
            <p className="mt-2 text-[12.5px] leading-relaxed text-grey">{k.note}</p>
          </div>
        ))}
      </section>

      {/* Scope, stated rather than left for a reader to discover by absence. */}
      <section className="mt-12 border-l-2 border-ink bg-wash py-5 pl-5 pr-4">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          What this page is, and is not
        </p>
        <p className="mt-3 max-w-[74ch] text-[14.5px] leading-relaxed">
          A profit and loss, unit economics and capital scale view, built entirely from figures
          IndiGo has published and this project has verified against the primary document.{" "}
          <strong>
            There is no balance sheet, no return on invested capital, no cost of capital and no
            financing plan.
          </strong>{" "}
          Not because they would be uninteresting, but because none of the inputs has cleared this
          project&rsquo;s assumption gate, and a page that mixes verified figures with plausible
          ones is worse than a page that stops. {brief.not_this}
        </p>
      </section>

      <div className="mt-20 space-y-20">
        <section>
          <h2 className="font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">
            Can it earn?
          </h2>
          <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
            The first branch of the driver tree, and the one that fails. Unit revenue minus unit
            cost times capacity is the whole profit identity for an airline, and the first term is
            negative.
          </p>
          <div className="mt-10 space-y-16">
            <RegisteredExhibit id="unit_spread" />
            <RegisteredExhibit id="margin_ladder" />
            <RegisteredExhibit id="cost_stack" />
          </div>
        </section>

        <section>
          <h2 className="font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">
            Can it win the passenger?
          </h2>
          <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
            The competitive branch. The carrier IndiGo is trying to take the connecting passenger
            from earns roughly double per passenger kilometre, which is both the size of the prize
            and the measure of the climb.
          </p>
          <div className="mt-10 space-y-16">
            <RegisteredExhibit id="competitive_position" />
          </div>
        </section>

        <section>
          <h2 className="font-serif text-[clamp(1.4rem,2.6vw,2rem)] font-semibold">
            How large is the commitment, and can the operation carry it?
          </h2>
          <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
            Scale without a price, because no aircraft price is verifiable here. Then the
            utilisation figure that converts an order book into capacity, and the cross-check that
            makes it trustworthy.
          </p>
          <div className="mt-10 space-y-16">
            <RegisteredExhibit id="capital_scale" />
            <RegisteredExhibit id="operations" />
          </div>
        </section>
      </div>

      <section className="mt-20 border-t-2 border-red pt-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red">
          So what
        </p>
        <p className="mt-4 max-w-[62ch] font-serif text-[clamp(1.3rem,2.6vw,1.9rem)] font-semibold leading-snug">
          A commitment worth a year of earnings, onto a cost base with no spread, in a market where
          the incumbent earns double per kilometre.
        </p>
        <p className="mt-4 max-w-[64ch] text-[15px] leading-relaxed text-ink/75">
          That is not an argument against the order, which is already firm. It is the argument for
          being right about where the aircraft go. Every point of yield headroom matters more when
          the starting spread is{" "}
          <span className="tnum font-medium text-red">{spread.spread.toFixed(2)}</span>, which is
          why the recommendation is sequenced by headroom rather than by traffic.{" "}
          <Link
            href="/story"
            className="underline decoration-light underline-offset-4 hover:text-red"
          >
            The argument for that sequence runs here
          </Link>
          .
        </p>
      </section>

      <footer className="mt-16 border-t border-light pt-6 text-[13px] leading-relaxed text-grey">
        {company.source}. This is a portfolio simulation, not a client engagement: IndiGo has not
        commissioned, seen or endorsed any of it.
      </footer>
    </main>
  );
}
