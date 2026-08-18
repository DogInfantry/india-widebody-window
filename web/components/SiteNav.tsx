"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Tier 1 of the three-tier navigation Vizro's dashboard method describes: global
// page nav here, page-level filter controls inside /dashboard, component-scoped
// interaction inside each exhibit. Keeping the tiers separate is what stops a
// filter looking like a navigation choice.

// Only routes that exist. /frameworks, /story, /deck and /methodology land in
// later phases; linking to them early would ship a 404 on a page whose whole
// claim is that it can be checked.
const PAGES = [
  { href: "/", label: "The answer" },
  { href: "/dashboard", label: "Dashboard" },
];

export function SiteNav() {
  const path = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-light bg-paper/95 backdrop-blur">
      <nav
        aria-label="Sections"
        className="mx-auto flex max-w-[1180px] flex-wrap items-baseline gap-x-6 gap-y-1 px-8 py-3"
      >
        <Link href="/" className="font-serif text-[15px] font-semibold hover:text-red">
          India&rsquo;s Wide-Body Window
        </Link>
        <span className="ml-auto flex flex-wrap gap-x-5 gap-y-1 text-[13px]">
          {PAGES.map((p) => {
            const active = path === p.href;
            return (
              <Link
                key={p.href}
                href={p.href}
                aria-current={active ? "page" : undefined}
                className={
                  active
                    ? "border-b-2 border-red pb-0.5 font-medium text-ink"
                    : "pb-0.5 text-grey hover:text-red"
                }
              >
                {p.label}
              </Link>
            );
          })}
        </span>
      </nav>
    </header>
  );
}
