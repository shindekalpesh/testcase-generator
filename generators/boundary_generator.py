"""
Boundary Test Case Generator.

SSOT sections: §7, §8

For each range parameter (input order), generate:

    min - 1   Lower Boundary -1
    min       Lower Boundary
    min + 1   Lower Boundary +1
    max - 1   Upper Boundary -1
    max       Upper Boundary
    max + 1   Upper Boundary +1

Narrow ranges produce repeated values (e.g. 18-19). Duplicates are removed
by value, keeping the FIRST occurrence and its reason (§8).

Expected Result depends only on the value (§8):
    min <= value <= max  ->  Policy Creation Success
    otherwise            ->  Validation Error
"""

import logging

from config import config
from utils.helpers import build_test_case, format_reason, range_parameters
from utils.logger import log_action

logger = logging.getLogger(__name__)


def generate_boundary_test_cases(parameters):
    """Return the list of boundary test cases for all range parameters."""
    test_cases = []

    for name, minimum, maximum in range_parameters(parameters):
        for value, reason in _boundary_values(name, minimum, maximum):
            test_cases.append(
                build_test_case(
                    parameters,
                    overrides={name: value},
                    scenario_type=config.SCENARIO_TYPE_BOUNDARY,
                    scenario_reason=format_reason(name, reason),
                    expected_result=_expected_result(value, minimum, maximum),
                )
            )

    log_action(logger, logging.INFO, "BoundaryGenerationCompleted",
               TestCaseCount=len(test_cases))
    return test_cases


def _boundary_values(name, minimum, maximum):
    """Return [(value, reason), ...] in §8 order, duplicates removed by value."""
    candidates = [
        (minimum - 1, config.REASON_LOWER_MINUS_1),
        (minimum, config.REASON_LOWER),
        (minimum + 1, config.REASON_LOWER_PLUS_1),
        (maximum - 1, config.REASON_UPPER_MINUS_1),
        (maximum, config.REASON_UPPER),
        (maximum + 1, config.REASON_UPPER_PLUS_1),
    ]

    seen = set()
    unique = []
    for value, reason in candidates:
        if value not in seen:
            seen.add(value)
            unique.append((value, reason))

    removed = len(candidates) - len(unique)
    if removed:
        log_action(logger, logging.INFO, "BoundaryDuplicatesRemoved",
                   Parameter=name, RemovedCount=removed)

    return unique


def _expected_result(value, minimum, maximum):
    if minimum <= value <= maximum:
        return config.EXPECTED_SUCCESS
    return config.EXPECTED_VALIDATION_ERROR
