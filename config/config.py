"""
Central configuration for the Test Case Generator.

Every fixed value from the SSOT lives here, so no other module hard-codes
a spec value. If the spec changes, this is the first file to update.

SSOT sections: §4, §8, §9, §10, §13, §15, §16, §17, §18, §20, §21
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (§21)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "testcase_generator.log"

# ---------------------------------------------------------------------------
# Input metadata types (§4 Row 2)
# ---------------------------------------------------------------------------
TYPE_LIST = "list"
TYPE_RANGE = "range"
SUPPORTED_TYPES = (TYPE_LIST, TYPE_RANGE)

# ---------------------------------------------------------------------------
# Scenario types (§14)
# ---------------------------------------------------------------------------
SCENARIO_TYPE_BOUNDARY = "Boundary"
SCENARIO_TYPE_NEGATIVE = "Negative"
SCENARIO_TYPE_PAIRWISE = "Pairwise"

# ---------------------------------------------------------------------------
# Expected results (§8, §9, §10)
# ---------------------------------------------------------------------------
EXPECTED_SUCCESS = "Policy Creation Success"
EXPECTED_VALIDATION_ERROR = "Validation Error"

# ---------------------------------------------------------------------------
# Boundary scenario reasons (§8) - order matters: it drives output order
# and which reason is kept when duplicate values are removed.
# ---------------------------------------------------------------------------
REASON_LOWER_MINUS_1 = "Lower Boundary -1"
REASON_LOWER = "Lower Boundary"
REASON_LOWER_PLUS_1 = "Lower Boundary +1"
REASON_UPPER_MINUS_1 = "Upper Boundary -1"
REASON_UPPER = "Upper Boundary"
REASON_UPPER_PLUS_1 = "Upper Boundary +1"

# Boundary and Negative reasons name the parameter under test (§8, §9)
SCENARIO_REASON_FORMAT = "{parameter} - {reason}"

# ---------------------------------------------------------------------------
# Negative test values (§9) - configurable
# ---------------------------------------------------------------------------
NEGATIVE_TEST_VALUES = {
    "numeric_range": [
        None,
        "",
        "ABC",
        "@@@",
        -1,
    ]
}

# Stored as (value, reason) pairs rather than a dict, because None and ""
# are awkward dict keys and the order must follow NEGATIVE_TEST_VALUES.
NEGATIVE_SCENARIO_REASONS = [
    (None, "Null"),
    ("", "Empty String"),
    ("ABC", "Alphabetic Value"),
    ("@@@", "Special Characters"),
    (-1, "Negative Number"),
]

# ---------------------------------------------------------------------------
# Pairwise (§10)
# ---------------------------------------------------------------------------
PAIRWISE_SCENARIO_REASON = "Pairwise Combination"

# ---------------------------------------------------------------------------
# Traceability IDs (§13)
# ---------------------------------------------------------------------------
BATCH_ID_PREFIX = "BAT"
POLICY_ID_PREFIX = "POL"
TESTCASE_ID_PREFIX = "TC"
ID_COUNTER_WIDTH = 6
ID_DATE_FORMAT = "%Y%m%d"
ID_TIME_FORMAT = "%H%M%S"

# ---------------------------------------------------------------------------
# Output columns (§15)
# ---------------------------------------------------------------------------
COL_BATCH_ID = "Batch_ID"
COL_POLICY_ID = "Policy_ID"
COL_TESTCASE_ID = "TestCase_ID"
COL_SCENARIO_TYPE = "Scenario_Type"
COL_SCENARIO_REASON = "Scenario_Reason"
COL_EXPECTED_RESULT = "Expected_Result"
COL_EXECUTION_STATUS = "Execution_Status"

LEADING_COLUMNS = [
    COL_BATCH_ID,
    COL_POLICY_ID,
    COL_TESTCASE_ID,
    COL_SCENARIO_TYPE,
    COL_SCENARIO_REASON,
]
TRAILING_COLUMNS = [
    COL_EXPECTED_RESULT,
    COL_EXECUTION_STATUS,
]

# Input parameters may not reuse a system column name (§6.6).
# Compared case-insensitively.
RESERVED_PARAMETER_NAMES = {name.casefold() for name in LEADING_COLUMNS + TRAILING_COLUMNS}

# ---------------------------------------------------------------------------
# Input file selection (§22)
# ---------------------------------------------------------------------------
INPUT_FILE_EXTENSION = ".xlsx"
EXCEL_LOCK_FILE_PREFIX = "~$"  # temp file Excel creates while a workbook is open

# ---------------------------------------------------------------------------
# Execution status (§16)
# ---------------------------------------------------------------------------
DEFAULT_EXECUTION_STATUS = "Not Executed"

# Dropdown options for the Execution_Status column (§16, §19)
EXECUTION_STATUS_VALUES = [
    DEFAULT_EXECUTION_STATUS,
    "Passed",
    "Failed",
    "Blocked",
]

# ---------------------------------------------------------------------------
# Output workbook (§17, §18)
# ---------------------------------------------------------------------------
OUTPUT_SHEET_NAME = "Generated_TestCases"
OUTPUT_FILE_TEMPLATE = "generated_{count}_testcases_{date}_{sequence}.xlsx"
OUTPUT_FILE_PATTERN = r"^generated_\d+_testcases_(\d{8})_(\d{3,})\.xlsx$"
OUTPUT_SEQUENCE_MIN_WIDTH = 3

# Display placeholders for values that would otherwise be a blank cell (§19)
NULL_DISPLAY = "<NULL>"
EMPTY_STRING_DISPLAY = "<EMPTY>"

# ---------------------------------------------------------------------------
# Logging (§20)
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
