"""I1-2c: what base AEO8 rests on - AEO8 country TFEC (Table C.8 per capita x Table D.1 population) against the national statistics
(ID: HEESI 2025) and against our UNSD base, 2019 and 2022.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_aeo8.py

A. AEO8 C.8 2022 historical TFEC per capita (printed 'ktoe / 1000 persons' = kgoe per person) x D.1 population 2022 for the 10 AEO8 countries
   (research_inputs/demand_v5/sources/AEO8_2050_BY_COUNTRY.csv, transcribed from AEO8 PDF p.189-190).
B. HEESI 2025 table 3.2.1 (final energy consumption by sector incl. traditional biomass, thousand BOE) and 3.2.2 (excluded) for 2019 and 2022,
   table 5.1.1 / 5.1.2 industry coal and biomass (W11 text extraction p042, p044, p060, p062); BOE = 3.6 / 0.6130 GJ.
C. Our base (D1 table, energy-use sectors) for ID 2019: S0 (UNdata export) and S4 (SDMX), from BASE2019_SDMX/BASE2019_SDMX_D1_ROWS.csv.
Writes tables/I1_2_AEO8_BASE_CHECK.csv, evidence/I1_2_aeo8.json.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402

HEESI = cm.W11 / "extracted" / "heesi2025"
GWH_PER_KBOE = 1e3 * (3.6 / 0.6130) / 3600.0      # thousand BOE -> GWh (1 BOE = 5.8728 GJ)
NAMES = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao PDR": "LA", "Malaysia": "MY", "Myanmar": "MM", "Philippines": "PH",
         "Singapore": "SG", "Thailand": "TH", "Vietnam": "VN"}


def heesi_rows(page: str, label: str) -> dict:
    t = (HEESI / f"{page}.txt").read_text(encoding="utf-8", errors="replace")
    years = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
    m = re.search(rf"^\s*{label}\s+(.*)$", t, re.M)
    vals = [float(x.replace(",", "")) for x in m.group(1).split()]
    return dict(zip(years, vals[-11:]))


def main():
    ev = cm.Evidence("I1_2_aeo8")
    a = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/AEO8_2050_BY_COUNTRY.csv", dtype=str)   # d1_common.SRC_DIR
    num = lambda v: float(str(v).replace(",", ""))
    rows = []
    for name, c in NAMES.items():
        d = a[a.country == name]
        pc = d[(d.indicator == "Final energy per capita (TFEC/Pop)") & (d.year == "2022") & (d.scenario == "historical")].value_as_printed
        pop = d[(d.indicator == "Population") & (d.year == "2022")].value_as_printed
        if len(pc) and len(pop):
            tfec22 = num(pc.iloc[0]) * num(pop.iloc[0]) * 1e3 * 11.63 / 1e6     # kgoe/person x million persons -> ktoe; x 11.63 MWh/toe -> TWh
            rows.append(dict(country=c, item="AEO8 C.8 x D.1 TFEC 2022", value_twh=tfec22, source="AEO8 PDF p.189-190 (AEO8_2050_BY_COUNTRY.csv)", status="EXACT", grade="B"))
    W = pd.read_csv(cm.BASE_OUT / "BASE2019_SDMX_D1_ROWS.csv")
    W = W[W.sector.isin(["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]) & (W.account != "TransportEmbeddedFuelParent")]
    for c in NAMES.values():
        for s in ("S0", "S4"):
            rows.append(dict(country=c, item=f"UNSD 2019 energy-use TFEC, our base {s}", value_twh=float(W[W.country == c][s].sum()) / 1e6,
                             source="BASE2019_SDMX_D1_ROWS.csv", status="EXACT", grade="A"))
    # HEESI (ID)
    inc = {lab: heesi_rows("p042", lab) for lab in ("Industrial", "Households", "Commercial", "Transportation", "Other")}
    exc = {lab: heesi_rows("p044", lab) for lab in ("Industrial", "Households", "Commercial", "Transportation", "Other")}
    for y in ("2019", "2022"):
        tot_inc = sum(v[y] for v in inc.values()); tot_exc = sum(v[y] for v in exc.values())
        rows.append(dict(country="ID", item=f"HEESI 2025 t.3.2.1 final energy {y} incl. traditional biomass", value_twh=tot_inc * GWH_PER_KBOE / 1e3, source="HEESI 2025 p.26 (text p042)", status="VERIFIED", grade="B"))
        rows.append(dict(country="ID", item=f"HEESI 2025 t.3.2.2 final energy {y} excl. traditional biomass", value_twh=tot_exc * GWH_PER_KBOE / 1e3, source="HEESI 2025 p.28 (text p044)", status="VERIFIED", grade="B"))
        for lab in inc:
            rows.append(dict(country="ID", item=f"HEESI 2025 t.3.2.1 {lab} {y}", value_twh=inc[lab][y] * GWH_PER_KBOE / 1e3, source="HEESI 2025 p.26", status="VERIFIED", grade="B"))
    for s_ in ("Industry", "Residential", "Transport", "Commercial", "AgricultureOthers"):
        for s in ("S0", "S4"):
            rows.append(dict(country="ID", item=f"UNSD 2019 {s_}, our base {s}", value_twh=float(W[(W.country == "ID") & (W.sector == s_)][s].sum()) / 1e6, source="BASE2019_SDMX_D1_ROWS.csv", status="EXACT", grade="A"))
    T = pd.DataFrame(rows)
    # ratios
    id22 = float(T[(T.country == "ID") & (T.item == "AEO8 C.8 x D.1 TFEC 2022")].value_twh.iloc[0])
    for lab in ("incl.", "excl."):
        h22 = float(T[(T.country == "ID") & T.item.str.contains(f"final energy 2022 {lab}")].value_twh.iloc[0])
        T = pd.concat([T, pd.DataFrame([dict(country="ID", item=f"AEO8 ID TFEC 2022 / HEESI final energy 2022 {lab} traditional biomass", value_twh=id22 / h22, source="ratio", status="EXACT", grade="B")])])
    cm.write_csv(T.to_dict("records"), cm.TABLES / "I1_2_AEO8_BASE_CHECK.csv")
    for r in T.itertuples():
        ev.add(f"{r.country}.{re.sub(r'[^A-Za-z0-9]+', '_', r.item)[:70]}", r.value_twh, "TWh or ratio", r.status, r.grade, r.source, "")
    p = ev.write()
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
    print(T.round(3).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
