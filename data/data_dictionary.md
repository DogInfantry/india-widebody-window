# Data dictionary

Every field used anywhere in this project, with its source, units, pull date and a
reliability grade. The rule in `CLAUDE.md` is that no number reaches the page unless
it is computed from a dataset listed here or carries its own citation.

**Pull date for all automated sources: 2026-08-15.**
Reliability: **H** official or primary, **M** community mirror or cross-checked
secondary, **L** single secondary source, directional only.

Regenerate everything with `python -m src.data_pipeline`.

---

## 1. DGCA traffic statistics

**Originating publisher:** Directorate General of Civil Aviation, Government of India.
**Accessed via:** https://github.com/Vonter/india-aviation-traffic (ODbL), which parses
the DGCA portal and publishes cleaned CSVs. The portal itself is JavaScript driven and
not directly machine readable, which is why the mirror is used. DGCA is credited as the
source on every figure.
**Reliability:** H for the underlying figures, M for the mirroring step.

### 1.1 `intl_country` (2,421 rows, 10 columns, 2015 to 2025)

Source file `aggregated/international/country.csv`. Quarterly.

| Field | Type | Units | Notes |
|---|---|---|---|
| `year` | Int64 | year | **Converted from DGCA two-digit form.** Source ships `15` for 2015 |
| `quarter` | int | 1 to 4 | |
| `country` | str | | Uppercased and stripped. DGCA spelling retained |
| `pax_to_india` | int | passengers | |
| `pax_from_india` | int | passengers | |
| `pax_total` | int | passengers | Both directions summed |
| `freight_to_india` | float | tonnes | Not used in the analysis |
| `freight_from_india` | float | tonnes | Not used in the analysis |
| `region` | str | | Mapped via `COUNTRY_REGION`. Unmapped countries fall to `Other` |
| `is_gulf` | bool | | True for the GCC six: UAE, Saudi Arabia, Qatar, Oman, Kuwait, Bahrain |

**Definition warning, and this one is the whole case.** These are **sector** passengers,
counted on the India to foreign-point leg. They are not true origin-destination. A
passenger flying Delhi to Dubai to London appears here under the United Arab Emirates,
not the United Kingdom. Any comparison against an O-D source such as IATA must say
which measure it is using. See section 6.

### 1.2 `intl_city` (15,318 rows, 9 columns)

Source file `aggregated/international/city.csv`. Quarterly city pairs.
`city1` and `city2` are kept verbatim because DGCA is not consistent about which is the
Indian point. `pax_total` sums both directional flows.

### 1.3 `intl_carrier` (10,329 rows, 10 columns)

Source file `aggregated/international/carrier.csv`. **Unpivoted from quarterly to
monthly** by this pipeline: the source packs three months per row as column suffixes
`M1`, `M2`, `M3`, which become `month = (quarter - 1) * 3 + m`.

| Field | Type | Units | Notes |
|---|---|---|---|
| `year`, `quarter`, `month` | Int64 | | |
| `airline` | str | | Uppercased. `Total *` rows removed, see section 5 |
| `pax_to_india`, `pax_from_india`, `pax_total` | int | passengers | |
| `carrier_group` | str | | `Indian`, `Gulf`, or `Other foreign` |

`carrier_group` is a judgement applied by this project, not a DGCA field. It is a
membership list of airline names, so a carrier DGCA spells differently in a future
release silently lands in `Other foreign`. `test_indian_carrier_share_2024` guards the
aggregate against drift.

### 1.4 `dom_carrier` (3,631 rows, 22 columns, 2015-01 to 2026-05)

Source file `aggregated/domestic/carrier.csv`. Monthly. The richest file in the set, and
despite the name it carries **both** domestic and international rows for Indian carriers,
split by `service_type`.

| Field | Type | Units | Notes |
|---|---|---|---|
| `service_type` | str | | `ScheduledDomestic`, `ScheduledInternational`, `NonScheduledDomestic`, `NonScheduledInternational` |
| `airline` | str | | `Total *` rows removed, see section 5 |
| `year`, `month` | Int64 | | |
| `pax` | float | passengers | Raw count, **not** thousands |
| `rpk` | float | passenger-km | **Converted from DGCA thousands by this pipeline** |
| `ask` | float | seat-km | **Converted from DGCA thousands by this pipeline** |
| `aircraft_km` | float | km | **Converted from DGCA thousands by this pipeline** |
| `load_factor` | float | percent | As published by DGCA |
| `aircraft_number` | float | departures | See the caveat below |
| `is_scheduled`, `is_international` | bool | | Derived from `service_type` |

**Units caveat.** DGCA publishes distance columns in thousands while passenger counts are
raw. This is not stated in the file. It was established three ways before the conversion
was applied:

1. **Scale.** Thousands gives India domestic 163.8bn RPK for 2025, matching the published
   industry range of roughly 160 to 170bn. The raw reading implies each domestic
   passenger flies 0.98 km.
2. **Ratio.** Computed `rpk / ask` agrees with DGCA's own `load_factor` column to within
   0.25pp on the major carriers and 0.93pp worst case across all carriers.
3. **Internal coherence.** For one sample month, 204 departures against 120 (thousand)
   aircraft-km gives 588 km per departure, and 25,905 passengers against 15,260
   (thousand) RPK gives 589 km. Two independent columns agree to one part in 600.

Left uncorrected this would have published an average stage length of 5 km.
`test_stage_length_is_physically_plausible` and `test_computed_load_factor_matches_published`
guard it.

The tonne-kilometre and cargo columns are also published in thousands and are **not**
converted, because nothing in this project reads them. Convert at the point of use if
that changes.

**`aircraft_number` caveat.** DGCA labels this "Aircraft Number", but the magnitudes
(204 against 25,905 passengers in one month) show it counts departures, not fleet size.
That reading is an inference from the data, not a documented DGCA definition. Graded **M**
and not used for any headline figure.

### 1.5 `dom_city` (65,166 rows, 11 columns)

Source file `aggregated/domestic/city.csv`. Monthly domestic city pairs.

---

## 2. OurAirports

**Source:** https://davidmegginson.github.io/ourairports-data/airports.csv
**Licence:** CC0 1.0, public domain. **Reliability:** H. Refreshed nightly upstream.
**Filtered to** `large_airport` and `medium_airport`, giving 5,272 rows.

Fields kept: `ident`, `type`, `name`, `latitude_deg`, `longitude_deg`, `iso_country`,
`municipality`, `iata_code`. Coordinates drive great circle distance for the bottom-up
market sizing.

---

## 3. World Bank Open Data

**Source:** https://api.worldbank.org/v2 **Licence:** CC BY 4.0. **Reliability:** H.
Countries: IND, ARE, QAT, SAU, OMN, KWT, BHR, CHN, USA, GBR, DEU, SGP. Years 2000 to 2025.
936 rows in long format: `country`, `iso3`, `indicator`, `year`, `value`.

| Indicator | Meaning | Coverage limit |
|---|---|---|
| `SP.POP.TOTL` | Population | Current |
| `NY.GDP.PCAP.CD` | GDP per capita, current USD | Current |
| `IS.AIR.PSGR` | Air transport, passengers carried | **No values after 2023** |

`IS.AIR.PSGR` supports cross-country elasticity fitting across 2010 to 2023. It cannot
size a current year. Anything projecting from it says so on the chart.

---

## 4. Manual assumptions (`data/manual/assumptions.csv`)

Numbers no free source publishes, chiefly airline yield in rupees per RPK. DGCA publishes
no fares. IndiGo discloses yield in quarterly filings; Air India is unlisted and files
nothing. Each row is transcribed by hand and carries its own provenance:

`key, value, unit, source_name, source_url, pull_date, page_ref, reliability`

`pull_date` is `YYYY-MM-DD`, `reliability` is one of `H`, `M`, `L`.
`test_manual_assumptions_carry_provenance` fails the build if any row lacks a source.

**Status: not yet populated.** Pending review before these drive the revenue waterfall.

---

## 5. Two structural traps in the source data

Both are handled once inside the loaders so no caller can forget, and both have a
regression test.

1. **Two-digit years.** DGCA ships `15` for 2015 in the international files but four-digit
   years in the domestic file. `_norm_year` normalises both. Guarded by
   `test_years_are_four_digit`.
2. **`Total *` pseudo-airlines.** The carrier files include `Total Domestic` and
   `Total International` rows formatted exactly like airlines. A groupby that keeps them
   double counts every passenger and reports every market share at roughly half its true
   value. `_drop_total_rows` removes them. Guarded by `test_no_total_pseudo_airlines`.

---

## 6. Known conflicts, flagged rather than resolved

Consistent with `CLAUDE.md`: conflicting figures are reported with their definitions, not
silently reconciled to whichever is convenient.

| Quantity | Competing figures | Why they differ |
|---|---|---|
| India international Gulf share | **51.2%** (DGCA sector, computed here, 2024) against **~40%** (IATA true O-D, secondary) | Sector counts the India to hub leg; O-D counts the passenger's actual destination. The gap is the connect leak, and it is the finding rather than a problem |
| India total passengers | 180.4M (World Bank, carriers-carried, 2023), 211M (IATA, 2024), 406M (DGCA, airport-handled, 2025) | Three different things counted. State the definition every time |
| Air India post-merger fleet | 198 / 205 / 218 | Varies by source date and by whether Vistara and Air India Express are consolidated |

---

## 7. Sources evaluated and not adopted

| Source | Why not |
|---|---|
| OpenSky Network | DGCA city-pair passenger counts are a better measure than frequency inferred from ADS-B, and OpenSky adds OAuth with 30 minute tokens |
| Airports Authority of India | Airport-level totals add nothing to a route and carrier case; only available as PDF |
| OpenFlights `routes.dat` | Route data frozen since 2014, structural reference only |
| Cirium, OAG, CAPA | Paywalled. Named in `docs/methodology.md` as what a real engagement would triangulate against |

---

## 8. Sources verified reachable, not yet wired in

Confirmed live on 2026-08-15, scheduled for the next pipeline commit.

| Source | Role | Status |
|---|---|---|
| Eurostat `avia_par_*` | European end of India-Europe routes, enabling both-ends reconciliation | Adopted, pending implementation |
| IOCL aviation fuel prices | Indian ATF price for the scenario fuel lever | Adopted, pending implementation |
| BTS T-100 International Segment | US end of India-US routes | Timeboxed to one attempt |
| UK CAA airport data | UK end of India-UK routes | Timeboxed to one attempt |

Timeboxed sources fail soft. If one resists, that arm is measured from the India side
only and `docs/methodology.md` says so.
