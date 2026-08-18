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

A second class of row has since joined it: numbers that **are** published, but only inside a
PDF that no API exposes. The wide-body seat counts come from the manufacturers' own airport
planning manuals (Airbus `AC_A350`, Boeing `D6-58333` and `D6-86073`), and every one is
recorded on a **two-class** basis so the variants stay comparable. Never mix in a one-class
figure: Boeing publishes the 787-9 at 290 two-class and 406 all-economy, a 40 percent spread.

`aircraft_utilisation_hours_per_day` is the one manual row with an independent cross-check.
IndiGo's FY26 annual report gives 1,619,570 block hours over 441 aircraft; DGCA's
`aircraft_hours` gives 1,614,608 for the same carrier and year, **0.31 percent apart**. That
is the second both-ends check in this repo after DGCA against Eurostat, and it is the reason
the row is graded `H`. The row is on an **owned-fleet** basis, which is not the ~13 hours that
circulates: that figure is active-fleet and implies roughly 100 grounded aircraft.

`key, value, unit, source_name, source_url, pull_date, page_ref, reliability, status, note`

`reliability` is one of `H`, `M`, `L`. `pull_date` accepts ISO or `M/D/YYYY` and is
normalised to `YYYY-MM-DD` on read, because fighting a spreadsheet over date formatting is a
good way to have the file stop being maintained.

### Status vocabulary

Only **two** states are cleared to drive a published figure. `dp.assumption()` raises
`UnverifiedAssumption` for every other state.

| Status | Cleared | Meaning |
|---|---|---|
| `VERIFIED` | yes | Checked against the primary source, value matched exactly |
| `CORRECTED_VERIFIED` | yes | Checked against primary; the original value was wrong and is now fixed |
| `DRAFT_UNVERIFIED` | no | Transcribed, nobody has checked it |
| `UNVERIFIED_NO_PRIMARY` | no | The company publishes no such line item, so it can never be checked |
| `VALUE_MISSING` | no | Source is good, value not yet transcribed |
| `VALUE_MISSING_LINK_FIXED` | no | Link was wrong and has been corrected; value still needed |
| `VALUE_MISSING_LINK_WEAK` | no | Link is an index or landing page, not a citable document |
| `VALUE_MISSING_NO_SOURCE` | no | No `source_url` at all, so nothing to verify against |
| `VALUE_MISSING_SOURCE_STALE` | no | Source exists but has been superseded |
| `MODELED` | no | Genuinely modelled, no source expected, must be labelled on the chart |
| `NOT_AVAILABLE` | no | A real figure exists but is not publicly disclosed |

This replaced an earlier three-state scheme after the first real verification pass, which
showed that "unverified" was doing the work of at least five different problems needing five
different actions: a missing value, an unchecked value, a value the company does not publish,
a dead link, and a superseded source.

`UNVERIFIED_NO_PRIMARY` is the state that earns its keep. It marks a value that exists and
looks entirely plausible but can never be verified, because the figure is an aggregator's
convention rather than something the company reports. That is exactly the case that produced
the retracted margin claim in `docs/methodology.md`.

### Current state: 25 of 31 rows cleared

Twenty-five rows carry `VERIFIED` or `CORRECTED_VERIFIED` and may drive a published figure.
The six that do not are **terminal, not pending work**: each was chased to a primary source
and the source does not exist.

| Row | Status | Why it will never clear |
|---|---|---|
| `air_india_yield_inr_per_rpk` | `NOT_AVAILABLE` | Air India is unlisted and files no exchange results |
| `aircraft_utilisation_hours_per_day_active` | `NOT_AVAILABLE` | The grounded-aircraft count is absent from both the FY26 annual report and the June 2026 analyst deck |
| `india_dubai_weekly_seat_entitlement_one_side` | `UNVERIFIED_NO_PRIMARY` | India publishes no bilateral entitlement table. Corroborated from the traffic end instead |
| `india_abu_dhabi_weekly_seat_entitlement_one_side` | `UNVERIFIED_NO_PRIMARY` | Same reason. Better corroborated than the Dubai row: two independent secondary sources give 50,000 one side, and a third figure from the traffic end reconciles with both |
| `gulf_od_share_pct` | `UNVERIFIED_NO_PRIMARY` | IATA sells origin-destination data and publishes no free table |
| `gulf_hub_connect_premium_pct` | `MODELED` | Nobody publishes it. Status is `MODELED` rather than `NOT_AVAILABLE` so it is not confused with a figure that exists but is undisclosed |

The two `UNVERIFIED_NO_PRIMARY` rows are the ones to watch, because both carry weight. Each is
read **only** through `assumption(key, allow_unverified=True)`, in exactly one diagnostic
function apiece, and everything derived from either is reported as a band and labelled
`MODELLED` on the chart face:

- `india_dubai_weekly_seat_entitlement_one_side` feeds `benchmarking.dubai_entitlement_check`,
  which corroborates it from DGCA traffic and finds 88.8% utilisation.
- `india_abu_dhabi_weekly_seat_entitlement_one_side` feeds `benchmarking.gulf_entitlement_check`,
  which finds Abu Dhabi at about 70% utilisation against Dubai's 89.6. That difference matters:
  it means the Gulf is **not** uniformly capacity-capped, and the recommendation was corrected
  to say so. **Sharjah holds the third UAE MoU and carries 2.3M passengers a year; two
  timeboxed searches found no entitlement figure for it, so it is outside the check.**
- `gulf_od_share_pct` feeds `options.connect_gap`. It carries the eleven point connect gap
  the recommendation rests on, which makes it **the most likely reason the case is wrong**.

A note on how this table used to read, kept because the drift is the lesson. It previously
said "6 of 18 rows cleared", called both operating-profit rows unusable, and recorded Emirates
yield as blank pending an unsettled FX rate. All three had been fixed in code and none of it
reached this file. Cross-check the counts against `load_manual_assumptions()` rather than
trusting the prose.

**Two rows added most recently:**

| Row | Value | Status | Note |
|---|---|---|---|
| `a321xlr_range_km` | 8,700 km | `VERIFIED` | Airbus product page. A product page is accepted for a **range** spec where it is refused for a seat count, because range has no configuration ambiguity. No seat row is recorded for the type: the airport planning manual 404ed, and breakeven is computed per ASK so the seat count is not needed |
| `gulf_od_share_pct` | 40% | `UNVERIFIED_NO_PRIMARY` | Promoted into the gate after being found on the live site as a hard number with no row at all |

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
| India international Gulf share | **50.9%** (DGCA sector, computed here, 2024) against **40%** (IATA true O-D, secondary, gated as `gulf_od_share_pct`) | Sector counts the India to hub leg; O-D counts the passenger's actual destination. The gap is the connect leak, and it is the finding rather than a problem |
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

## 8. Eurostat air transport by airport pair

**Source:** `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/avia_par_<cc>`
**Licence:** Commission Decision 2011/833/EU reuse policy. **Reliability:** H.
Filtered to `unit=PAS`, `tra_meas=PAS_CRD`, years 2019, 2023 and 2024.

One dataset per reporting country. Airport pair codes read
`<reporter>_<ICAO>_<partner>_<ICAO>`, so India routes are the codes containing `_IN_`.
Returns `reporter_country`, `reporter_icao`, `partner_icao`, `year`, `pax`.

This exists for one reason: it measures India to Europe routes from the **European**
end, where every other source in this project measures them from the Indian end. Two
independent agencies measuring the same physical route is the strongest validation
available without paying for Cirium or OAG.

### 8.1 The reconciliation result, 2024

| Country | DGCA (India end) | Eurostat (Europe end) | Gap |
|---|---|---|---|
| Finland | 149,508 | 149,551 | 0.0% |
| France | 964,079 | 955,339 | -0.9% |
| Switzerland | 340,372 | 343,583 | 0.9% |
| Germany | 1,744,685 | 1,766,890 | 1.3% |
| Netherlands | 664,238 | 673,438 | 1.4% |
| Poland | 108,223 | 109,731 | 1.4% |
| Denmark | 95,986 | 99,036 | 3.2% |
| **Italy** | **222,689** | **305,303** | **37.1%** |
| Total | 4,289,780 | 4,402,871 | 2.6% |

Seven of eight countries agree to within 3.2%, six of them to within 1.4%. That is
close enough to treat the DGCA spine as sound. Guarded by
`test_dgca_and_eurostat_agree_on_the_same_routes`, which fails if the two ever diverge
by more than 5% across the countries both cover.

### 8.2 The Italy dispute, unresolved and reported as such

Milan to Delhi agrees between the two agencies to 1.6% (DGCA 131,292, Eurostat 133,361).
The entire Italian gap sits on one route:

- Eurostat reports **171,942** passengers on Rome Fiumicino (LIRF) to Delhi (VIDP), 2024.
- DGCA lists **no Rome to Delhi city pair at all**. This is not a naming mismatch: DGCA
  uses the string `ROME` elsewhere in the same file, for Rome to Amritsar.

Three explanations are possible and free sources cannot separate them: DGCA omits the
route, Eurostat counts something indirect as direct, or an operating carrier is filed
differently by the two agencies.

**Handling:** the pair is quarantined in `src.data_pipeline.DISPUTED_ROUTES`, excluded
from any figure that depends on one agency being right, and reported with both numbers
in `docs/methodology.md`. `test_rome_delhi_stays_quarantined` stops it silently
rejoining the analysis. Italy is excluded from the reconciliation test for the same
reason.

### 8.3 Coverage gaps in Eurostat

Nine reporting countries return India routes across the years pulled: AT, CH, DE, DK, FI,
FR, IT, NL, PL. Austria returns India data in earlier years but **none for 2024**, while
DGCA reports 65,016 Austrian passengers that year. Belgium, Spain, Sweden, Portugal,
Ireland, Greece, Czechia and Hungary return nothing.

Eurostat is therefore a **validation instrument, not a complete census** of India to
Europe traffic. Totals for the European market come from DGCA; Eurostat checks them.

---

## 9. Timeboxed sources, attempted and dropped

Both were verified reachable on 2026-08-15 and both were dropped after their one
permitted attempt, per the rule in `CLAUDE.md` that a documented single-sided
measurement beats an undocumented scrape that breaks in CI.

| Source | What happened | Consequence |
|---|---|---|
| BTS T-100 International Segment | **Attempted twice, dropped twice.** All four `PREZIP` filename patterns return 404 (`T_T100I_SEGMENT_ALL_CARRIER[_YYYY]`, `T_T100_SEGMENT_ALL_CARRIER`, `T_T100I_MARKET_ALL_CARRIER`), so BTS has reorganised TranStats rather than simply moved one file. The `data.transportation.gov` Socrata catalog does not carry the series either: a search for it returns Colorado highway quality and a canal trail. What remains is a form POST carrying ASP.NET viewstate, which is exactly the brittle scraping this project refuses | The India to United States arm is measured from the India side only, and 5.6% cross-check coverage stands |
| IOCL aviation fuel prices | Page is JavaScript driven and serves no parseable table | ATF price becomes a single cited row in `data/manual/assumptions.csv`. One number per month does not justify a scraper |
