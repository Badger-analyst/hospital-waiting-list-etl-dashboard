# Waiting List Analytics

A module of the Healthcare Ward Analytics Platform. Reproduces, end-to-end,
the Excel/Power Query/Power BI workflow shown in the reference build:
monthly waiting list CSVs → folder-combine ETL → specialty mapping → data
model → DAX measures → a two-page Power BI report.

## Data source

**Real, public data**: Ireland's National Treatment Purchase Fund (NTPF)
National Public Hospital Waiting List Open Data — Inpatient/Day Case (IPDC)
and Outpatient (OP), published monthly, licensed **CC-BY**.

- Landing page: https://www.ntpf.ie/waiting-list-data/open-data/
- Format used here: **"by Speciality"** exports (no hospital-level
  breakdown), matching `Archive_Date, Specialty_HIPE, Specialty_Name,
  Case_Type, Adult_Child, Age_Profile, Time_Bands, Total`

> NTPF's site doesn't allow automated/bulk download (their CSV links serve
> as opaque binary to fetch tools and the domain isn't on most sandboxed
> network allowlists) — download the files manually from the link above and
> drop them into `data/raw/inpatient/` and `data/raw/outpatient/`.

## Structure

```
waiting-list-analytics/
├── data/
│   ├── raw/
│   │   ├── inpatient/       <- drop IPDC "by Speciality" CSVs here
│   │   └── outpatient/      <- drop OP "by Speciality" CSVs here
│   ├── mapping/
│   │   └── Specialty_Mapping.csv   (Specialty -> Specialty Group lookup)
│   └── processed/           <- ETL output (Inpatient/Outpatient/All_Data.csv)
├── etl/
│   └── combine_waiting_lists.py    (Python equivalent of the Power Query folder-combine)
├── powerbi/
│   ├── Data_Model.md        (tables, relationships, star schema)
│   ├── DAX_Measures.md      (every measure behind the KPIs/visuals)
│   └── Build_Guide.md       (click-by-click Power BI Desktop rebuild)
├── .github/workflows/
│   └── waiting-list-etl.yml (scheduled ETL run)
└── requirements.txt
```

## Quickstart

1. Download a handful of years of the **"IPDC Waiting List by Speciality"**
   and **"OP Waiting List by Speciality"** CSVs from the NTPF Open Data page
   into `data/raw/inpatient/` and `data/raw/outpatient/` respectively.
2. `pip install -r requirements.txt`
3. `python etl/combine_waiting_lists.py`
4. Open Power BI Desktop and follow `powerbi/Build_Guide.md`, pointing the
   folder queries at `data/raw/inpatient` and `data/raw/outpatient` (or load
   the pre-combined `data/processed/*.csv` directly and skip straight to the
   modeling step).

## Report

Two pages, matching the reference:

- **Summary** — Latest/PY-Latest wait list KPI cards, an Avg/Med Wait card
  driven by a Calculation Method slicer, a donut by `Case_Type`, a bar chart
  of Avg/Med wait by `Time_Bands` and `Age_Profile`, and year-over-year trend
  lines split by `Case_Type`.
- **Detail** — the same slice at a lower grain, table/matrix by specialty.

## What's real vs. reconstructed

| Part | Status |
|---|---|
| Data source & schema | Real NTPF open data, official column definitions |
| Specialty → Specialty Group mapping | Reconstructed from the screenshot + NTPF's published specialty list |
| ETL script | Original, mirrors the Power Query pattern shown |
| DAX measures | Reconstructed to match the visible KPIs/field names — not the original author's exact code |
| Visual layout | Reconstructed from the screenshots |

## License

NTPF data is CC-BY — attribute "National Treatment Purchase Fund" if you
publish this dashboard publicly.
