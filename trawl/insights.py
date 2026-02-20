"""
trawl/insights.py — Pandas queries over cn_combined.csv.

Public API:
    load()                          → load + cache the dataset
    match_categories(keywords)      → find matching Category values
    spend_by_agency(categories)     → top agencies by spend
    top_suppliers(categories)       → top winning suppliers
    expiring_contracts(categories)  → contracts ending within 6 months
    category_summary(categories)    → combined dict for LLM context
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache

import pandas as pd

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cn_combined.csv")


@lru_cache(maxsize=1)
def load() -> pd.DataFrame:
    """Load cn_combined.csv once and cache in-process."""
    df = pd.read_csv(_DATA_PATH, low_memory=False, parse_dates=["End Date", "Publish Date"])
    # Ensure Value is numeric
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df


def match_categories(keywords: list[str], df: pd.DataFrame | None = None) -> list[str]:
    """
    Return Category values from the dataset that contain any of the keywords
    (case-insensitive substring match).

    Example:
        match_categories(["cyber", "security", "cloud"])
        → ["Computer services", "Information technology consultation services", ...]
    """
    if df is None:
        df = load()

    cats = df["Category"].dropna().unique()
    kw_lower = [k.lower() for k in keywords]

    matched = [
        cat for cat in cats
        if any(kw in cat.lower() for kw in kw_lower)
    ]
    return sorted(matched)


def _filter(df: pd.DataFrame, categories: list[str]) -> pd.DataFrame:
    """Return rows whose Category is in the given list."""
    return df[df["Category"].isin(categories)]


def spend_by_agency(
    categories: list[str],
    top_n: int = 8,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Total spend per agency for the given categories, sorted descending.

    Returns DataFrame with columns: Agency, total_value, contract_count
    """
    if df is None:
        df = load()

    subset = _filter(df, categories)
    if subset.empty:
        return pd.DataFrame(columns=["Agency", "total_value", "contract_count"])

    result = (
        subset.groupby("Agency")
        .agg(total_value=("Value", "sum"), contract_count=("CN ID", "count"))
        .reset_index()
        .sort_values("total_value", ascending=False)
        .head(top_n)
    )
    return result


def top_suppliers(
    categories: list[str],
    agency: str | None = None,
    top_n: int = 5,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Top suppliers by total contract value for the given categories.
    Optionally filter to a specific agency.

    Returns DataFrame with columns: Supplier Name, total_value, contract_count
    """
    if df is None:
        df = load()

    subset = _filter(df, categories)
    if agency:
        subset = subset[subset["Agency"].str.contains(agency, case=False, na=False)]
    if subset.empty:
        return pd.DataFrame(columns=["Supplier Name", "total_value", "contract_count"])

    result = (
        subset.groupby("Supplier Name")
        .agg(total_value=("Value", "sum"), contract_count=("CN ID", "count"))
        .reset_index()
        .sort_values("total_value", ascending=False)
        .head(top_n)
    )
    return result


def expiring_contracts(
    categories: list[str],
    months: int = 6,
    df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Contracts in the given categories whose End Date falls within `months` from today.
    Sorted by End Date ascending (soonest first).

    Returns DataFrame with columns: CN ID, Agency, Supplier Name, Value, End Date, Category, Description
    """
    if df is None:
        df = load()

    subset = _filter(df, categories)
    now = pd.Timestamp.now()
    cutoff = now + pd.DateOffset(months=months)

    expiring = subset[
        (subset["End Date"] >= now) & (subset["End Date"] <= cutoff)
    ].copy()

    expiring = expiring.sort_values("End Date")
    return expiring[
        ["CN ID", "Agency", "Supplier Name", "Value", "End Date", "Category", "Description"]
    ]


def category_summary(categories: list[str], df: pd.DataFrame | None = None) -> dict:
    """
    Return a single dict with all the key insight numbers for the given categories.
    This is what gets passed to the LLM to generate the 💰 section.

    Keys:
        matched_categories      list of category strings used
        total_spend             float — total historical spend
        contract_count          int
        top_agencies            list of dicts {agency, total_value, contract_count}
        top_suppliers           list of dicts {supplier, total_value, contract_count}
        expiring_count          int — contracts expiring within 6 months
        expiring_value          float — $ value of expiring contracts
        expiring_sample         list of dicts (up to 5 soonest)
    """
    if df is None:
        df = load()

    subset = _filter(df, categories)

    if subset.empty:
        return {
            "matched_categories": categories,
            "total_spend": 0,
            "contract_count": 0,
            "top_agencies": [],
            "top_suppliers": [],
            "expiring_count": 0,
            "expiring_value": 0,
            "expiring_sample": [],
        }

    agencies_df = spend_by_agency(categories, top_n=5, df=df)
    suppliers_df = top_suppliers(categories, top_n=5, df=df)
    expiring_df = expiring_contracts(categories, months=6, df=df)

    return {
        "matched_categories": categories,
        "total_spend": float(subset["Value"].sum()),
        "contract_count": len(subset),
        "top_agencies": agencies_df.to_dict(orient="records"),
        "top_suppliers": suppliers_df.to_dict(orient="records"),
        "expiring_count": len(expiring_df),
        "expiring_value": float(expiring_df["Value"].sum()),
        "expiring_sample": expiring_df.head(5).to_dict(orient="records"),
    }
