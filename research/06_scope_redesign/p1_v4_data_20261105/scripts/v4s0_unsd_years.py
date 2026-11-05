"""V4 S0 section 3.3: which UNSD years are already on disk (pypsa-asean UNdata export, 2025-05-02) for the ASEAN industry-branch transactions.

    python scripts/v4s0_unsd_years.py --unsd <pypsa-asean/data/demand/unsd/data> --transactions <pypsa-asean/data/unsd_transactions.csv> --out <work dir>/evidence

Counts commodity rows per country, year and industry branch (the transactions build_base_industry_totals.py keeps). No unit conversion. Read-only.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ASEAN = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao People's Dem. Rep.": "LA", "Malaysia": "MY", "Myanmar": "MM", "Philippines": "PH",
         "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--unsd", type=Path, required=True); ap.add_argument("--transactions", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    tr = pd.read_csv(a.transactions, sep=";"); keep = dict(zip(tr.Transaction.str.strip().str.lower(), tr.clean_name))
    df = pd.concat((pd.read_csv(f, sep=";", dtype=str) for f in sorted(a.unsd.glob("*.txt"))), ignore_index=True)
    df = df[df["Country or Area"].isin(ASEAN)]
    sp = df["Commodity - Transaction"].str.split(" - ", n=1, expand=True)
    df["commodity"], df["transaction"] = sp[0].str.strip(), sp[1].fillna("").str.strip().str.lower()
    df = df[df.transaction.isin(keep)]
    df["branch"] = df.transaction.map(keep); df["iso"] = df["Country or Area"].map(ASEAN)
    df = df[df.Year.isin(["2019", "2020", "2021", "2022", "2023"])]
    df["q"] = pd.to_numeric(df.Quantity, errors="coerce")
    t = df[df.q > 0].groupby(["iso", "Year"]).agg(rows=("q", "size"), branches=("branch", "nunique"), commodities=("commodity", "nunique")).unstack("Year")
    t.to_csv(a.out / "UNSD_YEARS_ON_DISK_ASEAN.csv")
    print(t.to_string())


if __name__ == "__main__":
    main()
