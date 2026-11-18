"""
Excel Parser and Configuration Builder.

Reads the input workbook, sanitizes and validates every column, and returns
the internal configuration structure.

SSOT sections: §4 (Input Format), §5 (Parser Output), §6 (Sanitization & Validation)

Processing order for each column (matches §6):
    Row 1 header  -> trim, blank check, duplicate check        (§4, §6.6)
    Row 2 type    -> trim, lowercase, list/range check          (§4, §6.6)
    Row 3+ values -> 6.1 drop blanks
                     6.2 trim strings
                     6.3 whole floats -> int
                     6.4 remove duplicates (case-insensitive)
                     empty check                                (§6.6)
                     6.5 range rules (range columns only)

Validation errors are collected for the whole file first, then raised
together, so the user can fix everything in one pass (§6.6).
"""

import logging
import numbers
import re
from pathlib import Path

import pandas as pd

from config import config
from utils.logger import log_action

logger = logging.getLogger(__name__)

_INTEGER_TEXT = re.compile(r"^[+-]?\d+$")


class InputValidationError(Exception):
    """Raised when the input file fails one or more §6.6 checks."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__(f"Input validation failed with {len(errors)} error(s)")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def parse_excel(file_path):
    """
    Parse the input workbook (first sheet) into the §5 structure:

        {"age": {"type": "range", "values": [18, 60]}, ...}

    Raises:
        InputValidationError: one or more §6.6 checks failed.
        Exception: the file could not be read (logged first, then re-raised).
    """
    path = Path(file_path)
    log_action(logger, logging.INFO, "ReadExcel", File=path.name)

    try:
        # header=None: Row 1 is data to validate, not a pandas header.
        # dtype=object: stop pandas from turning numbers into floats.
        df = pd.read_excel(path, header=None, dtype=object, engine="openpyxl")
    except Exception as exc:
        log_action(
            logger, logging.ERROR, "ReadExcel",
            File=path.name, Reason=type(exc).__name__, Detail=exc,
        )
        raise

    parameters = {}
    errors = []
    seen_names = set()

    for col_index in df.columns:
        cells = df[col_index].tolist()
        result = _parse_column(col_index + 1, cells, seen_names, errors)
        if result is not None:
            name, param_type, values = result
            parameters[name] = {"type": param_type, "values": values}
            log_action(
                logger, logging.INFO, "ParameterParsed",
                Parameter=name, Type=param_type, ValueCount=len(values),
            )

    if not parameters and not errors:
        _record_error(errors, "InvalidHeader", Reason="NoParametersFound")

    if errors:
        raise InputValidationError(errors)

    return parameters


# ---------------------------------------------------------------------------
# Column processing
# ---------------------------------------------------------------------------
def _parse_column(excel_column, cells, seen_names, errors):
    """
    Validate one column. Returns (name, type, values), or None when the
    column is skipped or has an error (errors are appended to `errors`).
    """
    header = cells[0] if len(cells) > 0 else None
    metadata = cells[1] if len(cells) > 1 else None
    raw_values = cells[2:]

    # A column with nothing in it at all is a formatting leftover in Excel,
    # not a parameter. Skip it silently.
    if all(_is_blank(cell) for cell in cells):
        return None

    # --- Row 1: parameter name (§4) ---
    if _is_blank(header):
        _record_error(errors, "InvalidHeader",
                      Column=excel_column, Reason="BlankParameterName")
        return None

    name = str(_normalize_value(header))
    name_key = name.casefold()
    if name_key in config.RESERVED_PARAMETER_NAMES:
        _record_error(errors, "InvalidHeader",
                      Parameter=name, Reason="ReservedParameterName")
        return None
    if name_key in seen_names:
        _record_error(errors, "InvalidHeader",
                      Parameter=name, Reason="DuplicateParameterName")
        return None
    seen_names.add(name_key)

    # --- Row 2: metadata (§4) ---
    param_type = "" if _is_blank(metadata) else str(metadata).strip().lower()
    if param_type not in config.SUPPORTED_TYPES:
        shown = "<blank>" if _is_blank(metadata) else metadata
        _record_error(errors, "InvalidMetadata",
                      Parameter=name, Value=shown, Reason="UnsupportedType")
        return None

    # --- Row 3+: values (§6.1 - §6.4) ---
    values = [_normalize_value(v) for v in raw_values if not _is_blank(v)]
    values = _remove_duplicates(name, values)

    if not values:
        _record_error(errors, "EmptyParameter",
                      Parameter=name, Reason="NoValuesProvided")
        return None

    # --- Range rules (§6.5) ---
    if param_type == config.TYPE_RANGE:
        values = _build_range(name, values, errors)
        if values is None:
            return None

    return name, param_type, values


def _build_range(name, values, errors):
    """
    Apply §6.5. Returns [min, max] as ints, or None on error.

        2 values ascending  -> [min, max]
        2 values descending -> swapped, WARNING
        1 value             -> [v, v] fixed range, INFO
        >2 values           -> ERROR
        non-integer value   -> ERROR
    """
    integers = []
    has_invalid = False

    for value in values:
        as_int = _to_int(value)
        if as_int is None:
            _record_error(errors, "InvalidRangeValue",
                          Parameter=name, Value=value,
                          Reason="RangeValuesMustBeIntegers")
            has_invalid = True
        else:
            integers.append(as_int)

    if has_invalid:
        return None

    # A second pass catches duplicates that only appear after conversion,
    # e.g. the text "18" and the number 18 in the same column.
    integers = list(dict.fromkeys(integers))

    if len(integers) > 2:
        _record_error(errors, "InvalidRangeDefinition",
                      Parameter=name, ValueCount=len(integers),
                      Reason="RangeRequiresOneOrTwoValues")
        return None

    if len(integers) == 1:
        fixed = integers[0]
        log_action(logger, logging.INFO, "FixedValueRange",
                   Parameter=name, Value=fixed)
        return [fixed, fixed]

    first, second = integers
    if first > second:
        log_action(logger, logging.WARNING, "RangeNormalized",
                   Parameter=name, Original=[first, second],
                   Normalized=[second, first])
        return [second, first]

    return [first, second]


def _remove_duplicates(name, values):
    """
    §6.4: keep first occurrence, preserve order.
    Strings compare case-insensitively; a removed case-variant logs a WARNING.
    Exact duplicates are removed silently.
    """
    kept = {}  # comparison key -> value that was kept
    result = []

    for value in values:
        key = value.casefold() if isinstance(value, str) else value
        if key in kept:
            if isinstance(value, str) and value != kept[key]:
                log_action(logger, logging.WARNING, "CaseVariantDuplicateRemoved",
                           Parameter=name, Kept=kept[key], Removed=value)
            continue
        kept[key] = value
        result.append(value)

    return result


# ---------------------------------------------------------------------------
# Cell helpers
# ---------------------------------------------------------------------------
def _is_blank(value):
    """§6.1: None, NaN, or a string that is empty after trimming."""
    if isinstance(value, str):
        return value.strip() == ""
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _normalize_value(value):
    """
    §6.2: trim strings.
    §6.3: a float with no fractional part becomes int (18.0 -> 18).
    """
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return value
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        as_float = float(value)
        return int(as_float) if as_float.is_integer() else as_float
    return value


def _to_int(value):
    """
    Convert a range value to int, or return None if it is not a whole number.
    Accepts whole numbers stored as text (e.g. '18' in a text-formatted cell).
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        as_float = float(value)
        return int(as_float) if as_float.is_integer() else None
    if isinstance(value, str) and _INTEGER_TEXT.match(value):
        return int(value)
    return None


def _record_error(errors, action, **fields):
    """Log a §6.6 validation error and remember it for the final raise."""
    log_action(logger, logging.ERROR, action, **fields)
    errors.append({"action": action, **fields})
