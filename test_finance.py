"""
tests/test_finance.py
Unit tests for pure financial calculation functions.
"""
import pytest
import pandas as pd
from utils.finance import calculate_split, monthly_summary, pending_collections


class TestCalculateSplit:
    def test_equal_split(self):
        result = calculate_split(30000, ["Ahmed", "Sara", "Usman"], "equal")
        assert result == {"Ahmed": 10000.0, "Sara": 10000.0, "Usman": 10000.0}

    def test_percentage_split(self):
        result = calculate_split(10000, ["A", "B"], "percentage", [60, 40])
        assert result["A"] == 6000.0
        assert result["B"] == 4000.0

    def test_percentage_must_sum_100(self):
        with pytest.raises(ValueError):
            calculate_split(10000, ["A", "B"], "percentage", [60, 30])

    def test_custom_split(self):
        result = calculate_split(10000, ["A", "B"], "custom", [7000, 3000])
        assert result["A"] == 7000.0

    def test_empty_participants(self):
        result = calculate_split(5000, [], "equal")
        assert result == {}


class TestMonthlySummary:
    def _make_df(self, amounts, dates):
        return pd.DataFrame({"Amount": amounts, "Date": pd.to_datetime(dates)})

    def test_basic_summary(self):
        rev = self._make_df([100000, 50000], ["2025-05-01", "2025-05-15"])
        exp = self._make_df([30000],         ["2025-05-10"])
        s   = monthly_summary(exp, rev, "2025-05")
        assert s["total_revenue"]  == 150000.0
        assert s["total_expenses"] == 30000.0
        assert s["net_profit"]     == 120000.0
        assert s["profit_margin"]  == 80.0

    def test_empty_data(self):
        s = monthly_summary(pd.DataFrame(), pd.DataFrame(), "2025-05")
        assert s["net_profit"] == 0.0


class TestPendingCollections:
    def test_pending(self):
        students = pd.DataFrame({
            "StudentID":  ["S1", "S2", "S3"],
            "Name":       ["A", "B", "C"],
            "Balance":    [5000, 0, 3000],
            "MonthlyFee": [15000, 12000, 18000],
            "PaidAmount": [10000, 12000, 15000],
        })
        result = pending_collections(students)
        assert result["total"] == 8000
        assert result["count"] == 2

    def test_all_paid(self):
        students = pd.DataFrame({
            "StudentID":  ["S1"],
            "Balance":    [0],
        })
        result = pending_collections(students)
        assert result["total"] == 0
        assert result["count"] == 0
