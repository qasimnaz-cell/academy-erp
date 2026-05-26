"""
utils/finance.py
Core financial calculation helpers — pure functions, no I/O.
"""
import pandas as pd
from datetime import datetime
from typing import Literal


# ── Summary KPIs ──────────────────────────────────────────────────────────

def monthly_summary(expenses: pd.DataFrame, revenue: pd.DataFrame, month: str) -> dict:
    """
    Return a dict of KPIs for a given month (YYYY-MM).
    """
    def _filter(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "Date" not in df.columns:
            return df
        dates = pd.to_datetime(df["Date"], errors="coerce")
        return df[dates.dt.to_period("M").astype(str) == month]

    exp_m = _filter(expenses)
    rev_m = _filter(revenue)

    total_revenue  = float(rev_m["Amount"].sum()) if not rev_m.empty else 0.0
    total_expenses = float(exp_m["Amount"].sum()) if not exp_m.empty else 0.0
    net_profit     = total_revenue - total_expenses
    margin         = (net_profit / total_revenue * 100) if total_revenue else 0.0

    return {
        "month":          month,
        "total_revenue":  total_revenue,
        "total_expenses": total_expenses,
        "net_profit":     net_profit,
        "profit_margin":  round(margin, 2),
    }


def pending_collections(students: pd.DataFrame) -> dict:
    """Return total pending and list of overdue students."""
    if students.empty:
        return {"total": 0, "count": 0, "students": []}

    overdue = students[students["Balance"] > 0].copy()
    return {
        "total":    float(overdue["Balance"].sum()),
        "count":    len(overdue),
        "students": overdue.to_dict("records"),
    }


def revenue_breakdown(revenue: pd.DataFrame) -> pd.DataFrame:
    """Group revenue by Source with totals and percentages."""
    if revenue.empty:
        return pd.DataFrame()
    grp = revenue.groupby("Source")["Amount"].sum().reset_index()
    grp["Percentage"] = (grp["Amount"] / grp["Amount"].sum() * 100).round(1)
    return grp.sort_values("Amount", ascending=False)


def expense_breakdown(expenses: pd.DataFrame) -> pd.DataFrame:
    """Group expenses by Category."""
    if expenses.empty:
        return pd.DataFrame()
    grp = expenses.groupby("Category")["Amount"].sum().reset_index()
    grp["Percentage"] = (grp["Amount"] / grp["Amount"].sum() * 100).round(1)
    return grp.sort_values("Amount", ascending=False)


# ── Cash Flow ─────────────────────────────────────────────────────────────

def monthly_cashflow(expenses: pd.DataFrame, revenue: pd.DataFrame, months: int = 6) -> pd.DataFrame:
    """
    Return a DataFrame with columns [Month, Revenue, Expenses, NetProfit]
    for the last `months` months.
    """
    period_range = pd.period_range(end=datetime.today(), periods=months, freq="M")
    rows = []
    for period in period_range:
        m = str(period)
        s = monthly_summary(expenses, revenue, m)
        rows.append({
            "Month":      period.strftime("%b %Y"),
            "Revenue":    s["total_revenue"],
            "Expenses":   s["total_expenses"],
            "NetProfit":  s["net_profit"],
        })
    return pd.DataFrame(rows)


# ── Split Expense Calculator ──────────────────────────────────────────────

SplitType = Literal["equal", "percentage", "custom"]


def calculate_split(
    total: float,
    participants: list[str],
    split_type: SplitType,
    shares: list[float] | None = None,
) -> dict[str, float]:
    """
    Returns dict mapping participant → amount owed.
    - equal: each pays total / n
    - percentage: shares must sum to 100
    - custom: shares are absolute amounts, must sum to total
    """
    n = len(participants)
    if n == 0:
        return {}

    if split_type == "equal":
        each = round(total / n, 2)
        return {p: each for p in participants}

    if split_type == "percentage":
        if not shares or len(shares) != n:
            raise ValueError("Percentage split requires one share per participant")
        if abs(sum(shares) - 100) > 0.01:
            raise ValueError("Percentages must sum to 100")
        return {p: round(total * s / 100, 2) for p, s in zip(participants, shares)}

    if split_type == "custom":
        if not shares or len(shares) != n:
            raise ValueError("Custom split requires one amount per participant")
        if abs(sum(shares) - total) > 0.50:
            raise ValueError("Custom amounts must sum to total")
        return {p: round(s, 2) for p, s in zip(participants, shares)}

    raise ValueError(f"Unknown split type: {split_type}")


def net_balances(splits_df: pd.DataFrame) -> dict[str, float]:
    """
    Calculate running net balance for each participant across all unsettled splits.
    Positive = owed money. Negative = owes money.
    """
    import json
    balances: dict[str, float] = {}

    for _, row in splits_df.iterrows():
        if row.get("Status") == "settled":
            continue
        try:
            participants = json.loads(row["Participants"])
            shares       = json.loads(row["Shares"])
            paid_by      = row["PaidBy"]
        except Exception:
            continue

        for person, amount in zip(participants, shares):
            balances[person] = balances.get(person, 0.0) - amount

        # Payer gets credited the full amount
        balances[paid_by] = balances.get(paid_by, 0.0) + float(row["TotalAmount"])

    return {k: round(v, 2) for k, v in balances.items()}


# ── Forecasting (simple linear trend) ─────────────────────────────────────

def forecast_next_month(cashflow: pd.DataFrame, column: str = "Revenue") -> float:
    """Simple linear regression forecast for next period."""
    if cashflow.empty or column not in cashflow.columns:
        return 0.0
    import numpy as np
    y = cashflow[column].values
    x = list(range(len(y)))
    if len(y) < 2:
        return float(y[-1]) if len(y) else 0.0
    coeffs = np.polyfit(x, y, 1)
    return round(float(np.polyval(coeffs, len(y))), 2)
