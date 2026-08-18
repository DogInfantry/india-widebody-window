// Every number this app renders enters through this file, and every one of them
// was computed by the Python layer in `src/app_export.py`. Nothing is typed by
// hand and nothing is recalculated in TypeScript: a control can only ever index
// a value Python already produced. That is the same provenance contract the
// analysis side runs on, carried across the language boundary.
//
// The JSON is imported rather than fetched because the app is a static export,
// so this resolves at build time and the data ships in the bundle.

import kpisJson from "@/public/data/kpis.json";
import corridorsJson from "@/public/data/corridors.json";
import carriersJson from "@/public/data/carriers.json";
import fleetJson from "@/public/data/fleet.json";
import economicsJson from "@/public/data/economics.json";
import accessJson from "@/public/data/access.json";
import marketJson from "@/public/data/market.json";
import narrativeJson from "@/public/data/narrative.json";
import evidenceJson from "@/public/data/evidence.json";
import scenarioCubeJson from "@/public/data/scenario_cube.json";

export type Kpi = { value: string; label: string; note: string | null };

export type Corridor = {
  region: string;
  pax_total: number;
  share_pct: number;
  stage_km: number | null;
  cask_at_stage: number | null;
  breakeven_yield: number | null;
  yield_headroom_pct: number | null;
  reachable_by_narrowbody: boolean | null;
  hub_iata: string | null;
  hub_name: string | null;
  rpk_bn: number | null;
  revenue_inr_cr: number | null;
  margin_pct: number | null;
  profit_inr_cr: number | null;
  pax_share_pct: number | null;
  revenue_share_pct: number | null;
  profit_share_pct: number | null;
  freight_t: number | null;
  kg_per_pax: number | null;
  ftk_per_100_rpk: number | null;
};

export const kpis = kpisJson as Kpi[];
export const corridors = corridorsJson as Corridor[];
export const carriers = carriersJson;
export const fleet = fleetJson;
export const economics = economicsJson;
export const access = accessJson;
export const market = marketJson;

/** The option menu and the nine-row risk register, parsed out of
 *  docs/recommendation.md by src/app_export.py rather than retyped, so the app
 *  and the written recommendation cannot disagree. */
export const narrative = narrativeJson;

/** The provenance ledger: assumption statuses, the pivot log and the coverage
 *  score, all counted from the repo by src/app_export.py on every build. */
export const evidence = evidenceJson;
export const scenarioCube = scenarioCubeJson;

/** Corridors that have a hub, so an economics figure exists for them. "Other"
 *  is a residual bucket with no single stage length and must not be plotted on
 *  an economics axis. */
export const economicCorridors = corridors.filter(
  (c): c is Corridor & { yield_headroom_pct: number; stage_km: number } =>
    c.yield_headroom_pct !== null && c.stage_km !== null,
);
