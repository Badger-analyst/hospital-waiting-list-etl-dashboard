"""
build_sample_from_ntpf_published_reports.py

Populates data/processed/ with a REAL (not synthetic) sample dataset,
transcribed from NTPF's own published national summary reports, so the
analysis notebook, tests and Power BI model all have something genuine to
run against before you've downloaded the full multi-year CSVs yourself.

Sources (all NTPF / National Treatment Purchase Fund, Ireland - CC-BY):
  - Inpatient/Day Case by Specialty, Adult & Child, as at 31/08/2023
    https://www.ntpf.ie/home/pdf/2023/08/nationalnumbers/in-patient/National02.pdf
  - Outpatient by Specialty, Adult & Child, as at 27/07/2023
    https://www.ntpf.ie/home/pdf/2023/07/nationalnumbers/out-patient/National02.pdf
  - National monthly totals (press releases), Oct 2024 - Sep 2025
    https://www.ntpf.ie/?p=194 (Oct 2024), ?p=3984 (Nov 2024), ?p=4017 (Dec 2024),
    ?p=4476 (Jun 2025), ?p=4613 (Sep 2025)

Limitations vs the full NTPF Open Data CSVs (documented in the README):
  - These national PDF summaries don't publish Specialty_HIPE codes or the
    finer Age_Profile bands - only Specialty x Adult/Child x 4 time bands.
  - Only two specialty-level snapshots (Aug 2023 IP, Jul 2023 OP) are
    transcribed here, so the specialty-level analysis is a snapshot, not a
    multi-year trend. The multi-year *national total* trend (Oct 2024-Sep
    2025) is real and used for the trend/gap questions in the notebook.
  - Row sums occasionally differ from NTPF's published Total by 1-2 due to
    NTPF's own Statistical Disclosure Control (SDC) rounding - see
    docs/data_dictionary.md.
"""

from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MAPPING_FILE = ROOT_DIR / "data" / "mapping" / "Specialty_Mapping.csv"

TIME_BANDS = ["0-6 Months", "6-12 Months", "12-18 Months", "18+ Months"]

# (Specialty_Name, Adult_Child, Total, 0-6, 6-12, 12-18, 18+)
# Inpatient/Day Case as at 31/08/2023
IP_ROWS = [
    ("Anaesthetics", "Adult", 90, 88, 2, 0, 0),
    ("Breast Surgery", "Adult", 213, 107, 41, 30, 36),
    ("Cardiology", "Adult", 3265, 2519, 519, 173, 54),
    ("Cardio-Thoracic Surgery", "Adult", 345, 284, 33, 7, 21),
    ("Clinical Immunology", "Adult", 403, 208, 127, 58, 10),
    ("Dental Surgery", "Adult", 55, 44, 6, 2, 4),
    ("Dermatology", "Adult", 921, 658, 153, 75, 35),
    ("Endocrinology", "Adult", 32, 14, 2, 4, 13),
    ("Gastro-Enterology", "Adult", 653, 398, 155, 26, 74),
    ("Gastro-Intestinal Surgery", "Adult", 633, 281, 158, 81, 113),
    ("General Medicine", "Adult", 215, 164, 31, 12, 9),
    ("General Surgery", "Adult", 12473, 7311, 2390, 1189, 1583),
    ("Geriatric Medicine", "Adult", 25, 19, 4, 2, 0),
    ("Gynaecology", "Adult", 5685, 3878, 981, 350, 476),
    ("Haematology", "Adult", 46, 43, 4, 0, 0),
    ("Hepato-Biliary Surgery", "Adult", 48, 21, 14, 6, 8),
    ("Maxillo-Facial", "Adult", 1633, 568, 554, 242, 269),
    ("Nephrology", "Adult", 52, 49, 4, 0, 0),
    ("Neurology", "Adult", 236, 190, 20, 14, 13),
    ("Neurosurgery", "Adult", 794, 393, 220, 135, 47),
    ("Oncology", "Adult", 85, 85, 0, 0, 0),
    ("Ophthalmology", "Adult", 8606, 5733, 1853, 543, 477),
    ("Orthopaedics", "Adult", 8981, 5790, 1689, 670, 832),
    ("Otolaryngology (ENT)", "Adult", 5317, 2922, 1146, 651, 598),
    ("Pain Relief", "Adult", 5399, 3438, 1299, 313, 350),
    ("Plastic Surgery", "Adult", 6139, 3448, 1235, 596, 860),
    ("Radiology", "Adult", 120, 109, 4, 4, 4),
    ("Respiratory Medicine", "Adult", 912, 708, 86, 100, 18),
    ("Rheumatology", "Adult", 706, 497, 104, 78, 27),
    ("Small Volume Specialties", "Adult", 7, 7, 0, 0, 0),
    ("Urology", "Adult", 7860, 5574, 1210, 410, 666),
    ("Vascular Surgery", "Adult", 1651, 1156, 305, 104, 86),
    ("Cardio-Thoracic Surgery", "Child", 58, 49, 2, 4, 2),
    ("Clinical Immunology", "Child", 405, 125, 100, 129, 51),
    ("Dental Surgery", "Child", 331, 169, 66, 39, 56),
    ("General Surgery", "Child", 283, 191, 54, 14, 23),
    ("Maxillo-Facial", "Child", 189, 84, 48, 38, 19),
    ("Ophthalmology", "Child", 915, 465, 292, 92, 66),
    ("Orthopaedics", "Child", 353, 185, 75, 62, 31),
]

# Outpatient as at 27/07/2023
OP_ROWS = [
    ("Breast Surgery", "Adult", 2125, 2109, 16, 0, 0),
    ("Cardiology", "Adult", 36584, 22210, 8377, 4160, 1837),
    ("Cardio-Thoracic Surgery", "Adult", 404, 313, 41, 27, 23),
    ("Chemical Pathology", "Adult", 63, 49, 14, 0, 0),
    ("Clinical (Medical) Genetics", "Adult", 3359, 1048, 752, 793, 766),
    ("Clinical Immunology", "Adult", 2334, 1312, 603, 413, 6),
    ("Clinical Neurophysiology", "Adult", 1736, 626, 393, 434, 283),
    ("Dermatology", "Adult", 45587, 26077, 8673, 4255, 6582),
    ("Diabetes Mellitus", "Adult", 2057, 1340, 419, 192, 106),
    ("Endocrinology", "Adult", 19628, 8159, 4058, 2982, 4429),
    ("Gastro-Enterology", "Adult", 16396, 11111, 3478, 1166, 641),
    ("Gastro-Intestinal Surgery", "Adult", 269, 163, 70, 27, 9),
    ("General Medicine", "Adult", 18940, 10417, 3866, 2507, 2150),
    ("General Surgery", "Adult", 36104, 26459, 5714, 2502, 1429),
    ("Geriatric Medicine", "Adult", 3854, 3271, 391, 93, 99),
    ("Gynaecology", "Adult", 29179, 22138, 4597, 1362, 1082),
    ("Haematology", "Adult", 9197, 5472, 1880, 1052, 793),
    ("Hepato-Biliary Surgery", "Adult", 97, 81, 14, 2, 0),
    ("Infectious Diseases", "Adult", 1307, 860, 443, 2, 2),
    ("Maxillo-Facial", "Adult", 4498, 1713, 668, 480, 1637),
    ("Respiratory Medicine", "Adult", 21629, 12300, 4742, 2037, 2550),
    ("Rheumatology", "Adult", 14511, 8381, 2665, 1424, 2041),
    ("Small Volume Specialities", "Adult", 128, 81, 24, 15, 8),
    ("Urology", "Adult", 23312, 12967, 4757, 1970, 3618),
    ("Vascular Surgery", "Adult", 14261, 8048, 2818, 1805, 1590),
    ("Cardiology", "Child", 80, 47, 10, 7, 16),
    ("Cardio-Thoracic Surgery", "Child", 60, 56, 2, 2, 0),
    ("Clinical (Medical) Genetics", "Child", 1221, 548, 335, 296, 42),
    ("Clinical Immunology", "Child", 869, 438, 175, 73, 183),
    ("Dental Surgery", "Child", 319, 184, 88, 40, 7),
    ("Dermatology", "Child", 3168, 1617, 491, 366, 694),
    ("Developmental Paediatrics", "Child", 1101, 355, 248, 208, 290),
    ("Gastro-Enterology", "Child", 31, 26, 4, 2, 0),
    ("General Medicine", "Child", 31, 23, 7, 2, 0),
    ("General Surgery", "Child", 1533, 882, 340, 155, 156),
    ("Gynaecology", "Child", 732, 518, 142, 63, 9),
    ("Haematology", "Child", 85, 71, 9, 4, 2),
    ("Immunology", "Child", 328, 252, 71, 4, 2),
    ("Maxillo-Facial", "Child", 436, 206, 99, 46, 85),
    ("Neurology", "Child", 38, 23, 10, 4, 2),
    ("Ophthalmology", "Child", 3923, 2070, 755, 454, 644),
]

# Real NTPF press-release national totals, end of month (source URLs in module docstring)
NATIONAL_MONTHLY_TOTALS = [
    ("2024-10-31", "Inpatient/Day Case", 87753),
    ("2024-10-31", "Outpatient", 588544),
    ("2024-10-31", "GI Endoscopy", 24442),
    ("2024-11-30", "Inpatient/Day Case", 88296),
    ("2024-11-30", "Outpatient", 572403),
    ("2024-11-30", "GI Endoscopy", 24819),
    ("2024-12-31", "Inpatient/Day Case", 91031),
    ("2024-12-31", "Outpatient", 557187),
    ("2024-12-31", "GI Endoscopy", 25744),
    ("2025-06-30", "Inpatient/Day Case", 99863),
    ("2025-06-30", "Outpatient", 600390),
    ("2025-06-30", "GI Endoscopy", 31367),
    ("2025-09-30", "Inpatient/Day Case", 100045),
    ("2025-09-30", "Outpatient", 626521),
    ("2025-09-30", "GI Endoscopy", 33784),
]


def rows_to_long(rows, archive_date, case_type, source_name):
    records = []
    for specialty, adult_child, total, *bands in rows:
        for band_label, band_value in zip(TIME_BANDS, bands):
            records.append(
                {
                    "Archive_Date": archive_date,
                    "Specialty_HIPE": pd.NA,
                    "Specialty_Name": specialty,
                    "Case_Type": case_type,
                    "Adult_Child": adult_child,
                    "Age_Profile": "All Ages",
                    "Time_Bands": band_label,
                    "Total": band_value,
                    "Source_Name": source_name,
                }
            )
    return pd.DataFrame.from_records(records)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    mapping = pd.read_csv(MAPPING_FILE)

    inpatient = rows_to_long(
        IP_ROWS, "2023-08-31", "Inpatient/Day Case",
        "NTPF National02.pdf (in-patient, Aug 2023)",
    )
    outpatient = rows_to_long(
        OP_ROWS, "2023-07-27", "Outpatient",
        "NTPF National02.pdf (out-patient, Jul 2023)",
    )

    for df, path in (
        (inpatient, PROCESSED_DIR / "Inpatient.csv"),
        (outpatient, PROCESSED_DIR / "Outpatient.csv"),
    ):
        df.to_csv(path, index=False)

    all_data = pd.concat([inpatient, outpatient], ignore_index=True)
    all_data = all_data.merge(
        mapping, how="left", left_on="Specialty_Name", right_on="Specialty"
    ).drop(columns=["Specialty"])
    all_data.to_csv(PROCESSED_DIR / "All_Data.csv", index=False)

    national = pd.DataFrame(
        NATIONAL_MONTHLY_TOTALS, columns=["Archive_Date", "Case_Type", "Total"]
    )
    national.to_csv(PROCESSED_DIR / "National_Monthly_Totals.csv", index=False)

    print(f"Wrote {len(inpatient)} inpatient rows, {len(outpatient)} outpatient rows, "
          f"{len(all_data)} all_data rows, {len(national)} national total rows to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
