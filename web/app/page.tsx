import Link from "next/link";

// P0 scaffold. The executive answer is prose that is already published and
// verified, so it can stand here now. Every NUMBER on this route arrives in P1
// from `src/app_export.py`, because the house rule is that no figure is written
// by hand: it is computed in-repo or it does not appear.

const DOORS = [
  {
    href: "/deck",
    label: "Walk it through",
    time: "5 minutes",
    body: "Fifteen slides, one exhibit each, the argument in the order a partner would hear it.",
  },
  {
    href: "/dashboard",
    label: "Explore it",
    time: "Interactive",
    body: "Filter by corridor, carrier and year. Move fuel, currency and yield and watch the answer hold or break.",
  },
  {
    href: "/methodology",
    label: "Check it",
    time: "For the sceptic",
    body: "Every field sourced and graded, the assumption gate, and six documented changes of mind.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-[1180px] px-8 py-20">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
        Commercial aviation &middot; India and the Gulf
      </p>

      <h1 className="mt-5 text-[clamp(2.5rem,6vw,4.25rem)] font-bold">
        India&rsquo;s Wide-Body Window
      </h1>

      <p className="mt-6 max-w-[36ch] font-serif text-[clamp(1.15rem,2vw,1.5rem)] leading-snug text-ink/75">
        Where should Indian carriers deploy their next 100 long-haul aircraft, and can the
        India-Gulf corridor absorb them?
      </p>

      <div className="mt-12 border-t-2 border-red pt-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-red">
          The answer
        </p>
        <p className="mt-4 max-w-[28ch] font-serif text-[clamp(1.75rem,4vw,2.75rem)] font-semibold leading-[1.15]">
          Compete with the Gulf hubs. Do not fly more aircraft to them.
        </p>
        <p className="mt-4 max-w-[52ch] text-ink/70">
          Europe first, North America second, Gulf capacity roughly flat. The corridor is still
          the prize. It is won by flying past it.
        </p>
      </div>

      <nav aria-label="Choose a route through the case" className="mt-16 grid gap-px bg-light sm:grid-cols-3">
        {DOORS.map((d) => (
          <Link
            key={d.href}
            href={d.href}
            className="group bg-paper p-7 transition-colors hover:bg-wash focus-visible:bg-wash focus-visible:outline-2 focus-visible:outline-red"
          >
            <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-grey">
              {d.time}
            </span>
            <span className="mt-2 block font-serif text-2xl font-semibold group-hover:text-red">
              {d.label}
            </span>
            <span className="mt-3 block text-[15px] leading-relaxed text-ink/70">{d.body}</span>
          </Link>
        ))}
      </nav>

      <p className="mt-16 border-t border-light pt-6 text-[13px] text-grey">
        A self-directed case in the style of Bain Capability Network Advanced Manufacturing
        &amp; Services commercial aviation work. Not a client engagement, and it says so.{" "}
        <a
          className="underline decoration-light underline-offset-4 hover:text-red"
          href="https://doginfantry.github.io/india-widebody-window/"
        >
          The full analysis site
        </a>{" "}
        remains the reproducible mirror.
      </p>
    </main>
  );
}
