"""
Negative Test Case Generator.

SSOT sections: §7, §9

For each range parameter (input order), generate one test case per value in
NEGATIVE_TEST_VALUES["numeric_range"]. Expected Result is always
'Validation Error'.

Valid-range safeguard (§9): a numeric negative value that falls inside
[min, max] is a valid input, not a negative test. It is skipped with a
WARNING. Example: range -5..5 skips -1.

List parameters get no negative tests in the MVP (§2, §23).
"""

import logging

from config import config
from utils.helpers import (
    build_test_case,
    format_reason,
    is_number,
    range_parameters,
)
from utils.logger import log_action

logger = logging.getLogger(__name__)


def generate_negative_test_cases(parameters):
    """Return the list of negative test cases for all range parameters."""
    negative_values = config.NEGATIVE_TEST_VALUES["numeric_range"]
    test_cases = []

    for name, minimum, maximum in range_parameters(parameters):
        for value in negative_values:
            if is_number(value) and minimum <= value <= maximum:
                log_action(logger, logging.WARNING, "NegativeValueSkipped",
                           Parameter=name, Value=value,
                           Reason="WithinValidRange")
                continue

            test_cases.append(
                build_test_case(
                    parameters,
                    overrides={name: value},
                    scenario_type=config.SCENARIO_TYPE_NEGATIVE,
                    scenario_reason=format_reason(name, _reason_for(value)),
                    expected_result=config.EXPECTED_VALIDATION_ERROR,
                )
            )

    log_action(logger, logging.INFO, "NegativeGenerationCompleted",
               TestCaseCount=len(test_cases))
    return test_cases


def _reason_for(value):
    """
    Look up the §9 Scenario Reason for a negative value.

    Matches on type AND value, so that -1 never matches -1.0 or True, and
    None never matches "". A value added to NEGATIVE_TEST_VALUES without a
    reason is a configuration mistake, so it fails loudly.
    """
    for configured_value, reason in config.NEGATIVE_SCENARIO_REASONS:
        if type(configured_value) is type(value) and configured_value == value:
            return reason
    raise ValueError(
        f"No Scenario Reason configured for negative value {value!r}. "
        f"Add it to NEGATIVE_SCENARIO_REASONS in config/config.py."
    )
