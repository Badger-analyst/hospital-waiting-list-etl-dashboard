"""
combine_waiting_lists.py

Reproduces, in Python, the Power Query pattern used in Power BI Desktop for
this project:

    Parameter (folder path)
      -> Sample File
      -> Transform Sample File (custom function)
      -> Combine Files ("Filtered Hidden Files1" -> "Invoke Custom Function1")
      -> Append queries into All_Data
      -> Merge with Mapping_Specialty on Specialty_Name -> Specialty

Source data: NTPF (National Treatment Purchase Fund, Ireland) National
Public Hospital Waiting List Open Data - "by Speciality" reports.
https://www.ntpf.ie/waiting-list-data/open-data/

Drop the raw monthly CSVs you download from that page into:
    data/raw/inpatient/   (IPDC Waiting List by Speciality *.csv)
    data/raw/outpatient/  (OP Waiting List by Speciality *.csv)

Then run:
    python etl/combine_waiting_lists.py

Outputs (mirrors the Power BI data model tables):
    data/processed/Inpatient.csv
    data/processed/Outpatient.csv
    data/processed/All_Data.csv   (Inpatient + Outpatient, mapped to Specialty_Group)
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# Paths (the "Parameter" queries in the Power BI version)
# --------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_INPATIENT_DIR = ROOT_DIR / "data" / "raw" / "inpatient"
RAW_OUTPATIENT_DIR = ROOT_DIR / "data" / "raw" / "outpatient"
MAPPING_FILE = ROOT_DIR / "data" / "mapping" / "Specialty_Mapping.csv"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
LOG_DIR = ROOT_DIR / "logs"

# Standardised output schema, matching Archive_Date/Specialty_HIPE/
# Specialty_Name/Case_Type/Adult_Child/Age_Profile/Time_Bands/Total
STANDARD_COLUMNS = [
    "Archive_Date",
    "Specialty_HIPE",
    "Specialty_Name",
    "Case_Type",
    "Adult_Child",
    "Age_Profile",
    "Time_Bands",
    "Total",
]

# --------------------------------------------------------------------------
# Logging - rotating file handler, milestone logging, re-raise on failure
# --------------------------------------------------------------------------
_LOGGER_CACHE: dict[str, logging.Logger] = {}


def get_logger(name: str = "waiting_list_etl") -> logging.Logger:
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / f"{name}.log", maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    _LOGGER_CACHE[name] = logger
    return logger


@contextmanager
def pipeline_run(stage_name: str, logger: logging.Logger):
    logger.info("START  %s", stage_name)
    try:
        yield
        logger.info("SUCCESS %s", stage_name)
    except Exception:
        logger.exception("FAILURE %s", stage_name)
        raise  # re-raise so failures propagate to the caller/orchestrator


log = get_logger()

# --------------------------------------------------------------------------
# "Transform Sample File" - the custom function invoked over every file
# --------------------------------------------------------------------------
def transform_file(path: Path, case_type_default: str) -> pd.DataFrame:
    """
    Reads one NTPF monthly CSV and normalises it to STANDARD_COLUMNS.

    Handles the real-world NTPF export shapes seen across years - these
    differ more than you'd expect, so don't assume a new download matches
    exactly without checking:

      - Older long-format "by Hospital"/"by Group Hospital" exports
        (2014-2020, e.g. the `IN_WL 2018`-style file): one row per
        Archive_Date x Specialty x Case_Type x Adult_Child x Age_Profile x
        Time_Bands, with Hospital_Group/Hospital_HIPE/Hospital_Name columns
        that are dropped here since this project reports at national/
        specialty level, not per-hospital. Time_Bands has 7 finer bands
        (0-3 Months ... 18+ Months).
      - Current "by Speciality" open data (2021+): WIDE format - one row per
        Archive_Date x Specialty x Adult_Child, with the 4 time bands
        (0-6 Months, 6-12 Months, 12-18 Months, 18+ Months) as separate
        columns rather than a Time_Bands column. Melted into long format
        below. No Case_Type column in this export shape - the folder
        (inpatient/outpatient) tells you which, hence case_type_default.
    """
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    # Drop hospital-level columns if present (older "by Hospital" exports)
    for col in ("Hospital_Group", "Hospital_HIPE", "Hospital_Name"):
        if col in df.columns:
            df = df.drop(columns=col)

    # Normalise the "by Speciality" WIDE shape (time bands as columns) into
    # the long shape (one Time_Bands/Total row per band) used everywhere else.
    WIDE_BAND_COLUMNS = ["0-6 Months", "6-12 Months", "12-18 Months", "18+ Months"]
    if "Time_Bands" not in df.columns and any(c in df.columns for c in WIDE_BAND_COLUMNS):
        present_band_cols = [c for c in WIDE_BAND_COLUMNS if c in df.columns]
        # The wide export also carries its own aggregate Total column
        # alongside the per-band columns - drop it before melting since
        # we're deriving a per-band Total instead (summing the bands
        # reproduces it, modulo NTPF's own SDC rounding).
        id_cols = [c for c in df.columns if c not in WIDE_BAND_COLUMNS and c != "Total"]
        df = df.drop(columns=["Total"], errors="ignore").melt(
            id_vars=id_cols, value_vars=present_band_cols,
            var_name="Time_Bands", value_name="Total",
        )

    # Some NTPF exports call the specialty column "Speciality" (one 'i')
    # rather than "Specialty_Name" - normalise it.
    if "Specialty_Name" not in df.columns and "Speciality" in df.columns:
        df = df.rename(columns={"Speciality": "Specialty_Name"})

    if "Archive_Date" not in df.columns and "ArchiveDate" in df.columns:
        df = df.rename(columns={"ArchiveDate": "Archive_Date"})

    # Case_Type isn't always present (some exports are Inpatient/Outpatient-
    # specific with no Case_Type column) - fall back to the folder-derived
    # default, matching how the Power Query parameter drives this per-folder.
    if "Case_Type" not in df.columns:
        df["Case_Type"] = case_type_default

    # Age_Profile isn't published in every export shape either - the current
    # "by Speciality" format only splits Adult_Child, with no finer age band.
    if "Age_Profile" not in df.columns:
        df["Age_Profile"] = "All Ages"

    # Specialty_HIPE isn't published in every export shape - keep it as a
    # nullable column rather than failing the whole file over it.
    if "Specialty_HIPE" not in df.columns:
        df["Specialty_HIPE"] = pd.NA

    missing = [c for c in STANDARD_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name}: missing expected columns {missing}")

    df = df[STANDARD_COLUMNS].copy()
    df["Archive_Date"] = pd.to_datetime(df["Archive_Date"], dayfirst=True, errors="coerce")
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0).astype(int)
    df["Source_Name"] = path.name
    return df


# --------------------------------------------------------------------------
# "Combine Files" - folder scan + append
# --------------------------------------------------------------------------
def combine_folder(folder: Path, case_type_default: str, logger: logging.Logger) -> pd.DataFrame:
    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in %s - did you download the NTPF files there?", folder)
        return pd.DataFrame(columns=STANDARD_COLUMNS + ["Source_Name"])

    frames = []
    for f in csv_files:
        logger.info("Reading %s", f.name)
        frames.append(transform_file(f, case_type_default))

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Combined %d files from %s -> %d rows", len(csv_files), folder.name, len(combined))
    return combined


# --------------------------------------------------------------------------
# Merge with Mapping_Specialty
# --------------------------------------------------------------------------
def apply_specialty_mapping(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    mapping = pd.read_csv(MAPPING_FILE)
    merged = df.merge(
        mapping, how="left", left_on="Specialty_Name", right_on="Specialty"
    ).drop(columns=["Specialty"])

    unmapped = merged.loc[merged["Specialty_Group"].isna(), "Specialty_Name"].unique()
    if len(unmapped):
        logger.warning(
            "%d specialty name(s) not found in Specialty_Mapping.csv: %s",
            len(unmapped), ", ".join(sorted(unmapped)),
        )
        merged["Specialty_Group"] = merged["Specialty_Group"].fillna("Unmapped")

    return merged


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with pipeline_run("Combine Inpatient files", log):
        inpatient = combine_folder(RAW_INPATIENT_DIR, "Inpatient", log)

    with pipeline_run("Combine Outpatient files", log):
        outpatient = combine_folder(RAW_OUTPATIENT_DIR, "Outpatient", log)

    if inpatient.empty and outpatient.empty:
        log.warning(
            "Both raw folders are empty - leaving data/processed/ untouched "
            "(including the sample dataset, if that's what's there) rather "
            "than overwriting it with nothing. Download the NTPF CSVs into "
            "data/raw/inpatient/ and data/raw/outpatient/ and re-run."
        )
        return

    with pipeline_run("Apply Specialty_Mapping and write outputs", log):
        inpatient_mapped = apply_specialty_mapping(inpatient, log)
        outpatient_mapped = apply_specialty_mapping(outpatient, log)

        inpatient_mapped.to_csv(PROCESSED_DIR / "Inpatient.csv", index=False)
        outpatient_mapped.to_csv(PROCESSED_DIR / "Outpatient.csv", index=False)

        all_data = pd.concat([inpatient_mapped, outpatient_mapped], ignore_index=True)
        all_data.to_csv(PROCESSED_DIR / "All_Data.csv", index=False)

        log.info(
            "Wrote Inpatient (%d rows), Outpatient (%d rows), All_Data (%d rows) to %s",
            len(inpatient_mapped), len(outpatient_mapped), len(all_data), PROCESSED_DIR,
        )


if __name__ == "__main__":
    main()
