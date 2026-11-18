"""
Traceability ID Generator.

SSOT section: §13

One IdGenerator is created per run, at the start of the run. Its timestamp
is captured once and reused for every ID, so all IDs in a run share it:

    Batch_ID    = BAT_20261118_164057
    Policy_ID   = POL_20261118_164057_000001
    TestCase_ID = TC_20261118_164057_000001

The counter starts at 000001 every run and follows output order (§14),
so IDs must be assigned AFTER the three generators' results are merged.
"""

from datetime import datetime

from config import config


class IdGenerator:

    def __init__(self, run_timestamp=None):
        self.run_timestamp = run_timestamp or datetime.now()
        self.date_part = self.run_timestamp.strftime(config.ID_DATE_FORMAT)
        time_part = self.run_timestamp.strftime(config.ID_TIME_FORMAT)

        self._stamp = f"{self.date_part}_{time_part}"
        self.batch_id = f"{config.BATCH_ID_PREFIX}_{self._stamp}"

    def assign_ids(self, test_cases):
        """
        Return new test case dicts with Batch_ID, Policy_ID and TestCase_ID
        added at the front. The input list is not modified.
        """
        result = []
        for number, test_case in enumerate(test_cases, start=1):
            counter = f"{number:0{config.ID_COUNTER_WIDTH}d}"
            result.append({
                config.COL_BATCH_ID: self.batch_id,
                config.COL_POLICY_ID: f"{config.POLICY_ID_PREFIX}_{self._stamp}_{counter}",
                config.COL_TESTCASE_ID: f"{config.TESTCASE_ID_PREFIX}_{self._stamp}_{counter}",
                **test_case,
            })
        return result
