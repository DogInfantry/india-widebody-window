"use client";

import { useId, useState, type ReactNode } from "react";

// One exhibit grammar, reused everywhere, so a reader learns the interaction
// once on the first exhibit and never thinks about it again.
//
// This replaces a single "The evidence" disclosure. The disclosure was the right
// idea (the T-model: a simple top-level story, detail opened on demand) and the
// wrong shape, because it put three different KINDS of depth behind one flap.
// A partner pushing on an exhibit is asking one of exactly three questions, and
// they are not the same question:
//
//   "why do you believe that?"    -> Evidence
//   "where did the number come from?" -> How it was computed
//   "what would change your mind?" -> What would break it
//
// Four tabs is the cap and there is no nesting. If an exhibit needs a fifth, it
// is two exhibits. A tab with no content is not rendered, so nothing is ever an
// empty shell.

export const TAB_VOCABULARY = [
  "Exhibit",
  "Evidence",
  "How it was computed",
  "What would break it",
] as const;

export type TabName = (typeof TAB_VOCABULARY)[number];

export function Exhibit({
  anchor,
  title,
  source,
  evidence,
  computed,
  breaks,
  children,
  className = "",
}: {
  /** Anchor id, so the driver tree on the landing page can link to a specific
   *  exhibit. A leaf that points nowhere is decoration, and a test asserts none
   *  of them do. */
  anchor?: string;
  /** The takeaway, never the topic. A test enforces this on the Python side. */
  title: string;
  /** Where the numbers came from. Rendered under every tab, not hidden in one. */
  source: string;
  evidence?: ReactNode;
  computed?: ReactNode;
  breaks?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const [active, setActive] = useState<TabName>("Exhibit");
  const id = useId();

  const panels: Partial<Record<TabName, ReactNode>> = {
    Exhibit: children,
    Evidence: evidence,
    "How it was computed": computed,
    "What would break it": breaks,
  };
  const tabs = TAB_VOCABULARY.filter((t) => panels[t]);

  return (
    <figure id={anchor} className={`scroll-mt-24 border-t-2 border-ink pt-5 ${className}`}>
      <figcaption>
        <h3 className="max-w-[52ch] text-h3 font-semibold leading-snug">
          {title}
        </h3>
      </figcaption>

      {/* Only rendered when there is somewhere to go. A single-tab exhibit shows
          its chart with no chrome at all, which is the right amount of chrome. */}
      {/* Controls, not captions. These were 13px grey prose against 17px serif
          headings, far too close for the eye to sort "thing I read" from "thing I
          click". They are now deliberately NON-editorial: micro, sans, uppercase,
          tracked, with a resting surface. That is the same trick a caption uses to
          stop looking like body copy, run in reverse. */}
      {tabs.length > 1 && (
        <div role="tablist" aria-label="Exhibit detail" className="mt-4 flex flex-wrap gap-x-1 border-b border-light print:hidden">
          {tabs.map((t) => (
            <button
              key={t}
              type="button"
              role="tab"
              id={`${id}-tab-${t}`}
              aria-selected={active === t}
              aria-controls={`${id}-panel-${t}`}
              onClick={() => setActive(t)}
              className={`-mb-px border-b-2 px-2.5 pb-2 pt-1.5 text-micro font-semibold uppercase tracking-[0.1em] transition-colors focus-visible:outline-2 focus-visible:outline-red ${
                active === t
                  ? "border-red bg-wash text-ink"
                  : "border-transparent text-grey hover:bg-wash hover:text-red"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {tabs.map((t) => (
        <div
          key={t}
          role="tabpanel"
          id={`${id}-panel-${t}`}
          aria-labelledby={`${id}-tab-${t}`}
          hidden={active !== t}
          // Print shows every panel: a PDF has no tabs to click, and a reader
          // holding the printed page should not lose the depth.
          className={active === t ? "mt-5" : "mt-5 hidden print:block"}
        >
          {t !== "Exhibit" && (
            <p className="mb-2 hidden text-micro font-semibold uppercase tracking-[0.14em] text-grey print:block">
              {t}
            </p>
          )}
          <div
            className={
              t === "Exhibit"
                ? // Wide charts scroll inside their own box. Direct labels at a
                  // line's end are the right form and they do not always fit a
                  // 375px screen; letting the page scroll instead would break
                  // every other exhibit on it.
                  "overflow-x-auto"
                : "max-w-[68ch] space-y-3 text-body leading-relaxed text-ink/75"
            }
          >
            {panels[t]}
          </div>
        </div>
      ))}

      {/* The source line sits outside the tabs on purpose. Every exhibit carries
          one, and burying it inside a tab would make it conditional on a click. */}
      <p className="mt-4 max-w-[80ch] border-t border-light pt-3 text-caption leading-relaxed text-grey">
        {source}
      </p>
    </figure>
  );
}
