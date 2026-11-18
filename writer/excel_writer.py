"""
Excel Writer.

SSOT sections: §15 (Columns), §16 (Execution Status), §17 (Sheet Name),
               §18 (File Naming), §19 (Formatting, NULL/EMPTY display)

Column order (§15):
    Batch_ID, Policy_ID, TestCase_ID, Scenario_Type, Scenario_Reason,
    <parameters in original input order>,
    Expected_Result, Execution_Status

File name (§18):
    generated_<count>_testcases_<YYYYMMDD>_<sequence>.xlsx
    sequence = highest existing sequence for that date + 1 (starts at 001)
"""

import logging
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from config import config
from utils.logger import log_action

logger = logging.getLogger(__name__)

_FILE_PATTERN = re.compile(config.OUTPUT_FILE_PATTERN)

_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill("solid", start_color="1F4E78")
_THIN = Side(style="thin", color="BFBFBF")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_MAX_COLUMN_WIDTH = 60


def write_test_cases(test_cases, parameter_names, generation_date,
                     output_dir=config.OUTPUT_DIR):
    """
    Write test cases (IDs already assigned) to a new workbook.

    Args:
        test_cases:      merged list in §14 order, with IDs (§13).
        parameter_names: parameter names in original input order.
        generation_date: 'YYYYMMDD', taken from the run timestamp.
        output_dir:      folder to write into.

    Returns:
        Path of the file written.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    columns = config.LEADING_COLUMNS + list(parameter_names) + config.TRAILING_COLUMNS
    file_path = output_dir / _build_file_name(len(test_cases), generation_date, output_dir)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = config.OUTPUT_SHEET_NAME

    sheet.append(columns)
    for test_case in test_cases:
        row = [_cell_value(test_case, column, parameter_names) for column in columns]
        sheet.append(row)

    _protect_text_cells(sheet)
    _format_sheet(sheet)
    _add_execution_status_dropdown(sheet, columns, len(test_cases))

    workbook.save(file_path)
    log_action(logger, logging.INFO, "ExcelGenerated", File=file_path.name)
    return file_path


# ---------------------------------------------------------------------------
# File naming (§18)
# ---------------------------------------------------------------------------
def _build_file_name(count, generation_date, output_dir):
    sequence = _next_sequence(generation_date, output_dir)
    padded = f"{sequence:0{config.OUTPUT_SEQUENCE_MIN_WIDTH}d}"
    return config.OUTPUT_FILE_TEMPLATE.format(
        count=count, date=generation_date, sequence=padded
    )


def _next_sequence(generation_date, output_dir):
    """Highest sequence for this date + 1. Non-matching files are ignored."""
    highest = 0
    for existing in output_dir.iterdir():
        match = _FILE_PATTERN.match(existing.name)
        if match and match.group(1) == generation_date:
            highest = max(highest, int(match.group(2)))
    return highest + 1


# ---------------------------------------------------------------------------
# Cell values
# ---------------------------------------------------------------------------
def _cell_value(test_case, column, parameter_names):
    """
    Parameter columns come from the nested 'parameters' dict; system columns
    from the top level. None and "" in parameter cells are shown as
    placeholders (§19), because both would otherwise be a blank cell.
    """
    if column in parameter_names:
        value = test_case["parameters"][column]
        if value is None:
            return config.NULL_DISPLAY
        if value == "":
            return config.EMPTY_STRING_DISPLAY
        return value
    return test_case[column]


def _protect_text_cells(sheet):
    """
    A text value starting with '=' would be saved by openpyxl as a FORMULA.
    Force every such cell to plain text, so an input value can never run as
    a formula when a tester opens the file.
    """
    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.data_type = "s"


# ---------------------------------------------------------------------------
# Formatting (§19)
# ---------------------------------------------------------------------------
def _add_execution_status_dropdown(sheet, columns, row_count):
    """
    §16/§19: Execution_Status cells accept only the configured values.
    Typing anything else is rejected by Excel with an error message.
    """
    if row_count == 0:
        return

    letter = get_column_letter(columns.index(config.COL_EXECUTION_STATUS) + 1)
    options = ",".join(config.EXECUTION_STATUS_VALUES)

    validation = DataValidation(
        type="list",
        formula1=f'"{options}"',
        allow_blank=False,
        showDropDown=False,  # openpyxl naming: False means the arrow IS shown
        showErrorMessage=True,
        errorTitle="Invalid Execution Status",
        error=f"Choose one of: {options.replace(',', ', ')}",
    )
    validation.add(f"{letter}2:{letter}{row_count + 1}")
    sheet.add_data_validation(validation)


def _format_sheet(sheet):
    for cell in sheet[1]:
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row in sheet.iter_rows():
        for cell in row:
            cell.border = _BORDER

    sheet.freeze_panes = "A2"                 # header stays visible on scroll
    sheet.auto_filter.ref = sheet.dimensions  # filter buttons on the header

    for column_cells in sheet.columns:
        longest = max(len(str(cell.value)) if cell.value is not None else 0
                      for cell in column_cells)
        letter = column_cells[0].column_letter
        sheet.column_dimensions[letter].width = min(longest + 2, _MAX_COLUMN_WIDTH)
