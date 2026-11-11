"""V5 X20 C-1 (decision 252, LIMITATIONS_V5.md L-C10): per-MW annual inflow of the new-build hydro / ror candidates, one rule for the 11 countries.

    python scripts_project/v5_hydro_unit_inflow_data.py --ember <release_generation_yearly_global.csv> --iha <X03 HYDRO_STOCK_CHECK.csv>

Rule: unit inflow u_c (MWh per MW and year) = national generation / national capacity of the same basis
  * national generation = the national target of the existing stock, research_inputs/hydro_v5/HYDRO_NATIONAL_TARGET_S4C2.csv (median Ember yearly hydro
    generation 2019-2025 x 1.1, the same number the existing stock is normalised to; the existing stock is not changed by this rule);
  * national capacity = median of the Ember yearly hydro capacity (column 'Capacity (GW)', same file and same years as the generation median; years
    without a capacity value are skipped); if Ember has no capacity for a country, IHA 2024 (X03 HYDRO_STOCK_CHECK.csv, rows whose reference starts with
    'IHA 2024'); otherwise no value (a country with new-build candidates and no value stops the build).
CF = u_c / 8760. The Ember file is the decision-74 file (SHA256 checked against the registry rows of s4c_2). Writes
research_inputs/hydro_v5/HYDRO_CANDIDATE_UNIT_INFLOW_V5.csv.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/hydro_v5/HYDRO_CANDIDATE_UNIT_INFLOW_V5.csv"
TARGET = ROOT / "research_inputs/hydro_v5/HYDRO_NATIONAL_TARGET_S4C2.csv"
EMBER_SHA = "b2ac49fa9b27035fedda3c6afb85917bf136de9253bfcbaf09c3410904ec7cd1"
ISO = {"BN": "BRN", "KH": "KHM", "ID": "IDN", "LA": "LAO", "MY": "MYS", "MM": "MMR", "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def build(ember: Path, iha: Path | None) -> pd.DataFrame:
    es = sha256(ember)
    if es != EMBER_SHA:
        raise ValueError(f"Ember file SHA256 {es} differs from the registered decision-74 file {EMBER_SHA}")
    e = pd.read_csv(ember)
    h = e[(e["Electricity source"] == "Hydro") & e["ISO 3 code"].isin(ISO.values())].copy()
    T = pd.read_csv(TARGET, keep_default_na=False).set_index("country")
    I = {}
    if iha is not None and Path(iha).exists():
        x = pd.read_csv(iha, keep_default_na=False).set_index("country")
        I = {c: float(x.at[c, "reference_mw"]) for c in x.index if str(x.at[c, "reference"]).startswith("IHA 2024") and str(x.at[c, "reference_mw"]) != ""}
    rows = []
    for c in sorted(ISO):
        t = T.loc[c]; st = str(t.status)
        years = [int(y) for y in str(t.years).split(",") if y.strip()]
        k = h[(h["ISO 3 code"] == ISO[c]) & h.Year.isin(years)].dropna(subset=["Capacity (GW)"]).sort_values("Year")
        cap = float(k["Capacity (GW)"].median()) if len(k) else np.nan
        src = "Ember median" if np.isfinite(cap) and cap > 0 else ("IHA 2024" if c in I else "")
        cap_mw = cap * 1000.0 if src == "Ember median" else (I.get(c, np.nan) if src == "IHA 2024" else np.nan)
        tgt = float(t.target_mwh) if st == "REGISTERED" else np.nan
        u = tgt / cap_mw if st == "REGISTERED" and np.isfinite(cap_mw) and cap_mw > 0 else np.nan
        status = "REGISTERED" if np.isfinite(u) else ("NO_TARGET" if st != "REGISTERED" else "NO_CAPACITY")
        rows.append(dict(country=c, target_status=st, target_mwh=tgt, generation_median_twh=(float(t.generation_median_twh) if st == "REGISTERED" else np.nan),
                         multiplier=float(t.multiplier), years=",".join(map(str, years)), capacity_mw=cap_mw, capacity_source=src,
                         capacity_years=",".join(str(int(y)) for y in k.Year), capacity_series_gw=";".join(f"{int(y)}:{v:g}" for y, v in zip(k.Year, k["Capacity (GW)"])),
                         iha_2024_mw=I.get(c, np.nan), unit_inflow_mwh_per_mw=u, cf=(u / 8760.0 if np.isfinite(u) else np.nan), status=status,
                         note=("Ember hydro capacity may include pumped storage (INFERENCE); IHA 2024 includes PHS for PH / TH" if c in ("PH", "TH") else ""),
                         ember_sha256=es, target_table_sha256=sha256(TARGET)))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ember", type=Path, required=True); ap.add_argument("--iha", type=Path, default=None); a = ap.parse_args()
    t = build(a.ember, a.iha)
    t.to_csv(OUT, index=False, lineterminator="\n")
    print(t[["country", "status", "target_mwh", "capacity_mw", "capacity_source", "iha_2024_mw", "unit_inflow_mwh_per_mw", "cf"]].to_string())


if __name__ == "__main__":
    main()
