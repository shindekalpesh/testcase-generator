"""
Life Insurance Test Case Generator - entry point.

SSOT sections: §14 (Output Ordering), §20 (Console Output), §22 (Flow, Usage)

Usage:
    python main.py <input_file.xlsx>
    python main.py                      # uses the only .xlsx file in input/

Flow (§22):
    Input Excel -> Parser -> Boundary / Negative / Pairwise generators
    -> Merge (§14 order) -> IDs (§13) -> Excel Writer

Exactly one summary line is printed to the console (§20). Everything else
goes to logs/testcase_generator.log.

Exit codes: 0 = success, 1 = failure.
"""

import argparse
import logging
import sys
from pathlib import Path

from config import config
from generators.boundary_generator import generate_boundary_test_cases
from generators.negative_generator import generate_negative_test_cases
from generators.pairwise_generator import generate_pairwise_test_cases
from parser.excel_parser import InputValidationError, parse_excel
from utils.id_generator import IdGenerator
from utils.logger import log_action, setup_logging
from writer.excel_writer import write_test_cases

# Named explicitly: run as a script, __name__ would be "__main__".
logger = logging.getLogger("main")

LOG_HINT = "See logs/testcase_generator.log"


class InputFileError(Exception):
    """The input file could not be determined."""


def main(argv=None):
    args = _parse_arguments(argv)
    setup_logging()

    # The run timestamp is captured first, so every ID in this run and the
    # output file name share it (§13, §18).
    id_generator = IdGenerator()

    try:
        input_path = _resolve_input_file(args.input_file)
        log_action(logger, logging.INFO, "RunStarted",
                   BatchID=id_generator.batch_id, File=input_path.name)

        parameters = parse_excel(input_path)

        # §14: Boundary -> Negative -> Pairwise
        merged = (
            generate_boundary_test_cases(parameters)
            + generate_negative_test_cases(parameters)
            + generate_pairwise_test_cases(parameters)
        )

        test_cases = id_generator.assign_ids(merged)
        output_path = write_test_cases(
            test_cases,
            parameter_names=list(parameters.keys()),
            generation_date=id_generator.date_part,
        )

    except InputValidationError as exc:
        print(f"{len(exc.errors)} input error(s) found. {LOG_HINT}")
        return 1

    except Exception as exc:  # any other failure: log it, never crash silently
        log_action(logger, logging.ERROR, "GenerationFailed",
                   Reason=type(exc).__name__, Detail=exc)
        print(f"Generation failed. {LOG_HINT}")
        return 1

    print(f"Generated {len(test_cases)} test cases -> {output_path.name}")
    return 0


def _parse_arguments(argv):
    parser = argparse.ArgumentParser(
        description="Generate boundary, negative and pairwise test cases "
                    "from an insurance product parameter sheet."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to the input .xlsx file. If omitted, the only .xlsx file "
             "in the input/ folder is used.",
    )
    return parser.parse_args(argv)


def _resolve_input_file(input_file):
    """
    §22 input selection:
      - a path was given  -> it must exist
      - no path given     -> exactly one .xlsx file must be in input/
                             (Excel lock files '~$...' are ignored)
    """
    if input_file:
        path = Path(input_file)
        if not path.is_file():
            log_action(logger, logging.ERROR, "ReadExcel",
                       File=path.name, Reason="FileNotFound")
            raise InputFileError(f"Input file not found: {path}")
        return path

    candidates = sorted(
        p for p in config.INPUT_DIR.glob(f"*{config.INPUT_FILE_EXTENSION}")
        if not p.name.startswith(config.EXCEL_LOCK_FILE_PREFIX)
    )
    if len(candidates) != 1:
        log_action(logger, logging.ERROR, "ReadExcel",
                   Folder=config.INPUT_DIR.name, FileCount=len(candidates),
                   Reason="ExpectedExactlyOneInputFile")
        raise InputFileError(
            f"Expected exactly one .xlsx file in {config.INPUT_DIR}, "
            f"found {len(candidates)}"
        )
    return candidates[0]


if __name__ == "__main__":
    sys.exit(main())
