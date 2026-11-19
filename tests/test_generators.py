"""Tests for the three generators - spec §7 to §12."""

import itertools
import logging

import pytest

from config import config
from generators.boundary_generator import generate_boundary_test_cases
from generators.negative_generator import generate_negative_test_cases
from generators.pairwise_generator import (
    generate_pairwise_test_cases,
    get_pairwise_range_values,
)

DEFAULTS = {"colour": "red", "age": 18, "agency name": "online",
            "pt": 7, "smoker status": "smoker"}


def rows_for(cases, parameter):
    """(value, reason, expected) for the cases that test one parameter."""
    return [(c["parameters"][parameter], c["Scenario_Reason"], c["Expected_Result"])
            for c in cases if c["Scenario_Reason"].startswith(f"{parameter} - ")]


# --- Boundary (§8) -----------------------------------------------------------

def test_boundary_values_reasons_and_results(sample_parameters):
    cases = generate_boundary_test_cases(sample_parameters)
    assert rows_for(cases, "age") == [
        (17, "age - Lower Boundary -1", "Validation Error"),
        (18, "age - Lower Boundary", "Policy Creation Success"),
        (19, "age - Lower Boundary +1", "Policy Creation Success"),
        (59, "age - Upper Boundary -1", "Policy Creation Success"),
        (60, "age - Upper Boundary", "Policy Creation Success"),
        (61, "age - Upper Boundary +1", "Validation Error"),
    ]


def test_boundary_only_for_range_parameters(sample_parameters):
    cases = generate_boundary_test_cases(sample_parameters)
    assert len(cases) == 12  # 6 for age + 6 for pt


def test_boundary_other_parameters_stay_at_defaults(sample_parameters):
    first = generate_boundary_test_cases(sample_parameters)[0]
    assert first["parameters"] == {**DEFAULTS, "age": 17}


def test_boundary_narrow_range_removes_duplicates():
    cases = generate_boundary_test_cases({"age": {"type": "range", "values": [18, 19]}})
    assert [(v, r) for v, r, _ in rows_for(cases, "age")] == [
        (17, "age - Lower Boundary -1"),
        (18, "age - Lower Boundary"),
        (19, "age - Lower Boundary +1"),
        (20, "age - Upper Boundary +1"),
    ]


def test_boundary_fixed_range():
    cases = generate_boundary_test_cases({"pt": {"type": "range", "values": [10, 10]}})
    assert [(v, e) for v, _, e in rows_for(cases, "pt")] == [
        (9, "Validation Error"),
        (10, "Policy Creation Success"),
        (11, "Validation Error"),
    ]


# --- Negative (§9) -----------------------------------------------------------

def test_negative_values_reasons_and_results(sample_parameters):
    cases = generate_negative_test_cases(sample_parameters)
    assert rows_for(cases, "age") == [
        (None, "age - Null", "Validation Error"),
        ("", "age - Empty String", "Validation Error"),
        ("ABC", "age - Alphabetic Value", "Validation Error"),
        ("@@@", "age - Special Characters", "Validation Error"),
        (-1, "age - Negative Number", "Validation Error"),
    ]
    assert len(cases) == 10  # 5 for age + 5 for pt


def test_negative_skips_value_inside_valid_range(caplog):
    with caplog.at_level(logging.WARNING):
        cases = generate_negative_test_cases({"temp": {"type": "range", "values": [-5, 5]}})
    assert -1 not in [c["parameters"]["temp"] for c in cases]
    assert len(cases) == 4
    assert "Action=NegativeValueSkipped" in caplog.text


def test_negative_value_without_reason_fails_loudly(monkeypatch):
    monkeypatch.setitem(config.NEGATIVE_TEST_VALUES, "numeric_range", [999])
    with pytest.raises(ValueError, match="No Scenario Reason"):
        generate_negative_test_cases({"age": {"type": "range", "values": [18, 60]}})


# --- Pairwise (§10 - §12) ----------------------------------------------------

@pytest.mark.parametrize("low, high, expected", [
    (18, 60, [18, 19, 39, 59, 60]),
    (18, 20, [18, 19, 20]),
    (10, 10, [10]),
])
def test_pairwise_range_values(low, high, expected):
    assert get_pairwise_range_values(low, high) == expected


def test_pairwise_covers_every_pair(sample_parameters):
    cases = generate_pairwise_test_cases(sample_parameters)
    values = {"colour": ["red", "orange", "blue"], "age": [18, 19, 39, 59, 60],
              "agency name": ["online", "offline", "broker"], "pt": [7, 8, 11, 14, 15],
              "smoker status": ["smoker", "non smoker"]}
    rows = [c["parameters"] for c in cases]
    for a, b in itertools.combinations(values, 2):
        for x in values[a]:
            for y in values[b]:
                assert any(r[a] == x and r[b] == y for r in rows), f"{a}={x}, {b}={y}"


def test_pairwise_rows_are_valid_and_expect_success(sample_parameters):
    for case in generate_pairwise_test_cases(sample_parameters):
        assert 18 <= case["parameters"]["age"] <= 60
        assert 7 <= case["parameters"]["pt"] <= 15
        assert case["Scenario_Reason"] == "Pairwise Combination"
        assert case["Expected_Result"] == "Policy Creation Success"


def test_pairwise_is_same_every_run(sample_parameters):
    assert generate_pairwise_test_cases(sample_parameters) == \
           generate_pairwise_test_cases(sample_parameters)


def test_pairwise_single_value_list():
    cases = generate_pairwise_test_cases({
        "gender": {"type": "list", "values": ["Male"]},
        "age": {"type": "range", "values": [18, 60]},
    })
    assert sorted(c["parameters"]["age"] for c in cases) == [18, 19, 39, 59, 60]
    assert all(c["parameters"]["gender"] == "Male" for c in cases)


def test_pairwise_all_single_values_gives_one_row():
    cases = generate_pairwise_test_cases({
        "gender": {"type": "list", "values": ["Male"]},
        "pt": {"type": "range", "values": [10, 10]},
    })
    assert [c["parameters"] for c in cases] == [{"gender": "Male", "pt": 10}]


def test_pairwise_single_parameter_fallback(caplog):
    with caplog.at_level(logging.INFO):
        cases = generate_pairwise_test_cases({"age": {"type": "range", "values": [18, 60]}})
    assert [c["parameters"]["age"] for c in cases] == [18, 19, 39, 59, 60]
    assert "Action=PairwiseSkipped" in caplog.text


# --- Shared rules ------------------------------------------------------------

@pytest.mark.parametrize("generate", [
    generate_boundary_test_cases,
    generate_negative_test_cases,
    generate_pairwise_test_cases,
])
def test_every_case_starts_not_executed(sample_parameters, generate):
    assert all(c["Execution_Status"] == "Not Executed"
               for c in generate(sample_parameters))
