"""Tidy JSON for the Next.js delivery layer.

**Why this file exists.** `docs/assets/charts/*.json` holds Plotly *figure specs*,
not data: trace arrays are frequently binary encoded and the layout is baked in.
A React chart needs the records, so the app would otherwise re-derive them and
the two surfaces would drift within a month.

**So nothing is recomputed here.** Every value comes from the same module
function the Plotly figure already calls. `corridor_scale()`, `profit_pool()`,
`corridor_economics()` and `corridor_freight()` all key on `region`, which is
what makes a single corridor spine possible and is what the dashboard
cross-filters on.

**No model arithmetic reaches TypeScript.** The scenario controls read a
precomputed cube exported here, so a slider can only ever index a value Python
produced. The alternative, porting the formulas, needs golden-fixture tests to
stay honest and drifts anyway.

**No timestamps.** A generated-at field would make the output differ on every
run and turn CI's refresh into permanent churn, which gotcha 14 already costs us
on parquet.

    python -m src.app_export          # write web/public/data/
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src import benchmarking as bm
from src import cargo as cg
from src import fleet_gap as fg
from src import market_sizing as ms
from src import options as opt
from src import profit_pools as pp
from src import scenario as sc

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "public" / "data"

# Rounding is applied once, here, rather than in every component. Six figures is
# far past anything displayed and keeps the diff stable across pandas versions.
PRECISION = 6


def _clean(obj: Any) -> Any:
    """Make anything the modules return JSON-safe without losing meaning."""
    if isinstance(obj, pd.DataFrame):
        return [_clean(r) for r in obj.to_dict(orient="records")]
    if isinstance(obj, pd.Series):
        return _clean(obj.to_dict())
    if is_dataclass(obj) and not isinstance(obj, type):
        return _clean(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, float):
        # NaN and inf are not JSON. `json.dumps` writes them as bare NaN /
        # Infinity, which every JSON.parse in the browser rejects, and pandas
        # produces them freely: the "Other" corridor has no hub, so it has no
        # stage length and no yield headroom. They become null.
        if obj != obj or obj in (float("inf"), float("-inf")):
            return None
        return round(obj, PRECISION)
    if hasattr(obj, "item"):  # numpy scalar
        return _clean(obj.item())
    if isinstance(obj, (str, int, bool)) or obj is None:
        return obj
    return str(obj)


def corridor_spine() -> list[dict]:
    """One row per corridor, every corridor-level metric joined onto it.

    This is the table the dashboard filters. Keeping it as one join rather than
    four parallel datasets is what lets a corridor click filter every exhibit at
    once without the client re-joining anything.
    """
    scale = bm.corridor_scale()
    econ = opt.corridor_economics()[
        ["region", "stage_km", "cask_at_stage", "breakeven_yield",
         "yield_headroom_pct", "reachable_by_narrowbody", "hub_iata", "hub_name"]
    ]
    pool = pp.profit_pool()[
        ["region", "rpk_bn", "revenue_inr_cr", "margin_pct", "profit_inr_cr",
         "pax_share_pct", "revenue_share_pct", "profit_share_pct"]
    ]
    freight = cg.corridor_freight()[["region", "freight_t", "kg_per_pax", "ftk_per_100_rpk"]]

    out = scale.merge(econ, on="region", how="left")
    out = out.merge(pool, on="region", how="left")
    out = out.merge(freight, on="region", how="left")
    return _clean(out)


def scenario_cube() -> dict:
    """Everything a control can reach, precomputed.

    `fuel_fx_sensitivity()` already returns the full move_pct grid, so the cube
    is that grid crossed with the three demand paths. A slider indexes it. It
    never computes.
    """
    return {
        "demand_paths": _clean(sc.scenario_paths()),
        "demand_table": _clean(sc.scenario_table()),
        "unit_economics": _clean(sc.unit_economics()),
        "cask_bridge": _clean(sc.cask_bridge()),
        "fuel_fx": _clean(sc.fuel_fx_sensitivity()),
        "dollar_exposure": _clean(sc.dollar_exposure()),
    }


def kpi_band() -> list[dict]:
    """Six numbers that carry the whole argument, computed rather than typed.

    Six because Vizro's dashboard method puts the readable range at five to nine
    per view, and because six is what it takes to state the case: how big the
    market is, how much of it touches the Gulf, who flies it today, what the
    order book would add, whether the Gulf has room for it, and whether the
    economics work there.

    **The first four are the static site's band, in its order and wording**, so
    `scripts/refresh.py` slices them off rather than keeping a second copy. Two
    surfaces, one computation.
    """
    corridor = bm.corridor_scale().set_index("region")
    carriers = bm.who_carries_india().set_index("carrier_group")
    intl = bm.load_dgca_intl_country()
    total = intl[intl["year"] == bm.INTL_COUNTRY_YEAR]["pax_total"].sum()
    gulf, europe = corridor.loc["Gulf"], corridor.loc["Europe"]
    stage = bm.carrier_operating_summary(
        bm.LATEST_COMPLETE_YEAR, international=True
    ).set_index("airline")

    book = 100 * fg.order_book_ask()["ask"] / fg.baseline().ask
    dubai = bm.dubai_entitlement_check()
    econ = opt.corridor_economics().set_index("region")

    from src import charts  # local: keeps the export importable without plotly loaded

    return [
        charts.kpi(
            f"{total / 1e6:.0f}M",
            "India international sector passengers",
            note=f"{bm.INTL_COUNTRY_YEAR}, both directions, all carriers (DGCA)",
        ),
        charts.kpi(
            f"{gulf['share_pct']:.0f}%",
            "of that traffic touches a Gulf point",
            note=f"{gulf['pax_total'] / 1e6:.1f}M passengers, "
            f"{gulf['pax_total'] / europe['pax_total']:.1f}x the entire direct Europe market",
        ),
        charts.kpi(
            f"{carriers.loc['Indian', 'share_pct']:.0f}%",
            "is flown by Indian carriers",
            note="Gulf carriers take a quarter of India's own international market",
        ),
        charts.kpi(
            f"{stage.loc['Air India', 'stage_length_km'] / stage.loc['IndiGo', 'stage_length_km']:.1f}x",
            "Air India's average international flight vs IndiGo's",
            note=f"{stage.loc['Air India', 'stage_length_km']:,.0f} km against "
            f"{stage.loc['IndiGo', 'stage_length_km']:,.0f} km, {bm.LATEST_COMPLETE_YEAR}",
        ),
        charts.kpi(
            f"+{book:.0f}%",
            "is what the firm order book would add to international capacity",
            note="46,546 seats converted to ASK at computed block speed and sector length",
        ),
        charts.kpi(
            f"{dubai['utilisation_pct']:.1f}%",
            "of the India-Dubai seat entitlement is already used",
            note=f"Gulf yield headroom {econ.loc['Gulf', 'yield_headroom_pct']:+.1f}% against "
            f"Europe {econ.loc['Europe', 'yield_headroom_pct']:+.1f}%",
        ),
    ]


_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_EMPH = re.compile(r"\*\*|\*|`")


def _markdown_table(doc: Path, heading: str) -> list[dict]:
    """Read one markdown table out of a written-IP file, by the heading above it.

    The option menu and the nine-row risk register are **judgement**, not
    computation: a likelihood of "High" is an argued position, and there is no
    module that returns it. They are also already written, reviewed and shipped
    in `docs/recommendation.md`.

    So they are parsed rather than retyped. Retyping them into TypeScript would
    have created a second copy of the argument that drifts silently from the one
    a reader is pointed at, which is the exact failure `tests/test_narrative.py`
    exists to catch on the prose side.
    """
    lines = doc.read_text(encoding="utf-8").splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == heading)
    rows: list[dict] = []
    header: list[str] | None = None
    for ln in lines[start + 1 :]:
        if ln.startswith("#"):
            break
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue  # the ---|--- separator
        cells = [_MD_EMPH.sub("", _MD_LINK.sub(r"\1", c)) for c in cells]
        if header is None:
            header = cells
        else:
            rows.append(dict(zip(header, cells)))
    if not rows:
        raise ValueError(f"no table found under {heading!r} in {doc.name}")
    return rows


def narrative() -> dict:
    reco = ROOT / "docs" / "recommendation.md"
    return {
        "options": _markdown_table(reco, "## The options, and what each needs to be true"),
        "risks": _markdown_table(reco, "## Risk register"),
    }


DATASETS: dict[str, Any] = {
    "kpis": kpi_band,
    "narrative": narrative,
    "corridors": corridor_spine,
    "carriers": lambda: {
        "who_carries_india": _clean(bm.who_carries_india()),
        "share_trend": _clean(bm.carrier_share_trend()),
        # NAMED, not defaulted. `carrier_operating_summary()` returns DOMESTIC
        # unless told otherwise, and a domestic stage length of 943 km read as
        # an international one would have made the capability exhibit claim the
        # opposite of what it shows: IndiGo's INTERNATIONAL stage is 2,643 km
        # against Air India's 5,316 km, and that gap is the whole point.
        "domestic_summary": _clean(bm.carrier_operating_summary()),
        "international_summary": _clean(
            bm.carrier_operating_summary(bm.LATEST_COMPLETE_YEAR, international=True)
        ),
    },
    "market": lambda: {
        "triangulation": _clean(ms.triangulate()),
        "trend": _clean(ms.estimate_trend()),
        "propensity": _clean(ms.estimate_propensity()),
        "capacity": _clean(ms.estimate_capacity()),
    },
    "fleet": lambda: {
        "baseline": _clean(fg.baseline()),
        "order_book": _clean(fg.order_book_ask()),
        "absorption_frontier": _clean(fg.absorption_frontier()),
        "absorption_summary": _clean(fg.absorption_summary()),
        "gap_path": _clean(fg.gap_path()),
        "gap_band": _clean(fg.gap_band()),
        "gulf_headroom": _clean(fg.gulf_headroom_against_order_book()),
    },
    "economics": lambda: {
        "reference": _clean(opt.reference()),
        "value_at_stake": _clean(opt.value_at_stake()),
        "connect_gap": _clean(opt.connect_gap()),
        "option_menu": _clean(opt.option_menu()),
        "sensitivity": _clean(opt.sensitivity()),
    },
    "access": lambda: {
        "entitlements": _clean(bm.gulf_entitlement_check()),
        "seat_usage": _clean(bm.bilateral_seat_usage()),
        "gateway_flows": _clean(bm.gateway_flows()),
    },
    "scenario_cube": scenario_cube,
}


def write_all() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for name, build in DATASETS.items():
        path = OUT / f"{name}.json"
        # allow_nan=False makes a leaked NaN a build failure rather than a page
        # that renders blank charts in production.
        payload = json.dumps(build(), indent=1, sort_keys=True, allow_nan=False)
        path.write_text(payload + "\n", encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    for path in write_all():
        print(f"  {path.relative_to(ROOT).as_posix():<40} {path.stat().st_size:>9,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
