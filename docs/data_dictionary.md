# Data Dictionary

## Columns

| Column | Type | Description |
|---|---|---|
| `Archive_Date` | Date | The month-end (or publication date) the snapshot represents. NTPF publishes on a rolling monthly basis. |
| `Specialty_HIPE` | Integer | The HIPE (Hospital In-Patient Enquiry) specialty code — Ireland's national coding scheme for clinical specialties, maintained by the Healthcare Pricing Office. Only present in the raw "by Speciality"/"by Group Hospital" exports; NTPF's published PDF summaries (used for `analysis/`'s sample data) don't include it, so those rows are blank. |
| `Specialty_Name` | Text | Human-readable specialty, e.g. "Ophthalmology". Maps 1:1 to `Specialty_HIPE` in the full export. |
| `Case_Type` | Text | `Inpatient`, `Day Case`, or `Outpatient` — whether the patient is waiting for an overnight admission, a same-day procedure, or a first consultation. |
| `Adult_Child` | Text | See below. |
| `Age_Profile` | Text | Finer age banding within Adult/Child (e.g. `0-15`, `16-64`, `65+`) — present in the raw "by Speciality" export; not published in NTPF's PDF summaries, so the sample data uses a placeholder `"All Ages"`. |
| `Time_Bands` | Text | How long the patient has been waiting, in bands. Band widths differ by source era — see below. |
| `Total` | Integer | Patient count in that Specialty x Case_Type x Adult_Child x Age_Profile x Time_Bands bucket. Subject to NTPF's Small Volume Specialties suppression (below). |
| `Source_Name` | Text | Which raw file/report the row came from (lineage/audit trail). |
| `Specialty_Group` | Text | This project's own grouping of specialties into broader clinical areas (e.g. "Heart", "Bones") — not an NTPF field, added by `data/mapping/Specialty_Mapping.csv`. |

## Adult / Child split

NTPF reports every waiting list broken out by `Adult` and `Child`. There's no
single fixed age cutoff published in the open data documentation itself —
in practice it follows where the patient is treated (paediatric vs adult
services), which is why some specialties (e.g. Developmental Paediatrics)
only ever appear under `Child`, and most surgical/medical specialties appear
under both.

## Time band width by source era

| Source | Time_Bands values |
|---|---|
| Older long-format exports (2014-2020, e.g. the `IN_WL 2018`-style file) | `0-3 Months`, `3-6 Months`, `6-9 Months`, `9-12 Months`, `12-15 Months`, `15-18 Months`, `18+ Months` (finer granularity) |
| Current "by Speciality" open data (2021+) and NTPF's published PDF summaries | `0-6 Months`, `6-12 Months`, `12-18 Months`, `18+ Months` (coarser, 4 bands) |

The ETL script (`etl/combine_waiting_lists.py`) normalises whichever shape it
finds into the same long format (one row per band) rather than assuming a
fixed set of band labels — check `Time_Bands.unique()` after loading your own
downloaded files and update `powerbi/Data_Model.md`'s `Time_Bands_Midpoint`
table to match if the bands differ from what's documented there.

## Small Volume Specialties suppression (Statistical Disclosure Control)

NTPF applies **Statistical Disclosure Control (SDC)** before publishing, to
avoid indirectly identifying individual patients in small groups:

- Where a specialty/hospital/time-band cell has **fewer than 5** patients,
  NTPF does not publish the exact number.
- Specialties that fall below NTPF's reporting threshold are aggregated
  together under **"Small Volume Specialties"** rather than published
  individually.
- Because of this rounding and aggregation, **row-level sums in this dataset
  occasionally differ from NTPF's own published specialty `Total` by 1-2
  patients** — this is expected NTPF SDC behaviour, not a bug in this
  project's ETL. Don't "fix" small mismatches by adjusting the raw numbers.

Treat `Small Volume Specialties` as its own bucket rather than trying to
attribute it to a particular clinical area — that's the whole point of the
suppression.

## Sources

- NTPF Open Data: https://www.ntpf.ie/waiting-list-data/open-data/
- NTPF monthly press releases (national totals): https://www.ntpf.ie/publications/
- Data dictionary published alongside the Open Data CSVs on data.gov.ie
