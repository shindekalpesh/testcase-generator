"""
Shared test setup. pytest loads this file automatically.

Fixtures are reusable building blocks: a test asks for one by naming it as
an argument, e.g. `def test_x(make_excel): ...`.
"""

import pytest
from openpyxl import Workbook

# The sample input from spec §4, one list per column: [name, type, values...]
SAMPLE_COLUMNS = [
    ["colour", "list", "red", "orange", "blue"],
    ["age", "range", 18, 60],
    ["agency name", "list", "online", "offline", "broker"],
    ["pt", "range", 7, 15],
    ["smoker status", "list", "smoker", "non smoker"],
]

# What the parser should return for SAMPLE_COLUMNS (spec §5).
SAMPLE_PARAMETERS = {
    "colour": {"type": "list", "values": ["red", "orange", "blue"]},
    "age": {"type": "range", "values": [18, 60]},
    "agency name": {"type": "list", "values": ["online", "offline", "broker"]},
    "pt": {"type": "range", "values": [7, 15]},
    "smoker status": {"type": "list", "values": ["smoker", "non smoker"]},
}


@pytest.fixture
def make_excel(tmp_path):
    """
    Returns a function that writes an input workbook and returns its path.
    `tmp_path` is a fresh temporary folder pytest creates for each test.

        path = make_excel([["age", "range", 18, 60]])
    """
    def _make(columns, name="input.xlsx", folder=None):
        workbook = Workbook()
        sheet = workbook.active
        for col_number, column in enumerate(columns, start=1):
            for row_number, value in enumerate(column, start=1):
                if value is not None:
                    sheet.cell(row=row_number, column=col_number, value=value)
        path = (folder or tmp_path) / name
        workbook.save(path)
        return path

    return _make


@pytest.fixture
def sample_parameters():
    """A fresh copy of the parsed sample, so no test can change another's data."""
    return {name: {"type": spec["type"], "values": list(spec["values"])}
            for name, spec in SAMPLE_PARAMETERS.items()}
