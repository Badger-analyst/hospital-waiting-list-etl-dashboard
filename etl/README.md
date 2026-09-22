# Waiting List Analytics

A module of the Healthcare Ward Analytics Platform. End-to-end healthcare
data analytics on Ireland's national hospital waiting list: Python ETL
(folder-combine pattern, mirroring Power Query) -> specialty mapping -> EDA
-> Power BI data model and DAX measures.

## Data source

**Real, public data**: Ireland's National Treatment Purchase Fund (NTPF)
National Public Hospital Waiting List Open Data - Inpatient/Day Case (IPDC)
and Outpatient (OP), published monthly, licensed **CC-BY**.

- Landing page: https://www.ntpf.ie/waiting-list-data/open-data/
- Full column reference, HIPE codes, Adult/Child split, and the Small
  Volume Specialties suppression rule: **[`docs/data_dictionary.md`](docs/data_dictionary.md)**

> NTPF's site doesn't allow automated/bulk download (their CSV links serve
> as opaque binary to fetch tools, and the domain isn't on most sandboxed
> network allowlists) - download the files manually from the link above and
> drop them into `data/raw/inpatient/` and `data/raw/outpatient/`.

**Out of the box, this repo ships with a real (not synthetic) sample** -
transcribed from NTPF's own published national summary reports, so the ETL,
notebook and tests all run against genuine numbers before you've downloaded
anything yourself. See `etl/build_sample_from_ntpf_published_reports.py` for
exact sources and its documented limitations.

## Structure

```
waiting-list-analytics/
├── data/
│   ├── raw/
│   │   ├── inpatient/       <- drop IPDC "by Speciality" CSVs here
│   │   └── outpatient/      <- drop OP "by Speciality" CSVs here
│   ├── mapping/
│   │   └── Specialty_Mapping.csv   (Specialty -> Specialty Group lookup)
│   └── processed/           <- ETL output (Inpatient/Outpatient/All_Data.csv + National_Monthly_Totals.csv)
├── etl/
│   ├── combine_waiting_lists.py               (Python equivalent of the Power Query folder-combine)
│   └── build_sample_from_ntpf_published_reports.py  (seeds the real sample data above)
├── analysis/
│   └── waiting_list_eda.ipynb   (4 real questions, answered - see below)
├── docs/
│   ├── data_dictionary.md   (HIPE codes, Adult/Child split, Small Volume Specialties rule)
│   └── img/                 (charts exported from the notebook, embedded below)
├── powerbi/
│   ├── Data_Model.md        (tables, relationships, star schema)
│   ├── DAX_Measures.md      (every measure behind the KPIs/visuals)
│   └── Build_Guide.md       (click-by-click Power BI Desktop rebuild)
├── tests/
│   └── test_etl.py          (pytest - data quality + ETL shape-normalisation)
├── .github/workflows/
│   └── waiting-list-etl.yml (scheduled ETL run)
└── requirements.txt
```

## Quickstart

1. `pip install -r requirements.txt`
2. Run against the built-in sample straight away: `pytest tests/` and open
   `analysis/waiting_list_eda.ipynb`.
3. For your own multi-year data: download the **"IPDC Waiting List by
   Speciality"** and **"OP Waiting List by Speciality"** CSVs from the NTPF
   Open Data page into `data/raw/inpatient/` and `data/raw/outpatient/`, then
   `python etl/combine_waiting_lists.py` (this replaces the sample with your
   real, larger dataset - it won't overwrite it with nothing if the raw
   folders are empty).
4. Open Power BI Desktop and follow `powerbi/Build_Guide.md`.

## Analysis - what the data actually says

`analysis/waiting_list_eda.ipynb` answers four questions and shows the work
(full charts and code in the notebook):

1. **Longest waits by specialty** - Developmental Paediatrics, Maxillo-Facial
   and Clinical (Medical) Genetics show the longest weighted-average waits
   (~11-12 months) among specialties with meaningful volume.
2. **Adult vs Child** - adults are 96% of patients in the sample, but the
   weighted-average wait is *longer* for children (8.8 months) than adults
   (7.4 months) - flagged in the notebook as likely a sample-composition
   effect rather than a general finding, since the sample's child rows only
   cover a subset of specialties.
3. **Trend, Oct 2024 - Sep 2025** - the national Inpatient/Day Case list grew
   from 87,753 to 100,045 (**+14.0%**); Outpatient grew from 588,544 to
   626,521 (**+6.5%**). Both lists trended upward across the period.
4. **Inpatient vs Outpatient gap** - as of Sep 2025, the Outpatient list is
   **6.3x** the size of the Inpatient/Day Case list - most of the headline
   "waiting list" number is an Outpatient story.

![Longest waits by specialty](docs/img/longest_waits_by_specialty.png)
![Adult vs Child](docs/img/adult_vs_child.png)
![National trend](docs/img/national_trend.png)
![Inpatient vs Outpatient gap](docs/img/ip_vs_op_gap.png)

## Reconciliation

Checking this project's numbers against NTPF's own published totals, rather
than just trusting the pipeline:

- **Adult Inpatient/Day Case subtotal**: summing this repo's transcribed
  specialty x time-band rows for Adult patients as at 31 Aug 2023 gives
  **73,611**; NTPF's own published summary states **73,598** for the same
  snapshot - a difference of 13 (0.02%), consistent with NTPF's Statistical
  Disclosure Control rounding (see the data dictionary), not a transcription
  error.
- **Child subtotal is *not* reconciled** in this sample on purpose - the
  sample only transcribes the child specialties NTPF's PDF reported
  individually, not the full child breakdown, so it undercounts (2,531 vs
  NTPF's published 9,694). This resolves once you load the full raw export.
- **`[Latest Month Wait List]`**: once you've loaded your own full multi-year
  download and the DAX measure is summing real row-level detail rather than
  this repo's small sample, it should reconcile (within NTPF's own SDC
  rounding) to that month's press-release figure - e.g. **100,045** for Sep
  2025 (https://www.ntpf.ie/?p=4613). `data/processed/National_Monthly_Totals.csv`
  already carries that exact figure so you have something to check your
  computed measure against immediately.

## Tests

`pytest tests/` - 8 checks covering: no nulls in `Total`, non-negative
totals, row counts within a sane range, every `Specialty_Name` mapping
successfully to a `Specialty_Group`, and unit tests for the ETL's
normalisation of both the older long-format and current wide-format
("by Speciality") NTPF file shapes.

## Report (Power BI)

Two pages, matching the reference build this project follows:

- **Summary** - Latest/PY-Latest wait list KPI cards, an Avg/Med Wait card
  driven by a Calculation Method slicer, a donut by `Case_Type`, a bar chart
  of Avg/Med wait by `Time_Bands` and `Age_Profile`, and year-over-year trend
  lines split by `Case_Type`.
- **Detail** - the same slice at a lower grain, table/matrix by specialty.

Once you've built the report in Power BI Desktop (`powerbi/Build_Guide.md`),
drop screenshots into `powerbi/screenshots/` and reference them here.

## What's real vs. reconstructed

| Part | Status |
|---|---|
| Data source & schema | Real NTPF open data, official column definitions |
| Sample dataset (`data/processed/`) | Real, transcribed from NTPF's own published PDF summaries - not synthetic |
| Specialty -> Specialty Group mapping | Reconstructed from the screenshot + NTPF's published specialty list |
| ETL script | Original, mirrors the Power Query pattern shown; handles both known NTPF file shapes |
| Analysis notebook | Original, executed against the real sample above |
| DAX measures | Reconstructed to match the visible KPIs/field names - not the original author's exact code |
| Visual layout | Reconstructed from the screenshots |

## License

NTPF data is CC-BY - attribute "National Treatment Purchase Fund" if you
publish this dashboard publicly.
