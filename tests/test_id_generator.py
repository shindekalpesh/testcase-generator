"""Tests for utils/id_generator.py - spec §13."""

from datetime import datetime

from utils.id_generator import IdGenerator

FIXED_TIME = datetime(2026, 11, 18, 16, 40, 57)


def test_batch_id_and_date_part():
    ids = IdGenerator(FIXED_TIME)
    assert ids.batch_id == "BAT_20261118_164057"
    assert ids.date_part == "20261118"


def test_ids_follow_order_and_share_one_timestamp():
    result = IdGenerator(FIXED_TIME).assign_ids([{"n": 1}, {"n": 2}, {"n": 3}])
    assert [r["Policy_ID"] for r in result] == [
        "POL_20261118_164057_000001",
        "POL_20261118_164057_000002",
        "POL_20261118_164057_000003",
    ]
    assert result[2]["TestCase_ID"] == "TC_20261118_164057_000003"
    assert {r["Batch_ID"] for r in result} == {"BAT_20261118_164057"}


def test_ids_come_first_and_original_data_is_kept():
    result = IdGenerator(FIXED_TIME).assign_ids([{"Scenario_Type": "Boundary"}])
    assert list(result[0]) == ["Batch_ID", "Policy_ID", "TestCase_ID", "Scenario_Type"]


def test_input_list_is_not_modified():
    original = [{"Scenario_Type": "Boundary"}]
    IdGenerator(FIXED_TIME).assign_ids(original)
    assert original == [{"Scenario_Type": "Boundary"}]
