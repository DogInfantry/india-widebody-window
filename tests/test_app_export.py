"""The app's data must be the analysis layer's data.

`docs/assets/charts/*.json` and `web/public/data/*.json` are two renderings of
the same numbers for two different surfaces. The failure this file exists to
prevent is the one the project has already had twice in other forms: a surface
that keeps rendering while the numbers behind it stop agreeing with the modules.

The drift guard at the bottom is the one that matters. It is the same shape as
the chart-JSON check in `CLAUDE.md` gotcha 11: editing a module does NOT update
the committed export, so a stale file will pass every other test here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import app_export
from src import benchmarking as bm
from src import options as opt
from src import scenario as sc

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "public" / "data"


@pytest.fixture(scope="module")
def exported() -> dict[str, object]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(DATA.glob("*.json"))}


def test_every_declared_dataset_was_written(exported):
    assert set(exported) == set(app_export.DATASETS), (
        "web/public/data is out of step with app_export.DATASETS. Run "
        "`python -m src.app_export`."
    )


@pytest.mark.parametrize("name", sorted(app_export.DATASETS))
def test_the_export_is_strict_json(name):
    """NaN is not JSON, and pandas produces it freely.

    This shipped once: the "Other" corridor has no hub, so it has no stage
    length and no yield headroom, and `json.dumps` wrote a bare `NaN` that every
    `JSON.parse` in the browser rejects. The page would have rendered nothing
    and no Python test would have noticed.
    """
    raw = (DATA / f"{name}.json").read_text(encoding="utf-8")
    assert "NaN" not in raw and "Infinity" not in raw
    json.loads(raw)  # strict by default: raises on NaN


def test_the_export_is_deterministic(tmp_path, monkeypatch):
    """No timestamps, no dict ordering churn.

    A generated-at field would make every CI refresh a diff, which is the
    parquet churn of gotcha 14 all over again on files that are read by the
    build.
    """
    monkeypatch.setattr(app_export, "OUT", tmp_path)
    first = {p.name: p.read_bytes() for p in app_export.write_all()}
    second = {p.name: p.read_bytes() for p in app_export.write_all()}
    assert first == second


def test_the_corridor_spine_holds_every_corridor(exported):
    spine = exported["corridors"]
    assert {r["region"] for r in spine} == set(bm.corridor_scale()["region"])
    assert len({r["region"] for r in spine}) == len(spine), "a join fanned the spine out"


def test_the_spine_reports_what_the_modules_compute(exported):
    """Compared against the module, never re-derived. A re-derivation here would
    pass while both sides were wrong together."""
    spine = {r["region"]: r for r in exported["corridors"]}
    econ = opt.corridor_economics().set_index("region")

    for region in ("Gulf", "Europe", "North America"):
        assert spine[region]["yield_headroom_pct"] == pytest.approx(
            econ.loc[region, "yield_headroom_pct"], abs=1e-5
        ), f"{region} yield headroom on the app does not match options.corridor_economics()"

    # The finding the recommendation turns on. If this flips sign the answer
    # changed and the app must not be the last surface to hear about it.
    assert spine["Gulf"]["yield_headroom_pct"] < 0 < spine["Europe"]["yield_headroom_pct"]


def test_the_scenario_cube_covers_every_reachable_control_position(exported):
    """No model arithmetic runs in TypeScript, so a control can only index a
    value Python produced. If the grid is short, a slider position renders
    undefined."""
    cube = exported["scenario_cube"]
    grid = sc.fuel_fx_sensitivity()
    assert len(cube["fuel_fx"]) == len(grid)
    assert {row["move_pct"] for row in cube["fuel_fx"]} == set(grid["move_pct"])
    assert {row["scenario"] for row in cube["demand_table"]} == {"Bear", "Base", "Bull"}


def test_the_committed_export_matches_a_fresh_build(tmp_path, monkeypatch):
    """The guard that catches the stale file.

    Editing a module does not rewrite `web/public/data/`. Without this, the app
    keeps serving last month's numbers and every other test in this file passes
    against them.
    """
    monkeypatch.setattr(app_export, "OUT", tmp_path)
    stale = []
    for fresh in app_export.write_all():
        committed = DATA / fresh.name
        if committed.read_bytes() != fresh.read_bytes():
            stale.append(fresh.name)
    assert not stale, (
        f"{stale} differ from a fresh build. Run `python -m src.app_export` "
        "(or `python scripts/refresh.py --no-fetch`) and commit the result."
    )
