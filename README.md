# Life Insurance Test Case Generator

Generates ready-to-execute test cases for a life insurance product from a small Excel sheet of product parameters.

You describe the parameters (age range, policy term, agency, smoker status, ...). The tool writes an Excel file of **Boundary**, **Negative** and **Pairwise** test cases. Each one has traceability IDs, an expected result and an execution status.

The design is defined in [`docs/PROJECT_SPECIFICATION.md`](docs/PROJECT_SPECIFICATION.md), which is the single source of truth. Changes are recorded in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

---

## Requirements

- Python **3.10 or newer**
- Windows, macOS or Linux

---

## Setup (Windows)

Open Command Prompt or PowerShell in the project folder:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS / Linux, activate with `source .venv/bin/activate` instead.

---

## Preparing the Input File

Use one worksheet (only the first sheet is read).

| Row | Contains |
|---|---|
| 1 | Parameter names |
| 2 | Type of each parameter: `list` or `range` |
| 3 onwards | Values |

Example (`input/sample_input.xlsx`):

| colour | age | agency name | pt | smoker status |
|---|---|---|---|---|
| list | range | list | range | list |
| red | 18 | online | 7 | smoker |
| orange | 60 | offline | 15 | non smoker |
| blue | | broker | | |

Rules:

- **list**: every allowed value, one per row.
- **range**: whole numbers only. Give the minimum and maximum in either order, or a single value for a fixed value (for example a fixed policy term of 10).
- Blank cells, extra spaces and duplicate values (including `Red` / `red`) are cleaned up automatically.
- Parameter names must be unique and must not reuse an output column name (`Batch_ID`, `Expected_Result`, ...).

---

## Running

With a file path:

```bash
python main.py input/my_product.xlsx
```

Or put exactly one `.xlsx` file in the `input/` folder and run:

```bash
python main.py
```

The console shows one line:

```text
Generated 48 test cases -> generated_48_testcases_20261118_001.xlsx
```

or, if something is wrong:

```text
7 input error(s) found. See logs/testcase_generator.log
```

The exit code is `0` on success and `1` on failure.

---

## Output

Files are written to `output/`:

```text
generated_<count>_testcases_<YYYYMMDD>_<sequence>.xlsx
```

The sequence restarts at `001` each day and never overwrites an earlier file.

Sheet `Generated_TestCases`, with these columns:

| Column | Meaning |
|---|---|
| Batch_ID | Same for every row in one run |
| Policy_ID | Scenario reference for evidence and defect logs |
| TestCase_ID | The row to execute |
| Scenario_Type | Boundary, Negative or Pairwise |
| Scenario_Reason | What is being tested, e.g. `age - Lower Boundary -1` |
| *your parameters* | Complete values to enter, in your input order |
| Expected_Result | `Policy Creation Success` or `Validation Error` |
| Execution_Status | Starts as `Not Executed`; testers update it |

`<NULL>` means "no value at all" and `<EMPTY>` means "an empty value".

---

## When Something Goes Wrong

Open `logs/testcase_generator.log`. Every problem is one line that names the parameter and the reason, for example:

```text
2026-11-18 16:42:03 | ERROR | parser.excel_parser | Action=InvalidRangeValue | Parameter=sa | Value=18.5 | Reason=RangeValuesMustBeIntegers
```

All input errors are listed in one run, so you can fix them all before running again.

| Reason in log | Fix |
|---|---|
| BlankParameterName | Fill in the Row 1 name for that column |
| DuplicateParameterName | Rename one of the two columns |
| ReservedParameterName | Rename the column; it clashes with an output column |
| UnsupportedType | Row 2 must be `list` or `range` |
| NoValuesProvided | Add at least one value under that parameter |
| RangeValuesMustBeIntegers | Range values must be whole numbers |
| RangeRequiresOneOrTwoValues | A range has only a minimum and a maximum |
| FileNotFound | Check the file path |
| ExpectedExactlyOneInputFile | Leave exactly one `.xlsx` in `input/`, or pass the path |

---

## Project Structure

```text
testcase-generator/
├── docs/          Specification and changelog
├── config/        All fixed values from the spec
├── parser/        Reads, cleans and validates the input
├── generators/    Boundary, Negative and Pairwise generators
├── utils/         Logging, IDs, shared helpers
├── writer/        Excel output
├── input/         Put input files here
├── output/        Generated files appear here
├── logs/          Log file
├── tests/         Automated tests
└── main.py        Entry point
```

---

## Running the Tests

For anyone changing the code. Testers running the tool don't need this.

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Expected result: `60 passed`. The tests write only to temporary folders, so your `input/`, `output/` and `logs/` are untouched.

Run them before and after every change. If a test fails, the message names the test and shows what was expected and what came out.
