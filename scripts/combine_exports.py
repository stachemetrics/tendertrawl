"""
combine_exports.py — Concatenate AusTender Contract Notice Export files.

Each .xlsx has metadata in rows 1-2, header at row 3 (pandas header=2).
Outputs a single cleaned CSV to data/cn_combined.csv.

Usage:
    python scripts/combine_exports.py
"""

import glob
import os
import sys

import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cn_combined.csv")


def load_single(path: str) -> pd.DataFrame:
    """Load one xlsx export. Header is at row 3 (0-indexed: header=2)."""
    try:
        df = pd.read_excel(path, header=2, engine="openpyxl")
        df = df.dropna(how="all")
        print(f"  ✓ {os.path.basename(path)}: {len(df):,} rows, {len(df.columns)} cols")
        return df
    except Exception as e:
        print(f"  ✗ {os.path.basename(path)}: FAILED — {e}")
        return pd.DataFrame()


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and deduplicate the combined dataframe."""
    # --- Dedup by CN ID (keep latest amendment if dupes) ---
    if "CN ID" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["CN ID"], keep="last")
        dupes = before - len(df)
        print(f"\n  Deduped: {before:,} → {len(df):,} rows ({dupes:,} duplicates removed)")

    # --- Parse Value: strip $, commas, whitespace → float ---
    if "Value" in df.columns:
        df["Value"] = (
            df["Value"]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    # --- Parse date columns (Australian format: day first) ---
    date_cols = ["Publish Date", "Start Date", "End Date", "Amendment Publish Date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # --- Strip whitespace from string columns ---
    str_cols = df.select_dtypes(include=["object", "str"]).columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    return df


def summarise(df: pd.DataFrame) -> None:
    """Print a summary of the combined dataset."""
    print("\n" + "=" * 60)
    print("📊 DATASET SUMMARY")
    print("=" * 60)
    print(f"  Total rows:          {len(df):,}")
    print(f"  Columns:             {len(df.columns)}")

    if "Publish Date" in df.columns:
        print(f"  Date range:          {df['Publish Date'].min()} → {df['Publish Date'].max()}")

    if "Value" in df.columns:
        print(f"  Total value:         ${df['Value'].sum():,.0f}")
        print(f"  Mean contract:       ${df['Value'].mean():,.0f}")
        print(f"  Median contract:     ${df['Value'].median():,.0f}")

    if "Agency" in df.columns:
        print(f"  Unique agencies:     {df['Agency'].nunique()}")
        print(f"  Top 5 by spend:")
        top = df.groupby("Agency")["Value"].sum().nlargest(5)
        for agency, val in top.items():
            print(f"    ${val:>14,.0f}  {agency}")

    if "Category" in df.columns:
        print(f"  Unique categories:   {df['Category'].nunique()}")

    if "Supplier Name" in df.columns:
        print(f"  Unique suppliers:    {df['Supplier Name'].nunique()}")

    if "End Date" in df.columns:
        now = pd.Timestamp.now()
        six_months = now + pd.DateOffset(months=6)
        expiring = df[(df["End Date"] >= now) & (df["End Date"] <= six_months)]
        print(f"  Expiring <6 months:  {len(expiring):,} contracts (${expiring['Value'].sum():,.0f})")

    if "Procurement Method" in df.columns:
        print(f"\n  Procurement methods:")
        for method, count in df["Procurement Method"].value_counts().items():
            pct = count / len(df) * 100
            print(f"    {count:>6,} ({pct:4.1f}%)  {method}")

    print("=" * 60)


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.xlsx")))
    print(f"🐟 Found {len(files)} xlsx files in {RAW_DIR}\n")

    if not files:
        print("No files found! Check that data/raw/ contains .xlsx exports.")
        sys.exit(1)

    # --- Load all files ---
    frames = []
    for f in files:
        result = load_single(f)
        if not result.empty:
            frames.append(result)

    if not frames:
        print("No data loaded from any file!")
        sys.exit(1)

    # --- Check column consistency ---
    base_cols = set(frames[0].columns)
    for i, frame in enumerate(frames[1:], start=1):
        if set(frame.columns) != base_cols:
            diff = set(frame.columns).symmetric_difference(base_cols)
            print(f"\n  ⚠️  File {i+1} has different columns: {diff}")

    # --- Combine and clean ---
    combined = pd.concat(frames, ignore_index=True)
    print(f"\n  Combined: {len(combined):,} total rows from {len(frames)} files")

    combined = clean(combined)

    # --- Save ---
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    combined.to_csv(OUT_PATH, index=False)
    print(f"\n  💾 Saved to {OUT_PATH}")

    # --- Summary ---
    summarise(combined)

    # --- Column list for reference ---
    print(f"\n  Columns: {list(combined.columns)}")


if __name__ == "__main__":
    main()