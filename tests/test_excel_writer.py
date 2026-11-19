"""Tests for writer/excel_writer.py - spec §15 to §19."""

from openpyxl import load_workbook

from writer.excel_writer import write_test_cases

DATE = "20261118"


def make_case(**parameters):
    """One test case with IDs, as the writer receives it."""
    return {
        "Batch_ID": "BAT_20261118_164057",
        "Policy_ID": "POL_20261118_164057_000001",
        "TestCase_ID": "TC_20261118_164057_000001",
        "Scenario_Type": "Negative",
        "Scenario_Reason": "age - Null",
        "parameters": parameters,
        "Expected_Result": "Validation Error",
        "Execution_Status": "Not Executed",
    }


def write_and_open(tmp_path, cases, names):
    path = write_test_cases(cases, names, DATE, output_dir=tmp_path)
    return path, load_workbook(path).active


def test_sheet_name_and_column_order(tmp_path):
    _, sheet = write_and_open(tmp_path, [make_case(colour="red", age=17)], ["colour", "age"])
    assert sheet.title == "Generated_TestCases"
    assert [c.value for c in sheet[1]] == [
        "Batch_ID", "Policy_ID", "TestCase_ID", "Scenario_Type", "Scenario_Reason",
        "colour", "age", "Expected_Result", "Execution_Status",
    ]
    assert [c.value for c in sheet[2]][5:7] == ["red", 17]


def test_file_name_and_daily_sequence(tmp_path):
    first = write_test_cases([make_case(age=1)], ["age"], DATE, output_dir=tmp_path)
    second = write_test_cases([make_case(age=1)] * 3, ["age"], DATE, output_dir=tmp_path)
    assert first.name == "generated_1_testcases_20261118_001.xlsx"
    assert second.name == "generated_3_testcases_20261118_002.xlsx"


def test_sequence_ignores_other_dates_and_unrelated_files(tmp_path):
    (tmp_path / "generated_9_testcases_20200101_007.xlsx").touch()
    (tmp_path / "notes.xlsx").touch()
    path = write_test_cases([make_case(age=1)], ["age"], DATE, output_dir=tmp_path)
    assert path.name.endswith("_20261118_001.xlsx")


def test_null_and_empty_shown_as_placeholders(tmp_path):
    _, sheet = write_and_open(tmp_path, [make_case(age=None), make_case(age="")], ["age"])
    assert sheet["F2"].value == "<NULL>"
    assert sheet["F3"].value == "<EMPTY>"


def test_text_starting_with_equals_is_not_a_formula(tmp_path):
    _, sheet = write_and_open(tmp_path, [make_case(agency="=1+1")], ["agency"])
    assert sheet["F2"].value == "=1+1"
    assert sheet["F2"].data_type == "s"


def test_execution_status_dropdown(tmp_path):
    _, sheet = write_and_open(tmp_path, [make_case(age=1)] * 3, ["age"])
    [dropdown] = sheet.data_validations.dataValidation
    assert dropdown.formula1 == '"Not Executed,Passed,Failed,Blocked"'
    assert str(dropdown.sqref) == "H2:H4"


def test_header_frozen_and_filtered(tmp_path):
    _, sheet = write_and_open(tmp_path, [make_case(age=1)], ["age"])
    assert sheet.freeze_panes == "A2"
    assert sheet.auto_filter.ref
    assert sheet["A1"].font.bold
