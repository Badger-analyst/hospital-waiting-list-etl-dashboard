"""
Basic data-quality and ETL assertions.

Run with: pytest tests/

Covers:
  - no nulls in Total
  - row counts within an expected range (sanity check against silent
    truncation or duplicate-append bugs)
  - every Specialty_Name maps successfully to Specialty_Group
  - transform_file() correctly normalises both the long-format shape
    (Time_Bands as a column) and the wide-format shape (time bands as
    separate columns) into the same standard schema
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "etl"))

from combine_waiting_lists import STANDARD_COLUMNS, transform_file  # noqa: E402

PROCESSED_DIR = ROOT_DIR / "data" / "processed"


@pytest.fixture(scope="module")
def all_data():
    path = PROCESSED_DIR / "All_Data.csv"
    if not path.exists():
        pytest.skip(
            f"{path} not found - run etl/build_sample_from_ntpf_published_reports.py "
            "or etl/combine_waiting_lists.py first"
        )
    return pd.read_csv(path)


def test_no_nulls_in_total(all_data):
    assert all_data["Total"].isna().sum() == 0, "Total column contains nulls"


def test_total_is_non_negative(all_data):
    assert (all_data["Total"] >= 0).all(), "Total contains negative values"


def test_row_count_within_expected_range(all_data):
    # Sanity check, not a precise bound - catches gross ETL bugs (e.g. an
    # accidental double-append, or a folder silently returning zero files)
    # without being so tight it breaks every time you add another month.
    assert 50 <= len(all_data) <= 200_000, (
        f"Row count {len(all_data)} is outside the sane range - check for a "
        "duplicate append or an empty raw folder"
    )


def test_all_specialty_names_map_to_a_group(all_data):
    unmapped = all_data.loc[all_data["Specialty_Group"].isna(), "Specialty_Name"].unique()
    assert len(unmapped) == 0, (
        f"{len(unmapped)} specialty name(s) not found in Specialty_Mapping.csv: "
        f"{sorted(unmapped)}"
    )


def test_required_columns_present(all_data):
    expected = set(STANDARD_COLUMNS) | {"Source_Name", "Specialty_Group"}
    missing = expected - set(all_data.columns)
    assert not missing, f"All_Data.csv is missing columns: {missing}"


# --------------------------------------------------------------------------
# ETL unit tests - long-format vs wide-format ("by Speciality") normalisation
# --------------------------------------------------------------------------
def test_transform_file_handles_long_format(tmp_path):
    """Older long-format exports already have a Time_Bands column."""
    sample = tmp_path / "IN_WL_sample.csv"
    sample.write_text(
        "Archive_Date,Specialty_HIPE,Specialty_Name,Case_Type,Adult_Child,"
        "Age_Profile,Time_Bands,Total\n"
        "31/01/2018,600,Otolaryngology (ENT),Day Case,Child,0-15,0-3 Months,14\n"
        "31/01/2018,600,Otolaryngology (ENT),Day Case,Child,0-15,3-6 Months,2\n"
    )
    result = transform_file(sample, case_type_default="Inpatient")
    assert list(result["Time_Bands"]) == ["0-3 Months", "3-6 Months"]
    assert list(result["Total"]) == [14, 2]
    assert set(STANDARD_COLUMNS).issubset(result.columns)


def test_transform_file_handles_wide_by_speciality_format(tmp_path):
    """Current 'by Speciality' exports have time bands as separate columns
    and no Case_Type column - the folder tells you Case_Type instead."""
    sample = tmp_path / "OpenData_OPNational02_sample.csv"
    sample.write_text(
        "ArchiveDate,Adult_Child,Speciality,0-6 Months,6-12 Months,12-18 Months,18+ Months,Total\n"
        "31/07/2023,Adult,Cardiology,22210,8377,4160,1837,36584\n"
    )
    result = transform_file(sample, case_type_default="Outpatient")
    assert set(result["Time_Bands"]) == {"0-6 Months", "6-12 Months", "12-18 Months", "18+ Months"}
    assert result["Total"].sum() == 22210 + 8377 + 4160 + 1837
    assert (result["Case_Type"] == "Outpatient").all()
    assert (result["Specialty_Name"] == "Cardiology").all()


def test_transform_file_raises_on_genuinely_missing_columns(tmp_path):
    sample = tmp_path / "broken.csv"
    sample.write_text("Not_A_Real_Column\n1\n")
    with pytest.raises(ValueError):
        transform_file(sample, case_type_default="Inpatient")
