import type { Metadata } from "next";
import { access, evidence } from "@/lib/data";

export const metadata: Metadata = { title: "Methodology" };

// The Granular level, and the page the rest of the project's claim rests on.
// Everything here is counted from the repo rather than asserted: the assumption
// ledger is read from data/manual/assumptions.csv, the pivots from
// docs/pivot_log.md, the coverage score from docs/coverage.md. If the gate is
// widened or a row clears, this page moves on the next export.
//
// No charts. A provenance page that needs a chart to make its point does not
// have a point.

const { assumptions, pivots, coverage } = evidence;

const STATUS_NOTE: Record<string, string> = {
  VERIFIED: "checked against the primary source named in the row",
  CORRECTED_VERIFIED: "the sheet value was wrong; corrected against the primary source",
  UNVERIFIED_NO_PRIMARY: "plausible, and no primary source exists to check it against",
  NOT_AVAILABLE: "the figure is not published by anyone",
  MODELED: "no one publishes it, so it is a labelled modelled knob with a sensitivity beside it",
};

export default function Methodology() {
  const cleared = Math.round((100 * assumptions.usable) / assumptions.total);

  return (
    <main className="mx-auto max-w-[1180px] px-8 py-14">
      <header className="max-w-[62ch]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
          Methodology
        </p>
        <h1 className="mt-4 font-serif text-[clamp(2rem,5vw,3.25rem)] font-bold leading-[1.1]">
          What can be checked, and what cannot
        </h1>
        <p className="mt-5 text-[17px] leading-relaxed text-ink/75">
          Every hard number in this case is either computed in-repo from committed data, or it
          is a hand-entered value that had to clear a gate before any module could read it.
          This page is the ledger. It is counted from the repository on every build, so it
          cannot flatter itself.
        </p>
      </header>

      <section className="mt-14 grid gap-px bg-light sm:grid-cols-3">
        {[
          { v: `${assumptions.total}`, l: "hand-entered values in the whole project", n: "everything else is computed from source data" },
          { v: `${cleared}%`, l: `cleared the gate (${assumptions.usable} of ${assumptions.total})`, n: `only ${assumptions.usable_statuses.join(" and ")} may be read by a module` },
          { v: `${coverage.pct}%`, l: `of the job description evidenced (${coverage.evidenced} of ${coverage.total})`, n: "self-scored, and deliberately not engineered upward" },
        ].map((k) => (
          <div key={k.l} className="bg-paper p-6">
            <p className="tnum font-serif text-[2.5rem] font-semibold leading-none text-red">
              {k.v}
            </p>
            <p className="mt-3 text-[15px] font-medium leading-snug">{k.l}</p>
            <p className="mt-2 text-[12.5px] leading-relaxed text-grey">{k.n}</p>
          </div>
        ))}
      </section>

      <section className="mt-16">
        <h2 className="font-serif text-2xl font-semibold">The gate</h2>
        <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
          A hand-entered number is unusable until a person has checked it against a named
          primary source. Asking for one that has not cleared raises, and the module simply
          cannot run. It has blocked real work rather than being relaxed, which is the only
          evidence that a gate is real.
        </p>

        <ul className="mt-6 space-y-2">
          {assumptions.by_status.map((s) => {
            const usable = assumptions.usable_statuses.includes(s.status);
            return (
              <li key={s.status} className="flex flex-wrap items-center gap-3 text-[14px]">
                <span className="tnum w-8 text-right font-semibold">{s.count}</span>
                <span className="h-4" style={{ width: `${(s.count / assumptions.total) * 320}px`, background: usable ? "#999999" : "#CC0000" }} />
                <span className="font-medium">{s.status}</span>
                <span className="text-grey">{STATUS_NOTE[s.status]}</span>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="mt-16">
        <h2 className="font-serif text-2xl font-semibold">
          The {assumptions.open} that never cleared, and why they never will
        </h2>
        <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
          These are terminal, not a to-do list. Naming them is the point: a case that reports
          only what it could verify, without saying what it could not, is telling half the
          story.
        </p>

        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-[13.5px]">
            <thead>
              <tr className="border-b border-ink">
                <th className="p-2 text-left font-semibold">Value</th>
                <th className="w-56 p-2 text-left font-semibold">Status</th>
                <th className="p-2 text-left font-semibold">Why it stays open</th>
              </tr>
            </thead>
            <tbody>
              {assumptions.open_rows.map((r) => (
                <tr key={r.key} className="border-b border-light align-top">
                  <td className="p-2 font-mono text-[12.5px]">{r.key}</td>
                  <td className="p-2 text-red">{r.status}</td>
                  <td className="p-2 leading-relaxed text-ink/75">{r.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-16">
        <h2 className="font-serif text-2xl font-semibold">
          {pivots.length} documented changes of mind
        </h2>
        <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
          Each is dated and cites the commit it happened in, including a claim that was
          published on the page and had to be withdrawn. An analysis that never bent under its
          own evidence was not really run.
        </p>

        <ol className="mt-6 space-y-px bg-light">
          {pivots.map((p) => (
            <li key={p.n} className="flex gap-5 bg-paper p-5">
              <span className="tnum font-serif text-3xl font-semibold text-red">{p.n}</span>
              <span className="text-[15px] leading-relaxed">{p.title}</span>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-16">
        <h2 className="font-serif text-2xl font-semibold">Where the numbers are checked twice</h2>
        <p className="mt-3 max-w-[68ch] text-[15px] leading-relaxed text-ink/75">
          Two agencies measuring the same routes from opposite ends agree to 2.6% across seven
          countries, and DGCA reconciles with IndiGo&rsquo;s own published block hours to 0.31%.
          That is the good news. The bad news is that only 5.6% of India&rsquo;s international
          traffic has a second agency covering it at all, and the Gulf, which carries half the
          traffic, has no equivalent open source.
        </p>

        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[560px] border-collapse text-[13.5px]">
            <thead>
              <tr className="border-b border-ink">
                <th className="p-2 text-left font-semibold">Gulf point</th>
                <th className="p-2 text-right font-semibold">Seats a week, implied</th>
                <th className="p-2 text-right font-semibold">Reported entitlement</th>
                <th className="p-2 text-right font-semibold">Used</th>
              </tr>
            </thead>
            <tbody>
              {access.entitlements.map((e) => (
                <tr key={e.foreign_point} className="border-b border-light">
                  <td className="p-2">{e.foreign_point}</td>
                  <td className="tnum p-2 text-right">
                    {Math.round(e.implied_seats_per_week).toLocaleString()}
                  </td>
                  <td className="tnum p-2 text-right">
                    {Math.round(e.reported_entitlement_both_sides).toLocaleString()}
                  </td>
                  <td className="tnum p-2 text-right font-semibold">
                    {e.utilisation_pct.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[12.5px] leading-relaxed text-grey">
          The entitlement figures themselves are the weakest link in the recommendation: India
          publishes no entitlement table, so they carry{" "}
          <span className="text-red">UNVERIFIED_NO_PRIMARY</span> and are corroborated only from
          the traffic end.
        </p>
      </section>

      <footer className="mt-16 border-t border-light pt-6 text-[13px] leading-relaxed text-grey">
        Full provenance for every field, with source, pull date and reliability grade, is in{" "}
        <a
          className="underline decoration-light underline-offset-4 hover:text-red"
          href="https://github.com/DogInfantry/india-widebody-window/blob/main/data/data_dictionary.md"
        >
          the data dictionary
        </a>
        , and the pivots in full are in{" "}
        <a
          className="underline decoration-light underline-offset-4 hover:text-red"
          href="https://github.com/DogInfantry/india-widebody-window/blob/main/docs/pivot_log.md"
        >
          the pivot log
        </a>
        . This is a portfolio simulation, not a client engagement.
      </footer>
    </main>
  );
}
