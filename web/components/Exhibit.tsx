import type { ReactNode } from "react";

// The T-model, which is how BCG decks are built: a simple top-level story, with
// the detail opened on demand rather than set beside it. That is the fix for
// this project's actual problem, which was 85 paragraphs sitting next to 18
// charts. The prose is not deleted, it is demoted behind a disclosure, so the
// page reads as a deliverable and the rigour is still one click away.
//
// The title is the takeaway, never the topic. A test enforces that on the
// Python side and it holds here too.

export function Exhibit({
  title,
  source,
  evidence,
  children,
  className = "",
}: {
  title: string;
  source: string;
  evidence: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <figure className={`border-t border-light pt-6 ${className}`}>
      <figcaption>
        <h3 className="max-w-[46ch] text-[clamp(1.05rem,1.6vw,1.35rem)] font-semibold leading-snug">
          {title}
        </h3>
      </figcaption>

      <div className="mt-5">{children}</div>

      <details className="group mt-4 border-t border-light pt-3">
        <summary className="cursor-pointer list-none text-[13px] font-medium text-grey transition-colors hover:text-red focus-visible:outline-2 focus-visible:outline-red">
          <span className="inline-block w-4 transition-transform group-open:rotate-90">›</span>
          The evidence
        </summary>
        <div className="mt-3 max-w-[68ch] space-y-3 pl-4 text-[14px] leading-relaxed text-ink/70">
          {evidence}
          <p className="text-[12px] text-grey">{source}</p>
        </div>
      </details>
    </figure>
  );
}
