import pytest
import pytest_check as check
from datetime import datetime as dt, timedelta as td
from calendar_logic import Day

@pytest.mark.parametrize(
    "issue_date, resolve_date, expected_result",
    [(dt(2021, 1, 1, 10), dt(2021, 1, 1, 10), td(seconds=0)), (dt(2021, 3, 2, 19, 50), dt(2021, 3, 6, 19, 20), td(seconds=0))],
)
def test_calculation(issue_date, resolve_date, expected_result):
    issue_day = Day(issue_date, is_issue_day=True)
    resolve_day = Day(resolve_date, is_issue_day=False)
    check.equal(resolve_day - issue_day, expected_result)
