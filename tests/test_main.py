"""
End-to-end tests for main.py - spec §14, §20, §22.

These run the whole tool the way a tester does. Every test points the
input, output and log folders at a temporary folder, so your real
input/, output/ and logs/ are never touched.
"""

import pytest
from openpyxl import load_workbook

import main
from config import config
from conftest import SAMPLE_COLUMNS


@pytest.fixture
def folders(tmp_path, monkeypatch):
    """Redirect input/, output/ and the log file into tmp_path."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    monkeypatch.setattr(config, "INPUT_DIR", input_dir)
    monkeypatch.setattr(config, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(config, "LOG_FILE", tmp_path / "logs" / "test.log")
    return input_dir, output_dir


def test_success_prints_summary_and_writes_file(folders, make_excel, capsys):
    input_dir, output_dir = folders
    path = make_excel(SAMPLE_COLUMNS, folder=input_dir)

    exit_code = main.main([str(path)])

    [output_file] = output_dir.iterdir()
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == f"Generated 48 test cases -> {output_file.name}"
    assert load_workbook(output_file).active.max_row == 49  # header + 48


def test_output_order_is_boundary_negative_pairwise(folders, make_excel):
    input_dir, output_dir = folders
    main.main([str(make_excel(SAMPLE_COLUMNS, folder=input_dir))])

    sheet = load_workbook(next(output_dir.iterdir())).active
    types = [row[3] for row in sheet.iter_rows(min_row=2, values_only=True)]
    assert types == ["Boundary"] * 12 + ["Negative"] * 10 + ["Pairwise"] * 26


def test_input_errors_give_count_and_exit_1(folders, make_excel, capsys):
    input_dir, _ = folders
    path = make_excel([["gender", "lists", "M"], ["sa", "range", 18.5, 60]], folder=input_dir)

    assert main.main([str(path)]) == 1
    assert capsys.readouterr().out.startswith("2 input error(s) found.")


def test_missing_file_fails_cleanly(folders, capsys):
    assert main.main(["does_not_exist.xlsx"]) == 1
    assert capsys.readouterr().out.startswith("Generation failed.")


def test_no_argument_uses_only_file_and_ignores_lock_file(folders, make_excel, capsys):
    input_dir, _ = folders
    make_excel(SAMPLE_COLUMNS, folder=input_dir)
    (input_dir / "~$input.xlsx").touch()  # Excel's lock file

    assert main.main([]) == 0
    assert capsys.readouterr().out.startswith("Generated 48 test cases")


def test_no_argument_with_two_files_fails(folders, make_excel, capsys):
    input_dir, _ = folders
    make_excel(SAMPLE_COLUMNS, name="a.xlsx", folder=input_dir)
    make_excel(SAMPLE_COLUMNS, name="b.xlsx", folder=input_dir)

    assert main.main([]) == 1
    assert capsys.readouterr().out.startswith("Generation failed.")
