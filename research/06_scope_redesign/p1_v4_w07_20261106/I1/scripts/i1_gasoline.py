"""I1-4: ID household motor gasoline (W12 F6) against HEESI 2025; the same check for MM; 2050 effect from the scratch chain runs.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_gasoline.py

A. UNSD 2019 motor gasoline by transaction for ID and MM: model capsule (UNdata export 2025-05-02) and SDMX current database (W12 responses).
B. HEESI 2025 (Handbook of Energy & Economic Statistics of Indonesia 2025; text layer extracted by W11, work/p1_v4_ncv_20261106/extracted/
   heesi2025): 2019 row of table 5.4.1 Transportation (original unit, kilolitre; gasoline RON 88 / 92 / 95+98+100 / 90) and table 5.4.2 (energy
   unit, thousand BOE); table 5.2.1 Household carries no gasoline column (traditional biomass, gas, kerosene, LPG, biogas, electricity);
   table 5.3.1 Commercial gasoline 2019 'n.a.'. Values transcribed from the page text below (VERIFIED against the extracted page, grade B).
C. Tonnes from kilolitres with a density range 0.72 / 0.74 / 0.76 t per m3 (INFERENCE: typical motor-gasoline density, HEESI prints no density).
D. 2050: tables/I1_CHAIN_RESULTS.csv case GASmove (ID and MM household gasoline moved to RoadResidualFuel on the current base) under the growth
   readings I, IIa (RAS), IIb (frozen anchors), IId (fixed v3 RAS column factors); land-transport fuel, EV electricity (x 0.30215), residential fuel.
Writes ID_GASOLINE_CHECK.csv, tables/I1_4_*.csv, evidence/I1_4_gasoline.json.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402

HEESI = cm.W11 / "extracted" / "heesi2025"
HEESI_PDF = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/01_industry/content-handbook-of-energy-and-economic-statistics-of-indonesia-2025.pdf")
BOE_GJ = 3.6 / 0.6130          # HEESI BOE (W11 section 2.2: 1 MWh = 0.6130 BOE)
DENS = (0.72, 0.74, 0.76)


def heesi_2019() -> dict:
    t1 = (HEESI / "p076.txt").read_text(encoding="utf-8", errors="replace")
    t2 = (HEESI / "p078.txt").read_text(encoding="utf-8", errors="replace")
    t3 = (HEESI / "p066.txt").read_text(encoding="utf-8", errors="replace")
    row = lambda t: [x.replace(",", "") for x in re.search(r"^\s*2019\s+(.*)$", t, re.M).group(1).split()]
    r1, r2 = row(t1), row(t2)
    # 5.4.1 columns: Gas(MMSCF) Avgas Avtur RON88 RON92 RON95+ RON90 GasoilCN51 GasoilCN53 Kerosene GasoilCN48 MDF FuelOil BioGasoil Total Electricity(GWh)
    # the 2019 row prints 16 numbers in that order (CN51 / CN53 present from 2016)
    k1 = ["gas_mmscf", "avgas", "avtur", "ron88", "ron92", "ron95plus", "ron90", "gasoil_cn51", "gasoil_cn53", "kerosene", "gasoil_cn48", "mdf", "fuel_oil", "bio_gasoil", "total_oil_kl", "electricity_gwh"]
    k2 = ["gas", "avgas", "avtur", "ron88", "ron92", "ron95plus", "ron90", "gasoil_cn51", "gasoil_cn53", "kerosene", "gasoil_cn48", "mdf", "fuel_oil", "bio_gasoil", "total_oil", "electricity", "total"]
    if len(r1) != len(k1) or len(r2) != len(k2):
        raise SystemExit(f"STOP: HEESI 2019 row layout changed: {r1} / {r2}")
    a, b = dict(zip(k1, map(float, r1))), dict(zip(k2, map(float, r2)))
    hh = (HEESI / "p066_plain.txt").read_text(encoding="utf-8", errors="replace")
    return dict(kl=a, kboe=b, household_header_has_gasoline=("asoline" in t3), household_header=re.sub(r"\s+", " ", t3[:600]))


def unsd(ev: cm.Evidence) -> pd.DataFrame:
    cap0 = pd.DataFrame(__import__("json").loads((cm.SRC / "UNSD_2019_SOURCE_CAPSULE.json").read_text())["records"])
    capS = pd.read_csv(cm.BASE_OUT / "SDMX_2019_CAPSULE_RECORDS.csv", dtype=str)
    rows = []
    for src, d in (("UNdata export 2025-05-02 (model capsule)", cap0), ("UNSD SDMX current (W12 2026-11-05)", capS)):
        g = d[d.Country.isin(["ID", "MM"]) & d.Commodity.str.lower().eq("motor gasoline")]
        for r in g.itertuples():
            rows.append(dict(source=src, country=r.Country, transaction=r.Transaction, quantity_kt=float(r.Quantity), unit=r.Unit,
                             twh_frozen_factor=float(r.Quantity) * 0.0123, footnote=getattr(r, "_6", "") if False else ""))
    U = pd.DataFrame(rows)
    cm.write_csv(U.to_dict("records"), cm.TABLES / "I1_4_UNSD_MOTOR_GASOLINE_2019.csv")
    for r in U[U.transaction.str.lower().str.contains("household|road|final energy")].itertuples():
        ev.add(f"unsd.{r.country}.{r.source[:6]}.{r.transaction}", r.quantity_kt, "kt (2019)", "VERIFIED", "A", r.source, "Motor Gasoline")
    return U


def main():
    ev = cm.Evidence("I1_4_gasoline")
    H = heesi_2019()
    U = unsd(ev)
    kl = H["kl"]; kb = H["kboe"]
    gas_kl = kl["ron88"] + kl["ron92"] + kl["ron95plus"] + kl["ron90"]
    gas_kboe = kb["ron88"] + kb["ron92"] + kb["ron95plus"] + kb["ron90"]
    ev.add("heesi2025.t541.2019.gasoline_transport_kl", gas_kl, "kL", "VERIFIED", "B", f"HEESI 2025 table 5.4.1 (PDF {HEESI_PDF.name}, page text p076, printed p.60)",
           f"RON88 {kl['ron88']:.0f} + RON92 {kl['ron92']:.0f} + RON95+ {kl['ron95plus']:.0f} + RON90 {kl['ron90']:.0f}")
    ev.add("heesi2025.t542.2019.gasoline_transport_kboe", gas_kboe, "thousand BOE", "VERIFIED", "B", "HEESI 2025 table 5.4.2 (page text p078)", "")
    ev.add("heesi2025.t521.household_has_gasoline_column", H["household_header_has_gasoline"], "bool", "VERIFIED", "B", "HEESI 2025 table 5.2.1 (page text p066)", H["household_header"][:300])
    uid = U[(U.country == "ID")]
    def q(src, pat):
        x = uid[uid.source.str.startswith(src) & uid.transaction.str.lower().str.contains(pat)]
        return float(x.quantity_kt.max()) if len(x) else 0.0
    rows = []
    for src, lab in (("UNdata", "UNdata export (model)"), ("UNSD SDMX", "SDMX current")):
        hh, road, fec = q(src, "household"), q(src, r"\broad\b|in road|by road"), q(src, "final energy")
        rows.append(dict(item=f"UNSD {lab}: ID motor gasoline households 2019", value=hh, unit="kt", status="VERIFIED", grade="A"))
        rows.append(dict(item=f"UNSD {lab}: ID motor gasoline road 2019", value=road, unit="kt", status="VERIFIED", grade="A"))
        rows.append(dict(item=f"UNSD {lab}: ID motor gasoline final energy consumption 2019", value=fec, unit="kt", status="VERIFIED", grade="A"))
        rows.append(dict(item=f"UNSD {lab}: households share of road + households", value=hh / (hh + road) if hh + road else None, unit="ratio", status="EXACT", grade="A"))
    rows.append(dict(item="HEESI 2025 t.5.4.1: ID transport gasoline 2019 (RON 88+92+95+90)", value=gas_kl, unit="kL", status="VERIFIED", grade="B"))
    rows.append(dict(item="HEESI 2025 t.5.4.2: ID transport gasoline 2019", value=gas_kboe, unit="thousand BOE", status="VERIFIED", grade="B"))
    rows.append(dict(item="HEESI 2025 t.5.4.2: ID transport gasoline 2019 in TWh (BOE = 3.6/0.6130 GJ)", value=gas_kboe * 1e3 * BOE_GJ / 3.6e6, unit="TWh", status="EXACT", grade="B"))
    rows.append(dict(item="HEESI 2025 t.5.2.1: household sector has a gasoline column", value=H["household_header_has_gasoline"], unit="bool", status="VERIFIED", grade="B"))
    rows.append(dict(item="HEESI 2025 t.5.3.1: commercial sector gasoline 2019", value="n.a. (2025 only: 2 / 289 / 35 kL)", unit="kL", status="VERIFIED", grade="B"))
    for d in DENS:
        t = gas_kl * d / 1e3
        rows.append(dict(item=f"HEESI transport gasoline 2019 at {d} t/m3", value=t, unit="kt", status="INFERENCE", grade="C"))
    hh_e, road_e = q("UNdata", "household"), q("UNdata", r"\broad\b|in road|by road")
    for d in DENS:
        t = gas_kl * d / 1e3
        rows.append(dict(item=f"(UNSD export road + households) / HEESI transport tonnes at {d} t/m3", value=(hh_e + road_e) / t, unit="ratio", status="INFERENCE", grade="C"))
        rows.append(dict(item=f"UNSD export road / HEESI transport tonnes at {d} t/m3", value=road_e / t, unit="ratio", status="INFERENCE", grade="C"))
    # MM
    um = U[U.country == "MM"]
    for r in um.itertuples():
        rows.append(dict(item=f"UNSD {r.source[:30]}: MM motor gasoline {r.transaction}", value=r.quantity_kt, unit="kt", status="VERIFIED", grade="A"))
    rows.append(dict(item="MM national energy balance (MOEE) with gasoline by sector", value="not on this machine (MISSING_DATA)", unit="", status="VERIFIED", grade="E"))
    # 2050 from the chain
    R = pd.read_csv(cm.TABLES / "I1_CHAIN_RESULTS.csv")
    g = R[(R.case == "GASmove") & R.country.isin(["ID", "MM", "TH", "MY", "VN", "PH", "SG", "ASEAN11"])]
    for r in g.itertuples():
        for col, lab in (("d_land_vs_mode_S0_twh", "land-transport fuel"), ("d_ev_vs_mode_S0_twh", "EV electricity (x 0.30215)"), ("d_resf_vs_mode_S0_twh", "residential fuel"),
                         ("dT_v2_vs_mode_S0_twh", "T_v2"), ("d_Transport_vs_mode_S0_twh", "transport sector total")):
            rows.append(dict(item=f"2050 {lab}: {r.country}, reading {r.mode}", value=getattr(r, col), unit="TWh (2050)", status="EXACT", grade="C"))
            ev.add(f"chain.GASmove.{r.mode}.{r.country}.{col}", getattr(r, col), "TWh (2050)", "EXACT", "C", "tables/I1_CHAIN_RESULTS.csv case GASmove", lab)
    cm.write_csv(rows, cm.I1 / "ID_GASOLINE_CHECK.csv", ["item", "value", "unit", "status", "grade"])
    for r in rows[:30]:
        if r["status"] in ("VERIFIED", "EXACT", "INFERENCE") and isinstance(r["value"], (int, float)):
            ev.add("check." + re.sub(r"[^A-Za-z0-9]+", "_", r["item"])[:80], r["value"], r["unit"], r["status"], r["grade"], "ID_GASOLINE_CHECK.csv", r["item"])
    p = ev.write()
    pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 110); pd.set_option("display.max_rows", 200)
    print(U.to_string())
    print(pd.DataFrame(rows).to_string())
    print(kl, kb)
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
