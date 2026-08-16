"""Map the job description to what this repo actually evidences.

Built to report honestly, not to score well. Two design choices follow from that
and both cost coverage points:

1. **Artifacts are checked for existence, not assumed.** A requirement whose
   evidence file has not been written yet reports as missing, so the number
   falls when the repo is incomplete instead of describing an intended repo.

2. **Requirements with no honest evidence are listed as gaps, not stretched to
   fit.** The posting asks for survey analysis and for first-level team
   management with performance discussions. A solo repository cannot evidence
   either. Claiming them via some adjacent artifact would be the exact failure
   mode this tool exists to expose.

A coverage figure engineered upward is worthless. One that names what is missing
is a statement about judgement, which is the thing being assessed.

    python -m src.gap_analyzer
    python -m src.gap_analyzer --write   # refresh docs/coverage.md
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JD_PATH = ROOT / "jd.txt"
OUT_PATH = ROOT / "docs" / "coverage.md"


@dataclass(frozen=True)
class Requirement:
    """One line from the posting, and what in this repo answers it.

    `phrase` must appear verbatim in jd.txt. That is deliberate: it stops the
    requirement list drifting into a flattering paraphrase of the job, and the
    check fails loudly if the posting is ever replaced with a different one.
    """

    phrase: str
    label: str
    artifacts: tuple[str, ...]
    note: str = ""

    def evidence(self) -> list[tuple[str, bool]]:
        return [(a, (ROOT / a).exists()) for a in self.artifacts]

    @property
    def covered(self) -> bool:
        return bool(self.artifacts) and all(ok for _, ok in self.evidence())


# Phrases lifted verbatim from the posting. Where the posting repeats itself,
# the first occurrence is used.
REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        "go-to-market strategies",
        "Go to market strategy",
        ("docs/storyline.md", "src/market_sizing.py"),
        "Where to deploy incoming wide-body capacity, sized three ways",
    ),
    Requirement(
        "industry analysis",
        "Industry analysis",
        ("src/benchmarking.py", "docs/assets/charts/corridor_scale.json"),
        "India international market by corridor, carrier and stage length",
    ),
    Requirement(
        "competitive benchmarking",
        "Competitive benchmarking",
        ("src/benchmarking.py", "docs/assets/charts/stage_length_gap.json"),
        "Indian carriers against Gulf carriers on share, load factor and stage length",
    ),
    Requirement(
        "excel models",
        "Model building",
        ("src/market_sizing.py", "src/data_pipeline.py"),
        "Reimagined in Python. Repo rule forbids Excel as output or intermediate",
    ),
    Requirement(
        "survey analysis",
        "Survey analysis",
        (),
        "NOT EVIDENCED. No survey data exists and fabricating one would be dishonest",
    ),
    Requirement(
        "ad-hoc studies",
        "Ad hoc investigation",
        ("data/data_dictionary.md",),
        "The Rome to Delhi discrepancy: found by cross-check, investigated, left unresolved and quarantined",
    ),
    Requirement(
        "business judgment to derive answers in \nsituations where data is not easily available",
        "Judgement where data is thin",
        ("data/manual/assumptions.csv", "src/data_pipeline.py"),
        "Assumption status gate, disputed route quarantine, provisional sizing band",
    ),
    Requirement(
        "secondary research",
        "Secondary research",
        ("data/data_dictionary.md", "NOTICE"),
        "Every field sourced, dated and reliability graded; conflicts flagged not resolved",
    ),
    Requirement(
        "story lining skills",
        "Storylining",
        ("docs/storyline.md", "docs/index.html"),
        "SCQA structure, answer-first titles enforced by test",
    ),
    Requirement(
        "baselining and benchmarking of global best practices",
        "Global best practice baselining",
        ("src/benchmarking.py", "docs/assets/charts/who_carries_india.json"),
        "Gulf carriers as the benchmark holding a quarter of India's own market",
    ),
    Requirement(
        "driving the analysis on complex cases",
        "Drives complex analysis",
        ("src/market_sizing.py", "src/benchmarking.py", "tests/test_analysis.py"),
        "",
    ),
    Requirement(
        "Able to interface with primary client contact (Bain case teams from ME offices)",
        "Middle East orientation",
        ("docs/assets/charts/gateway_flows.json", "docs/storyline.md"),
        "The India-Gulf corridor is the spine of the case, not a footnote",
    ),
    Requirement(
        "acumen to \nsolve open-ended problems",
        "Open ended problem solving",
        ("docs/hypothesis_tree.md",),
        "Case decomposed into a MECE issue tree before any analysis",
    ),
    Requirement(
        "client development",
        "Client development support",
        ("docs/alternative_b_datacenters.md",),
        "A documented second case option, showing breadth beyond the flagship",
    ),
    Requirement(
        "mentor and coach \nanalysts providing feedback",
        "Mentoring and coaching analysts",
        (),
        "NOT EVIDENCED. A solo repo cannot show feedback conversations. Tests and review notes are a proxy at best",
    ),
    Requirement(
        "first-level team management responsibility",
        "First level team management",
        (),
        "NOT EVIDENCED. Same reason. Allocating and reviewing work needs a team",
    ),
    # A "Quality assurance" requirement sat here until the phrase-drift check
    # flagged that "QA" appears nowhere in the posting. It was a flattering row
    # describing the repo rather than the job, so it was removed rather than
    # reworded to survive. The tests still serve as evidence under "drives the
    # analysis on complex cases", where they genuinely belong.
    Requirement(
        "Proficient in research and analysis",
        "Research and analysis",
        ("src/data_pipeline.py", "data/data_dictionary.md"),
        "Two agencies reconciled to 2.6 per cent across seven countries",
    ),
)


def _normalise(text: str) -> str:
    return " ".join(text.split()).lower()


def verify_phrases(jd_text: str) -> list[Requirement]:
    """Return requirements whose phrase is NOT in the posting.

    Guards against the requirement list quietly becoming a description of the
    repo rather than of the job.
    """
    haystack = _normalise(jd_text)
    return [r for r in REQUIREMENTS if _normalise(r.phrase) not in haystack]


def report(jd_path: Path = JD_PATH) -> str:
    jd_text = jd_path.read_text(encoding="utf-8") if jd_path.exists() else ""
    drifted = verify_phrases(jd_text) if jd_text else list(REQUIREMENTS)

    covered = [r for r in REQUIREMENTS if r.covered]
    gaps = [r for r in REQUIREMENTS if not r.covered]
    pct = 100 * len(covered) / len(REQUIREMENTS)

    lines = [
        "# Job description coverage",
        "",
        f"**{len(covered)} of {len(REQUIREMENTS)} requirements evidenced ({pct:.0f}%).**",
        "",
        "Generated by `python -m src.gap_analyzer` against the posting in `jd.txt`.",
        "Every artifact below is checked for existence, so this number falls when the",
        "repo is incomplete rather than describing an intended repo.",
        "",
        "Requirements with no honest evidence are listed as gaps rather than stretched",
        "to fit an adjacent artifact. A coverage figure engineered upward is worthless.",
        "",
        "| Requirement | Evidence | Status |",
        "|---|---|---|",
    ]

    for r in REQUIREMENTS:
        if r.artifacts:
            ev = "<br>".join(
                f"{'`' + a + '`' if ok else '~~`' + a + '`~~ *(missing)*'}" for a, ok in r.evidence()
            )
        else:
            ev = "_none_"
        status = "yes" if r.covered else "**gap**"
        note = f"<br><sub>{r.note}</sub>" if r.note else ""
        lines.append(f"| **{r.label}**{note} | {ev} | {status} |")

    if gaps:
        lines += ["", "## Gaps, stated plainly", ""]
        for r in gaps:
            missing = [a for a, ok in r.evidence() if not ok]
            reason = r.note if not r.artifacts else f"artifact not yet written: {', '.join(missing)}"
            lines.append(f"- **{r.label}**: {reason}")

    if drifted:
        lines += [
            "",
            "## Warning: requirement text not found in the posting",
            "",
            "These phrases are not present in `jd.txt`, which means either the posting",
            "changed or the requirement list has drifted away from it.",
            "",
        ]
        lines += [f"- `{r.phrase.strip()}` ({r.label})" for r in drifted]

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jd", type=Path, default=JD_PATH)
    parser.add_argument("--write", action="store_true", help="write docs/coverage.md")
    args = parser.parse_args()

    text = report(args.jd)
    if args.write:
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(text, encoding="utf-8")
        print(f"wrote {OUT_PATH.relative_to(ROOT)}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
