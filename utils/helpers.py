"""
Shared helpers used by the generators.

SSOT sections: §7 (Executable Test Case Principle), §16 (Execution Status)

A generated test case is a dict:

    {
        "Scenario_Type":    "Boundary",
        "Scenario_Reason":  "Lower Boundary -1",
        "parameters":       {"colour": "red", "age": 17, ...},   # input column order
        "Expected_Result":  "Validation Error",
        "Execution_Status": "Not Executed",
    }

Parameters are kept in their own nested dict, not mixed into the top level.
That way a product parameter that happens to be called "Expected_Result"
or "Batch_ID" can never overwrite a system column.

IDs (§13) are added later, after all test cases are merged in §14 order.
"""

import numbers

from config import config


def default_values(parameters):
    """§7: the default for every parameter is its first value (min for ranges)."""
    return {name: spec["values"][0] for name, spec in parameters.items()}


def build_test_case(parameters, overrides, scenario_type, scenario_reason,
                    expected_result):
    """
    Build one executable test case (§7).

    Every parameter starts at its default value; `overrides` replaces the
    ones under test. Execution_Status is always initialised to
    'Not Executed' (§16).
    """
    values = default_values(parameters)
    values.update(overrides)

    return {
        config.COL_SCENARIO_TYPE: scenario_type,
        config.COL_SCENARIO_REASON: scenario_reason,
        "parameters": values,
        config.COL_EXPECTED_RESULT: expected_result,
        config.COL_EXECUTION_STATUS: config.DEFAULT_EXECUTION_STATUS,
    }


def format_reason(parameter, reason):
    """§8/§9: 'age - Lower Boundary -1'."""
    return config.SCENARIO_REASON_FORMAT.format(parameter=parameter, reason=reason)


def range_parameters(parameters):
    """Yield (name, min, max) for every range parameter, in input order."""
    for name, spec in parameters.items():
        if spec["type"] == config.TYPE_RANGE:
            minimum, maximum = spec["values"]
            yield name, minimum, maximum


def is_number(value):
    """True for int/float values, False for bool, None, strings, etc."""
    return isinstance(value, numbers.Real) and not isinstance(value, bool)
