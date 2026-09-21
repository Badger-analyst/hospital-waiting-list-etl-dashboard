# Power BI Build Guide

Recreates the report shown in the reference screenshots: folder-combine ETL
in Power Query, a `Mapping_Specialty` lookup, and a two-page report
(Summary / Detail).

Power BI Desktop can't be built headlessly here, so this is the click-by-click
guide — expect ~30-45 minutes end to end.

## 1. Get the data into Power Query

For **each** of Inpatient and Outpatient:

1. `Get Data` → `Folder` → point at `data/raw/inpatient` (repeat for `outpatient`)
2. Power Query auto-generates a **Sample File**, **Transform Sample File**
   (custom function) and a **Parameter1** for the folder path — this is the
   "Helper Queries" group you saw in the video. Keep the defaults.
3. In the sample file transform: promote headers, set types
   (`Archive_Date` → Date, `Specialty_HIPE` → Whole Number, `Total` → Whole
   Number, everything else → Text), remove any `Hospital_*` columns if
   present (older NTPF exports include them).
4. Close & Apply. You'll get an `Inpatient` and an `Outpatient` query, each
   showing "10 columns, 999+ rows" the same way the video's screenshot does.

## 2. Load the mapping table

1. `Get Data` → `Text/CSV` → `data/mapping/Specialty_Mapping.csv`
2. Rename the query `Mapping_Specialty`.

## 3. Build `All_Data`

1. Duplicate `Inpatient`, rename `All_Data`
2. Home → `Append Queries` → append `Outpatient`
3. Home → `Merge Queries` → join `All_Data[Specialty_Name]` to
   `Mapping_Specialty[Specialty]`, join kind **Left Outer**
4. Expand the merged column, keep only `Specialty_Group`
5. Close & Apply

## 4. Relationships (Model view)

- Drag `Mapping_Specialty[Specialty]` onto `All_Data[Specialty_Name]`
- Confirm cardinality: **One** (Mapping_Specialty) to **Many** (All_Data),
  single cross-filter direction — matches the `1 ... *` marker in the video's
  model view.
- Add `Time_Bands_Midpoint` and `Calc Method` tables per `Data_Model.md`

## 5. Measures

Paste in every measure from `DAX_Measures.md` (New Measure, on `All_Data`).

## 6. Report pages

### Summary page

| Visual | Fields |
|---|---|
| Card | `[Latest Month Wait List]` |
| Card | `[PY Latest Month Wait List]` |
| Card | `[Avg/Med Wait]` |
| Donut chart | Legend: `Case_Type`, Values: `[Avg/Med Wait]` |
| Clustered bar/column | Axis: `Time_Bands`, Legend: `Age_Profile`, Values: `[Avg/Med Wait]` |
| Line chart (x2, small multiple by `Case_Type`) | Axis: `Archive_Date` (Year), Values: `[Sum of Total by Year]` |
| Slicer | `Calc Method[Method]` |
| Slicer | `Archive_Date` (range) |

### Detail page

Same field list at a lower level of aggregation (drop the Year rollup, add a
table/matrix visual with `Specialty_Name`, `Specialty_Group`, `Case_Type`,
`Time_Bands`, `[Total]`) — mirrors the "Summary / Detail" tabs at the bottom
of the report canvas in the screenshot.

## 7. Publish

`File → Publish` to your Power BI workspace, or just keep the `.pbix` in
`powerbi/` in this repo for the portfolio (GitHub won't render it, but a
screenshot in the README will — see `powerbi/screenshots/`).
