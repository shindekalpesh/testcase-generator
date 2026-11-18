"""
Pairwise Test Case Generator.

SSOT sections: §7, §10, §11, §12

Steps:
    1. Build the value list for every parameter (input order):
         list  -> its values
         range -> representative values (§11), always inside [min, max]
    2. Single-value lists are doubled for AllPairs only (§12):
         ["Male"] -> ["Male", "Male"]
    3. One parameter only -> no AllPairs; one test case per value (§10).
    4. Otherwise run AllPairs and turn each row into a test case.

Implementation notes:
    - AllPairs is given plain lists, not a dict. The dict form builds a
      namedtuple from the parameter names, which fails for names with
      spaces such as "agency name".
    - Exact duplicate rows are removed (first occurrence kept). They only
      appear when every parameter has a single value, a side effect of the
      §12 doubling. Removing them loses no pair coverage.
"""

import logging

from allpairspy import AllPairs

from config import config
from utils.helpers import build_test_case
from utils.logger import log_action

logger = logging.getLogger(__name__)


def generate_pairwise_test_cases(parameters):
    """Return the list of pairwise test cases (all valid combinations)."""
    names = list(parameters.keys())
    value_lists = [_pairwise_values(parameters[name]) for name in names]

    if len(names) == 1:
        rows = [[value] for value in value_lists[0]]
        log_action(logger, logging.INFO, "PairwiseSkipped",
                   Reason="SingleParameter", TestCaseCount=len(rows))
    else:
        allpairs_input = [
            values * 2 if len(values) == 1 else values  # §12
            for values in value_lists
        ]
        rows = _remove_duplicate_rows(list(row) for row in AllPairs(allpairs_input))

    test_cases = [
        build_test_case(
            parameters,
            overrides=dict(zip(names, row)),
            scenario_type=config.SCENARIO_TYPE_PAIRWISE,
            scenario_reason=config.PAIRWISE_SCENARIO_REASON,
            expected_result=config.EXPECTED_SUCCESS,
        )
        for row in rows
    ]

    log_action(logger, logging.INFO, "PairwiseGenerationCompleted",
               TestCaseCount=len(test_cases))
    return test_cases


def get_pairwise_range_values(min_val, max_val):
    """§11: representative values, filtered to stay inside [min, max]."""
    values = [
        min_val,
        min_val + 1,
        (min_val + max_val) // 2,
        max_val - 1,
        max_val,
    ]
    return sorted(v for v in set(values) if min_val <= v <= max_val)


def _pairwise_values(spec):
    if spec["type"] == config.TYPE_RANGE:
        minimum, maximum = spec["values"]
        return get_pairwise_range_values(minimum, maximum)
    return list(spec["values"])


def _remove_duplicate_rows(rows):
    seen = set()
    unique = []
    for row in rows:
        key = tuple(row)
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique
