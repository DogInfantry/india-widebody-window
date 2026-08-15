"""Fetch, clean, and cache every source feeding the analysis.

Data flows one way and no step is skipped:

    source -> data/raw/<source>_<YYYYMMDD>.csv -> tidy DataFrame -> data/processed/*.parquet

Every loader returns a tidy DataFrame with four-digit years. Nothing here computes
analysis; that lives in the sibling modules.

Sources and licences are recorded in data/data_dictionary.md and NOTICE.

Two traps in the DGCA data that every loader must handle, because getting either
wrong silently doubles or halves headline numbers:

1. `Year` ships as a two-digit integer (15 means 2015). Left alone it sorts and
   filters wrongly and joins against nothing.
2. The carrier files carry `Total Domestic` and `Total International` rows as if
   they were airlines. Any groupby that forgets to drop them counts all traffic
   twice and reports market shares of roughly half their true value.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MANUAL = ROOT / "data" / "manual"

# DGCA traffic statistics, mirrored and cleaned by Vonter under ODbL.
# Original publisher is the Directorate General of Civil Aviation, Government of India.
DGCA_BASE = "https://raw.githubusercontent.com/Vonter/india-aviation-traffic/main/aggregated/"
DGCA_FILES = {
    "intl_country": "international/country.csv",
    "intl_city": "international/city.csv",
    "intl_carrier": "international/carrier.csv",
    "dom_carrier": "domestic/carrier.csv",
    "dom_city": "domestic/city.csv",
}

OURAIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
WORLDBANK_BASE = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"

# Eurostat air transport by airport pair. One dataset per reporting country,
# named avia_par_<cc>. Airport pair codes read <reporter>_<ICAO>_<partner>_<ICAO>,
# so India routes are the codes containing "_IN_".
EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
EUROSTAT_REPORTERS = (
    "de", "fr", "nl", "it", "es", "at", "be", "pl",
    "ch", "dk", "se", "fi", "pt", "ie", "el", "cz", "hu",
)

# The Gulf Cooperation Council six, spelled as DGCA spells them.
# This set defines the headline "Gulf share" figure, so it is explicit rather
# than inferred from a region lookup that could drift.
GULF6 = {
    "UNITED ARAB EMIRATES",
    "SAUDI ARABIA",
    "QATAR",
    "OMAN",
    "KUWAIT",
    "BAHRAIN",
}

# Region tags for the Mekko and the profit-pool split. Covers the countries
# carrying the overwhelming majority of India international traffic; everything
# unlisted falls to "Other", which is reported rather than hidden.
COUNTRY_REGION = {
    **{c: "Gulf" for c in GULF6},
    "SINGAPORE": "Southeast Asia",
    "THAILAND": "Southeast Asia",
    "MALAYSIA": "Southeast Asia",
    "INDONESIA": "Southeast Asia",
    "VIETNAM": "Southeast Asia",
    "PHILIPPINES": "Southeast Asia",
    "MYANMAR": "Southeast Asia",
    "CAMBODIA": "Southeast Asia",
    "UNITED KINGDOM": "Europe",
    "GERMANY": "Europe",
    "FRANCE": "Europe",
    "NETHERLANDS": "Europe",
    "ITALY": "Europe",
    "SPAIN": "Europe",
    "SWITZERLAND": "Europe",
    "AUSTRIA": "Europe",
    "POLAND": "Europe",
    "RUSSIA": "Europe",
    "TURKEY": "Europe",
    "UNITED STATES": "North America",
    "CANADA": "North America",
    "SRI LANKA": "South Asia",
    "NEPAL": "South Asia",
    "BANGLADESH": "South Asia",
    "MALDIVES": "South Asia",
    "BHUTAN": "South Asia",
    "PAKISTAN": "South Asia",
    "AFGHANISTAN": "South Asia",
    "CHINA": "East Asia",
    "HONG KONG": "East Asia",
    "JAPAN": "East Asia",
    "SOUTH KOREA": "East Asia",
    "KOREA": "East Asia",
    "TAIWAN": "East Asia",
    "AUSTRALIA": "Oceania",
    "NEW ZEALAND": "Oceania",
    "KENYA": "Africa",
    "ETHIOPIA": "Africa",
    "SOUTH AFRICA": "Africa",
    "EGYPT": "Africa",
    "TANZANIA": "Africa",
    "MAURITIUS": "Africa",
    "SEYCHELLES": "Africa",
    "NIGERIA": "Africa",
}

# Airlines headquartered in the Gulf. Used to split "who carries India's
# international traffic" between Indian, Gulf, and other foreign carriers.
GULF_CARRIERS = {
    "EMIRATES AIRLINE",
    "ETIHAD AIRLINES",
    "QATAR AIRWAYS",
    "AIR ARABIA",
    "SAUDIA",
    "OMAN AIR",
    "FLY DUBAI",
    "FLYDUBAI",
    "KUWAIT AIRWAYS",
    "GULF AIR",
    "AIR ARABIA ABU DHABI",
    "SALAM AIR",
    "JAZEERA AIRWAYS",
    "FLYNAS",
}

INDIAN_CARRIERS = {
    "INDIGO",
    "AIR INDIA",
    "AIR INDIA EXPRESS",
    "VISTARA AIRLINES",
    "VISTARA",
    "SPICEJET",
    "AKASA AIR",
    "GO FIRST",
    "GOAIR",
    "ALLIANCE AIR",
    "STAR AIR",
    "FLY91",
    "AIX CONNECT",
}


# --------------------------------------------------------------------------
# fetch and cache
# --------------------------------------------------------------------------


def _today() -> str:
    return _dt.date.today().strftime("%Y%m%d")


def _fetch(url: str, name: str, *, force: bool = False, timeout: int = 120) -> Path:
    """Download `url` to data/raw/<name>_<YYYYMMDD> and return the path.

    Today's file is reused unless `force`, so re-running the pipeline in a
    session does not hammer the source. Older stamps are left in place: they are
    the provenance record for figures already published.
    """
    RAW.mkdir(parents=True, exist_ok=True)
    suffix = ".json" if "format=json" in url else ".csv"
    path = RAW / f"{name}_{_today()}{suffix}"
    if path.exists() and not force:
        return path
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    path.write_bytes(resp.content)
    return path


def _norm_year(s: pd.Series) -> pd.Series:
    """Normalise DGCA's two-digit years to four digits.

    DGCA ships 15 for 2015. Values already at four digits pass through, so this
    is safe to apply to every frame regardless of which convention it uses.
    """
    y = pd.to_numeric(s, errors="coerce").astype("Int64")
    return y.where(y >= 1000, y + 2000)


def _drop_total_rows(df: pd.DataFrame, col: str = "airline") -> pd.DataFrame:
    """Remove the `Total Domestic` / `Total International` pseudo-airline rows.

    DGCA files these as if they were carriers. Any groupby that keeps them
    double counts every passenger and halves every market share.
    """
    return df[~df[col].astype(str).str.strip().str.lower().str.startswith("total")].copy()


# --------------------------------------------------------------------------
# DGCA loaders
# --------------------------------------------------------------------------


def _load_dgca(key: str, *, force: bool = False) -> pd.DataFrame:
    path = _fetch(DGCA_BASE + DGCA_FILES[key], f"dgca_{key}", force=force)
    return pd.read_csv(path)


def load_dgca_intl_country(*, force: bool = False) -> pd.DataFrame:
    """India to country international traffic, quarterly.

    Columns: year, quarter, country, region, pax_to_india, pax_from_india,
    pax_total, freight_to_india, freight_from_india, is_gulf.

    `pax_total` is both directions summed, which is the DGCA *sector* measure.
    It is not origin-destination: a Delhi to Dubai to London passenger appears
    here under the United Arab Emirates. That distinction is the whole case, so
    it is named here and never silently relabelled downstream.
    """
    df = _load_dgca("intl_country", force=force)
    df = df.rename(
        columns={
            "Year": "year",
            "Quarter": "quarter",
            "Country": "country",
            "PaxToIndia": "pax_to_india",
            "PaxFromIndia": "pax_from_india",
            "FreightToIndia": "freight_to_india",
            "FreightFromIndia": "freight_from_india",
        }
    )
    df["year"] = _norm_year(df["year"])
    df["country"] = df["country"].astype(str).str.strip().str.upper()
    df["pax_total"] = df["pax_to_india"] + df["pax_from_india"]
    df["region"] = df["country"].map(COUNTRY_REGION).fillna("Other")
    df["is_gulf"] = df["country"].isin(GULF6)
    return df


def load_dgca_intl_city(*, force: bool = False) -> pd.DataFrame:
    """International city-pair traffic, quarterly.

    DGCA is not consistent about which of city1 / city2 is the Indian point, so
    both are kept verbatim and `pax_total` sums the two directional flows.
    """
    df = _load_dgca("intl_city", force=force)
    df = df.rename(
        columns={
            "Year": "year",
            "Quarter": "quarter",
            "City1": "city1",
            "City2": "city2",
            "PaxToCity2": "pax_to_city2",
            "PaxFromCity2": "pax_from_city2",
            "FreightToCity2": "freight_to_city2",
            "FreightFromCity2": "freight_from_city2",
        }
    )
    df["year"] = _norm_year(df["year"])
    for c in ("city1", "city2"):
        df[c] = df[c].astype(str).str.strip().str.upper()
    df["pax_total"] = df["pax_to_city2"] + df["pax_from_city2"]
    return df


def load_dgca_intl_carrier(*, force: bool = False) -> pd.DataFrame:
    """International traffic by airline, unpivoted from quarterly to monthly.

    The source stores three months per quarterly row as column suffixes M1, M2
    and M3. This unpivots them into a `month` column, where month equals
    (quarter - 1) * 3 + m, so downstream code never has to know the layout.

    `Total *` pseudo-airlines are dropped here, once, so no caller can forget.
    """
    df = _load_dgca("intl_carrier", force=force)
    df = df.rename(columns={"Year": "year", "Quarter": "quarter", "Airline": "airline"})
    df["year"] = _norm_year(df["year"])
    df["airline"] = df["airline"].astype(str).str.strip().str.upper()
    df = _drop_total_rows(df, "airline")

    metrics = {
        "PaxToIndia": "pax_to_india",
        "PaxFromIndia": "pax_from_india",
        "FreightToIndia": "freight_to_india",
        "FreightFromIndia": "freight_from_india",
    }
    frames = []
    for m in (1, 2, 3):
        cols = {f"{src}M{m}": dst for src, dst in metrics.items()}
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise KeyError(f"DGCA intl carrier file is missing expected columns: {missing}")
        part = df[["year", "quarter", "airline"] + list(cols)].rename(columns=cols)
        part["month"] = (part["quarter"] - 1) * 3 + m
        frames.append(part)

    out = pd.concat(frames, ignore_index=True)
    out["pax_total"] = out["pax_to_india"] + out["pax_from_india"]
    out["carrier_group"] = "Other foreign"
    out.loc[out["airline"].isin(INDIAN_CARRIERS), "carrier_group"] = "Indian"
    out.loc[out["airline"].isin(GULF_CARRIERS), "carrier_group"] = "Gulf"
    return out.sort_values(["year", "month", "airline"]).reset_index(drop=True)


def load_dgca_domestic_carrier(*, force: bool = False) -> pd.DataFrame:
    """Monthly airline operating statistics: passengers, ASK, RPK, load factor.

    This is the richest file in the set. It carries both `ScheduledDomestic` and
    `ScheduledInternational` rows for Indian carriers, which is what makes the
    average stage length comparison possible: stage length is RPK divided by
    passengers, and the international rows separate a short-haul network from a
    long-haul one without any assumption at all.

    `Total *` pseudo-airlines are dropped here, once.

    Units. `rpk`, `ask` and `aircraft_km` are converted from DGCA's thousands to
    true passenger-km, seat-km and km. `pax` is already a raw count and is left
    alone. The tonne-kilometre and cargo columns are also published in thousands
    but are not converted, because nothing in this project reads them; convert
    them at the point of use if that changes.

    `aircraft_number` is DGCA's label, but the magnitudes (204 against 25,905
    passengers in a single month) show it counts departures, not fleet size. That
    reading is an inference from the data, not a documented DGCA definition, and
    is flagged as such in data_dictionary.md.
    """
    df = _load_dgca("dom_carrier", force=force)
    df = df.rename(
        columns={
            "Type": "service_type",
            "Airline": "airline",
            "Year": "year",
            "Month": "month",
            "Aircraft Number": "aircraft_number",
            "Aircraft Hours": "aircraft_hours",
            "Aircraft Kilometres": "aircraft_km",
            "Passenger Number": "pax",
            "Passenger Kilometers": "rpk",
            "Seat Kilometers": "ask",
            "Passenger Load Factor": "load_factor",
            "Freight": "freight",
            "Total Cargo": "total_cargo",
        }
    )
    df["year"] = _norm_year(df["year"])
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
    df["airline"] = df["airline"].astype(str).str.strip()
    df = _drop_total_rows(df, "airline")

    # DGCA reports every distance column in THOUSANDS while passenger counts are
    # raw. Converting here, once, rather than in each caller.
    #
    # Verified three independent ways before applying, because a silent factor of
    # 1000 here would put an average stage length of 5 km on a published chart:
    #   scale     thousands gives India domestic 163.8bn RPK for 2025, matching the
    #             industry figure of roughly 160 to 170bn. Raw implies 0.98 km per
    #             passenger, which is impossible.
    #   ratio     computed rpk/ask matches DGCA's own published load_factor column
    #             to within 0.25pp on the majors and 0.93pp worst case.
    #   coherence 204 departures against 120 aircraft-km and 25,905 passengers
    #             reconciles to 588 km per departure from the aircraft-km column
    #             and 589 km from the RPK column, two columns agreeing independently.
    for col in ("rpk", "ask", "aircraft_km"):
        df[col] = pd.to_numeric(df[col], errors="coerce") * 1000.0

    df["is_scheduled"] = df["service_type"].astype(str).str.startswith("Scheduled")
    df["is_international"] = df["service_type"].astype(str).str.contains("International")
    return df


def load_dgca_domestic_city(*, force: bool = False) -> pd.DataFrame:
    """Domestic city-pair traffic, monthly."""
    df = _load_dgca("dom_city", force=force)
    df = df.rename(
        columns={
            "Year": "year",
            "Month": "month",
            "City1": "city1",
            "City2": "city2",
            "PaxToCity2": "pax_to_city2",
            "PaxFromCity2": "pax_from_city2",
        }
    )
    df["year"] = _norm_year(df["year"])
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
    for c in ("city1", "city2"):
        df[c] = df[c].astype(str).str.strip().str.upper()
    df["pax_total"] = df["pax_to_city2"] + df["pax_from_city2"]
    return df


# --------------------------------------------------------------------------
# reference and macro
# --------------------------------------------------------------------------


def load_ourairports(*, force: bool = False) -> pd.DataFrame:
    """Airport reference data, CC0. Used for coordinates and great circle distance."""
    path = _fetch(OURAIRPORTS_URL, "ourairports", force=force)
    df = pd.read_csv(path, low_memory=False)
    keep = [
        "ident",
        "type",
        "name",
        "latitude_deg",
        "longitude_deg",
        "iso_country",
        "municipality",
        "iata_code",
    ]
    df = df[keep].copy()
    return df[df["type"].isin(["large_airport", "medium_airport"])].reset_index(drop=True)


def load_worldbank_macro(
    countries: str = "IND;ARE;QAT;SAU;OMN;KWT;BHR;CHN;USA;GBR;DEU;SGP",
    indicators: tuple[str, ...] = ("SP.POP.TOTL", "NY.GDP.PCAP.CD", "IS.AIR.PSGR"),
    start: int = 2000,
    end: int = 2025,
    *,
    force: bool = False,
) -> pd.DataFrame:
    """World Bank macro indicators, long format: country, iso3, indicator, year, value.

    Known limitation, stated rather than smoothed over: IS.AIR.PSGR (air transport
    passengers carried) has no values after 2023. It supports cross-country
    elasticity fitting, not current-year sizing. Anything downstream that projects
    from it must say so on the chart.
    """
    frames = []
    for ind in indicators:
        url = (
            WORLDBANK_BASE.format(countries=countries, indicator=ind)
            + f"?format=json&per_page=2000&date={start}:{end}"
        )
        path = _fetch(url, f"worldbank_{ind.replace('.', '_')}", force=force)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if len(payload) < 2 or payload[1] is None:
            continue
        frames.append(
            pd.DataFrame(
                [
                    {
                        "country": r["country"]["value"],
                        "iso3": r["countryiso3code"],
                        "indicator": ind,
                        "year": int(r["date"]),
                        "value": r["value"],
                    }
                    for r in payload[1]
                ]
            )
        )
    if not frames:
        raise RuntimeError("World Bank returned no data for any indicator")
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["indicator", "iso3", "year"])
        .reset_index(drop=True)
    )


def _jsonstat_to_frame(payload: dict) -> pd.DataFrame:
    """Flatten a Eurostat JSON-stat response into a tidy frame.

    JSON-stat stores values against a single flat index computed row-major over
    the dimensions listed in `id` with lengths in `size`. This walks that index
    back out into one column per dimension.
    """
    ids: list[str] = payload["id"]
    sizes: list[int] = payload["size"]

    # position -> category code, per dimension
    code_by_pos: list[list[str]] = []
    for dim in ids:
        index = payload["dimension"][dim]["category"]["index"]
        if isinstance(index, list):  # Eurostat sometimes ships a plain list
            code_by_pos.append(list(index))
        else:
            inverted = {pos: code for code, pos in index.items()}
            code_by_pos.append([inverted[i] for i in range(len(inverted))])

    rows = []
    for flat, value in payload.get("value", {}).items():
        remainder = int(flat)
        positions = [0] * len(sizes)
        for axis in range(len(sizes) - 1, -1, -1):
            positions[axis] = remainder % sizes[axis]
            remainder //= sizes[axis]
        row = {dim: code_by_pos[i][positions[i]] for i, dim in enumerate(ids)}
        row["value"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def load_eurostat_avia_par(
    reporters: tuple[str, ...] = EUROSTAT_REPORTERS,
    years: tuple[int, ...] = (2019, 2023, 2024),
    *,
    force: bool = False,
) -> pd.DataFrame:
    """India to Europe traffic measured from the *European* end.

    Every other source in this project counts India-Europe routes at the Indian
    end. This counts the same routes at the European end, which is what makes
    triangulation something performed rather than claimed: the two measurements
    of one route can be compared, and the difference reported.

    Returns: reporter_country, reporter_icao, partner_icao, year, pax.
    Only pairs where the partner country is India (`IN`) are kept.

    Reporters that return no dataset are skipped rather than raising, because
    Eurostat coverage varies by country and year and one missing member state
    must not take down the pipeline. The set actually retrieved is reported in
    the `reporter_country` column, so any gap is visible rather than assumed.
    """
    frames = []
    for cc in reporters:
        for year in years:
            url = (
                f"{EUROSTAT_BASE}avia_par_{cc}"
                f"?format=JSON&lang=EN&unit=PAS&tra_meas=PAS_CRD&time={year}"
            )
            try:
                path = _fetch(url, f"eurostat_avia_par_{cc}_{year}", force=force, timeout=180)
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if "value" not in payload or not payload["value"]:
                continue
            df = _jsonstat_to_frame(payload)
            if "airp_pr" not in df.columns:
                continue
            df = df[df["airp_pr"].str.contains("_IN_", na=False)].copy()
            if df.empty:
                continue
            parts = df["airp_pr"].str.split("_", expand=True)
            df["reporter_country"] = parts[0]
            df["reporter_icao"] = parts[1]
            df["partner_icao"] = parts[3]
            df["year"] = int(year)
            df = df.rename(columns={"value": "pax"})
            frames.append(
                df[["reporter_country", "reporter_icao", "partner_icao", "year", "pax"]]
            )

    cols = ["reporter_country", "reporter_icao", "partner_icao", "year", "pax"]
    if not frames:
        return pd.DataFrame(columns=cols)
    return (
        pd.concat(frames, ignore_index=True)
        .groupby(cols[:-1], as_index=False)["pax"]
        .sum()
        .sort_values(["year", "pax"], ascending=[True, False])
        .reset_index(drop=True)
    )


def load_manual_assumptions() -> pd.DataFrame:
    """Hand-entered figures that no free source publishes, chiefly airline yields.

    Schema: key, value, unit, source_name, source_url, pull_date, page_ref, reliability
    with pull_date as YYYY-MM-DD and reliability in {H, M, L}.

    Every row is a number a real engagement would triangulate against a paid
    source such as Cirium or OAG. Each carries its own citation so a reader can
    check it. Returns an empty frame with the right columns when the file is not
    yet populated, so the pipeline stays importable during Phase 1.
    """
    cols = [
        "key",
        "value",
        "unit",
        "source_name",
        "source_url",
        "pull_date",
        "page_ref",
        "reliability",
    ]
    path = MANUAL / "assumptions.csv"
    if not path.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"assumptions.csv is missing required provenance columns: {missing}")
    return df


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

LOADERS = {
    "intl_country": load_dgca_intl_country,
    "intl_city": load_dgca_intl_city,
    "intl_carrier": load_dgca_intl_carrier,
    "dom_carrier": load_dgca_domestic_carrier,
    "dom_city": load_dgca_domestic_city,
    "airports": load_ourairports,
    "worldbank": load_worldbank_macro,
    "eurostat_india_europe": load_eurostat_avia_par,
}

# Routes where DGCA and Eurostat disagree by more than measurement noise and the
# disagreement cannot be resolved from free sources. Excluded from any figure that
# depends on a single agency being right, and reported in docs/methodology.md
# rather than quietly dropped.
#
# ROME to DELHI: Eurostat reports 171,942 passengers on LIRF to VIDP for 2024.
# DGCA lists no Rome to Delhi city pair at all, though it uses the string "ROME"
# elsewhere (Rome to Amritsar) so this is not a naming mismatch. Every other route
# the two agencies both cover agrees to within 1.6%.
DISPUTED_ROUTES = {("ROME", "DELHI")}


def build_all(*, force: bool = False) -> dict[str, pd.DataFrame]:
    """Run every loader, write parquet, write the raw manifest. Returns the frames."""
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out: dict[str, pd.DataFrame] = {}
    for name, fn in LOADERS.items():
        df = fn(force=force)
        df.to_parquet(PROCESSED / f"{name}.parquet", index=False)
        out[name] = df
    _write_manifest(out)
    return out


def _write_manifest(frames: dict[str, pd.DataFrame]) -> None:
    """Record what was pulled and when. Committed even though data/raw is not."""
    lines = [
        "# Raw pull manifest",
        "",
        f"Generated {_dt.date.today().isoformat()} by `src.data_pipeline.build_all`.",
        "",
        "`data/raw/` itself is gitignored because it is regenerable. This manifest is",
        "committed so the provenance of every published figure survives.",
        "",
        "| Dataset | Rows | Columns |",
        "|---|---|---|",
    ]
    for name, df in frames.items():
        lines.append(f"| {name} | {len(df):,} | {df.shape[1]} |")
    lines.append("")
    (RAW / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    for _name, _df in build_all().items():
        print(f"{_name:<14} {len(_df):>7,} rows  {_df.shape[1]:>2} cols")
