"""Tests for parser/excel_parser.py - spec §4, §5, §6."""

import logging

import pytest

from conftest import SAMPLE_COLUMNS, SAMPLE_PARAMETERS
from parser.excel_parser import InputValidationError, _normalize_value, parse_excel


def parse_errors(path):
    """Parse a file that should fail; return the list of error reasons."""
    with pytest.raises(InputValidationError) as caught:
        parse_excel(path)
    return [error["Reason"] for error in caught.value.errors]


# --- Valid input -----------------------------------------------------------

def test_sample_input_gives_spec_structure(make_excel):
    assert parse_excel(make_excel(SAMPLE_COLUMNS)) == SAMPLE_PARAMETERS


def test_parameters_keep_input_column_order(make_excel):
    result = parse_excel(make_excel(SAMPLE_COLUMNS))
    assert list(result) == ["colour", "age", "agency name", "pt", "smoker status"]


def test_names_values_and_type_are_trimmed(make_excel):
    result = parse_excel(make_excel([[" Colour ", " LIST ", " red ", "blue "]]))
    assert result == {"Colour": {"type": "list", "values": ["red", "blue"]}}


def test_blank_cells_are_ignored(make_excel):
    result = parse_excel(make_excel([["colour", "list", "red", None, "blue"]]))
    assert result["colour"]["values"] == ["red", "blue"]


def test_whole_float_becomes_int():
    assert _normalize_value(18.0) == 18
    assert type(_normalize_value(18.0)) is int
    assert _normalize_value(18.5) == 18.5


def test_case_variant_duplicate_keeps_first_and_warns(make_excel, caplog):
    path = make_excel([["colour", "list", "Red", "red", "Red", "blue"]])
    with caplog.at_level(logging.WARNING):
        result = parse_excel(path)
    assert result["colour"]["values"] == ["Red", "blue"]
    assert "Action=CaseVariantDuplicateRemoved" in caplog.text


def test_reversed_range_is_swapped_with_warning(make_excel, caplog):
    with caplog.at_level(logging.WARNING):
        result = parse_excel(make_excel([["age", "range", 60, 18]]))
    assert result["age"]["values"] == [18, 60]
    assert "Action=RangeNormalized" in caplog.text


@pytest.mark.parametrize("cells", [[10], [10, 10]])
def test_single_value_range_is_fixed_range(make_excel, cells):
    result = parse_excel(make_excel([["pt", "range", *cells]]))
    assert result["pt"]["values"] == [10, 10]


def test_whole_number_text_accepted_in_range(make_excel):
    result = parse_excel(make_excel([["age", "range", "18", 60]]))
    assert result["age"]["values"] == [18, 60]


def test_completely_empty_column_is_skipped(make_excel):
    result = parse_excel(make_excel([["age", "range", 18, 60], [], ["pt", "range", 7, 15]]))
    assert list(result) == ["age", "pt"]


# --- Invalid input (§6.6) ----------------------------------------------------

@pytest.mark.parametrize("column, reason", [
    ([None, "list", "a"], "BlankParameterName"),
    (["Expected_Result", "list", "a"], "ReservedParameterName"),
    (["gender", "lists", "M"], "UnsupportedType"),
    (["gender", None, "M"], "UnsupportedType"),
    (["agency", "list"], "NoValuesProvided"),
    (["sa", "range", 18.5, 60], "RangeValuesMustBeIntegers"),
    (["sa", "range", "abc", 60], "RangeValuesMustBeIntegers"),
    (["pt", "range", 5, 10, 15], "RangeRequiresOneOrTwoValues"),
])
def test_each_invalid_column_is_reported(make_excel, column, reason):
    assert parse_errors(make_excel([column])) == [reason]


def test_duplicate_name_is_case_insensitive(make_excel):
    path = make_excel([["age", "range", 18, 60], ["AGE", "range", 1, 2]])
    assert parse_errors(path) == ["DuplicateParameterName"]


def test_empty_sheet_is_reported(make_excel):
    assert parse_errors(make_excel([])) == ["NoParametersFound"]


def test_all_errors_reported_in_one_run(make_excel):
    path = make_excel([
        [None, "list", "a"],
        ["gender", "lists", "M"],
        ["agency", "list"],
        ["sa", "range", 18.5, 60],
    ])
    assert len(parse_errors(path)) == 4


def test_unreadable_file_raises(tmp_path):
    bad_file = tmp_path / "not_excel.xlsx"
    bad_file.write_text("not an excel file")
    with pytest.raises(Exception):
        parse_excel(bad_file)
