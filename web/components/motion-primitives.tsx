"use client";

import { useEffect, useRef, useState } from "react";
import { animate, useInView, useReducedMotion } from "motion/react";

// Motion, on page chrome only, and only where it earns the bytes.
//
// **The boundary, because it is the reason motion is allowed in at all.**
// `web/lib/chart-theme.ts` carries the rule "No animation on load" and every
// Recharts series sets `isAnimationActive={false}`. That does not change. A bar
// that grows every time it enters the viewport re-orders the reader's attention,
// which is what the one-red-element discipline exists to prevent.
// `tests/test_delivery.py` fails the build if a series turns animation on.
//
// **`Reveal` does NOT use Motion, and the reason is measured rather than
// stylistic.** It was built on `LazyMotion` + `m.div` + `whileInView` first, and
// that version wrote `opacity:0;transform:translateY(12px)` into the exported
// HTML on six wrappers, because Motion renders `initial` as an inline style
// during a static export. With JavaScript off, or on a printed page where
// `once: true` never fires for a section that was never scrolled to, that is not
// a missing animation. It is missing content. `grep -o 'opacity:0' web/out/
// index.html` counted six; it counts zero now.
//
// The fix is to invert the default. **Content is visible in the HTML and stays
// visible unless JavaScript is present AND the element is below the fold AND the
// reader has not asked for reduced motion.** Nothing can hide content by
// failing, only by succeeding. That is one `IntersectionObserver` and two CSS
// rules, and it is less code than the version it replaced.
//
// **Neither the reveal nor the count-up can be verified in the Browser pane, and
// that is gotcha 33, not a bug here.** The pane does not composite frames when
// hidden, so `IntersectionObserver` never fires in it: a native observer
// attached by hand in the console never received a single callback either. Both
// of these are progressive enhancements that degrade to the correct static page,
// which IS verifiable, and that is the property worth guaranteeing anyway.
//
// Motion stays for `CountUp`, where `useInView` and `animate` do real work
// (interpolation, easing, cancellation) and where no content is at stake: if it
// never runs, the reader sees the right number, still.

/** One build per section: fade and a short rise, once, on entry.
 *
 *  Deliberately not staggered per child and deliberately not a slide. Animate to
 *  REVEAL, not to decorate: a section that arrives is a section the reader has
 *  scrolled to, and anything more expressive is the page talking about itself.
 *
 *  An element already on screen at mount is never hidden, so nothing above the
 *  fold flashes and the first paint is the real page. */
export function Reveal({ children, className }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    // Below the fold or nothing. Hiding what the reader is already looking at
    // would be a flash, not a reveal.
    if (el.getBoundingClientRect().top < window.innerHeight) return;

    el.dataset.revealState = "hidden";
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            el.dataset.revealState = "shown";
            io.disconnect();
          }
        }
      },
      { rootMargin: "0px 0px -80px 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div ref={ref} data-reveal className={className}>
      {children}
    </div>
  );
}

const PARTS = /^([+-]?)([\d.]+)(.*)$/;

/** A hero KPI that counts up, and only when counting up is honest.
 *
 *  **Hydration safety is the whole design.** This is a static export, so the
 *  server renders the real figure into the HTML and a reader with no JavaScript
 *  sees the right number. Starting at zero on mount would knock a correct number
 *  back to nothing in front of the reader.
 *
 *  So, the same rule as `Reveal`: if the element is already in view when it
 *  mounts it never animates. Only a KPI scrolled down to counts up. Above the
 *  fold the figure is simply correct and still, which reads better anyway.
 *
 *  Values arrive as strings from the export ("88.8%", "2.0x", "+78%"), so the
 *  numeral is parsed out and the sign and suffix pass through untouched. Nothing
 *  here recomputes a number. */
export function CountUp({ value, className }: { value: string; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const reduced = useReducedMotion();

  const [shown, setShown] = useState<string | null>(null);
  const visibleAtMount = useRef<boolean | null>(null);

  useEffect(() => {
    if (visibleAtMount.current === null) visibleAtMount.current = inView;

    const parsed = PARTS.exec(value);
    if (!parsed || reduced || visibleAtMount.current || !inView) return;

    const [, sign, digits, suffix] = parsed;
    const places = digits.includes(".") ? digits.split(".")[1].length : 0;

    const controls = animate(0, parseFloat(digits), {
      duration: 0.85,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setShown(`${sign}${v.toFixed(places)}${suffix}`),
      onComplete: () => setShown(null),
    });
    return () => controls.stop();
  }, [inView, reduced, value]);

  return (
    <span ref={ref} className={className}>
      {shown ?? value}
    </span>
  );
}
