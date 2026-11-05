"""V4 W11 section 2: reference conversion factors per country and the four factor schemes (a) v3, (b) UNSD country, (c) national handbook,
(d) IPCC by coal rank.

    python scripts/v4ncv_references.py --work <work dir>

Every published number is read from the page text in extracted/ (v4ncv_pdf_text.py) and asserted against the value used here; the APEC 2022
table (PDF p.197) has no text layer: its values were transcribed from the page image (extracted/apec_img/, v4ncv_apec_image.py) and are marked
TRANSCRIBED. UNSD 2019 country values come from v4ncv_unsd_implied.py (ncv/UNSD_IMPLIED_COAL_NCV_2019.csv). GEM GIPT coal ranks (operating
coal units by 'Fuel (combustion only)') are the physical evidence for the rank judgement of scheme (d).
Outputs: ncv/NCV_REFERENCE_VALUES.csv (one row per published value), ncv/NCV_FACTOR_SCHEMES.csv (country x commodity x scheme -> GJ per unit),
ncv/GIPT_COAL_RANK_CAPACITY.csv, ncv/_references_evidence.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402

REFS = []


def ref(source, pdf_page, printed, table, item, unit, value, gj, country="", year="", status="VERIFIED", grade="B", note=""):
    REFS.append(dict(source=source, pdf_page=pdf_page, printed_page=printed, table=table, item=item, unit=unit, value=value, gj_per_unit=gj,
                     country=country, year=year, status=status, grade=grade, note=note))
    return gj


def text(work, key, page, plain=False):
    return (work / "extracted" / key / f"p{page:03d}{'_plain' if plain else ''}.txt").read_text(encoding="utf-8")


def find_num(txt: str, label: str, expect: float, tol=1e-9) -> float:
    """First number after `label` on its line; assert it equals `expect`."""
    for ln in txt.splitlines():
        mm = re.search(re.escape(label) + r"(?![A-Za-z])", ln)
        if mm:
            m = re.findall(r"(?<![\d.])(\d+\.\d+|\d+)(?![\d.])", ln[mm.end():])
            if m:
                v = float(m[0].replace(",", "").replace(" ", ""))
                if abs(v - expect) > tol * max(1, abs(expect)):
                    raise ValueError(f"{label}: read {v}, expected {expect}")
                return v
    raise ValueError(f"{label} not found")


def ipcc_triple(txt: str, label: str, expect: tuple) -> None:
    """IPCC Table 1.2 line: label [footnote] value lower upper (the triple may wrap to the next line); assert all three."""
    lines = txt.splitlines()
    for i, ln in enumerate(lines):
        m = re.search(re.escape(label) + r"(?!\s*[A-Za-z])", ln)
        if m:
            nums = re.findall(r"\d+\.\d+|\d+", ln[m.end():])
            j = i + 1
            while len(nums) < 3 and j < len(lines):
                nums += re.findall(r"\d+\.\d+|\d+", lines[j]); j += 1
            got = tuple(float(x) for x in nums[-3:]) if len(nums) <= 4 else tuple(float(x) for x in nums[-3:])
            if any(abs(g - e) > 1e-9 for g, e in zip(got, expect)):
                raise ValueError(f"IPCC {label}: read {got}, expected {expect}")
            return
    raise ValueError(f"IPCC {label} not found")


def references(work: Path) -> dict:
    R = {}
    # IPCC 2006 Vol. 2 Ch. 1 Table 1.2 (p.18-19)
    t18, t19 = text(work, "ipcc2006_v2c1", 18), text(work, "ipcc2006_v2c1", 19)
    for k, (v, lo, hi) in cm.IPCC.items():
        src = t18 if k not in ("Wood/Wood Waste", "Sulphite lyes (black liquor)", "Other Primary Solid Biomass", "Charcoal", "Biogasoline", "Biodiesels",
                               "Other Liquid Biofuels") else t19
        ipcc_triple(src, k, (v, lo, hi))
        ref("IPCC 2006 Vol.2 Ch.1 Table 1.2", 18 if src is t18 else 19, "1.18" if src is t18 else "1.19", "Default NCV (TJ/Gg) with 95 % limits", k, "TJ/Gg", v, v,
            note=f"lower {lo}, upper {hi}")
    R["ipcc"] = cm.IPCC
    # UNSD standard NCV (2019 edition p.27-28; 2014 edition 05.pdf p.2-3 identical)
    s27 = text(work, "un_eb2019", 27)
    for lab, key in (("Hard coal", "Hard coal"), ("Brown coal ", "Brown coal"), ("Coal coke", "Coal coke"), ("Patent fuel", "Patent fuel"),
                     ("Brown coal briquettes", "Brown coal briquettes"), ("Gas-diesel oil", "Gas-diesel oil"), ("Fuel oil", "Fuel oil"),
                     ("Liquefied petroleum gas", "Liquefied petroleum gas"), ("Motor gasoline", "Motor gasoline"), ("Bagasse", "Bagasse"),
                     ("Natural gas (original unit is TJ on a GCV basis)", "Natural gas (GCV TJ -> NCV TJ)")):
        find_num(s27, lab, cm.UNSD_STD[key])
        ref("UNSD Energy Balances 2019, Standard NCV", 27, "xxvi", "Standard net calorific values", key, "TJ per kt (gas: NCV/GCV)", cm.UNSD_STD[key], cm.UNSD_STD[key])
    # UNSD 2014 edition, country-specific NCVs (05.pdf = repository UNSD_NCV.pdf): ASEAN entries, 2014 column
    u14 = {("ID", "Hard coal", "production"): (4, 25.8), ("MY", "Hard coal", "production"): (4, 26.4), ("VN", "Hard coal", "production"): (4, 23.4),
           ("ID", "Brown coal", "production"): (5, 20.9), ("PH", "Brown coal", "production"): (5, 22.1), ("TH", "Brown coal", "production"): (5, 10.7),
           ("ID", "Hard coal", "imports"): (8, 28.2), ("MY", "Hard coal", "imports"): (8, 26.4), ("TH", "Hard coal", "imports"): (9, 26.4),
           ("VN", "Hard coal", "imports"): (9, 23.4), ("KH", "Brown coal", "imports"): (9, 19.9), ("PH", "Brown coal", "imports"): (10, 22.1),
           ("SG", "Brown coal", "imports"): (10, 9.7)}
    name = {"ID": "Indonesia", "MY": "Malaysia", "VN": "Viet Nam", "PH": "Philippines", "TH": "Thailand", "KH": "Cambodia", "SG": "Singapore"}
    for (cc, com, flow), (pg, v) in u14.items():
        tx = text(work, "unsd_ncv_05", pg, plain=True)
        line = next(ln for ln in tx.splitlines() if ln.strip().startswith(name[cc]))
        nums = re.findall(r"\d+\.\d", line.replace("1 8.6", "18.6"))
        if abs(float(nums[-1]) - v) > 1e-9:
            raise ValueError((cc, com, flow, nums, v))
        ref("UNSD Energy Balances 2014 (05.pdf), country NCVs", pg, "", f"{com} - {flow}", f"{com} {flow}", "GJ/t", v, v, cc, 2014, grade="B",
            note="2013 / 2014 columns; 2014 used")
    R["unsd2014"] = {f"{k[0]}|{k[1]}|{k[2]}": v[1] for k, v in u14.items()}
    # HEESI 2019 Annex (p.106-107, printed 128-129): BOE per original unit; BOE size from 'Electric Power 0.6130 BOE/MWh'
    h106, h107 = text(work, "heesi2019", 106), text(work, "heesi2019", 107)
    boe = 3.6 / find_num(h107, "Electric Power", 0.6130)
    ref("HEESI 2019 Conversion Factor", 107, "129", "Multiplier factor to BOE", "Electric Power", "BOE/MWh", 0.6130, 3.6 / 0.6130, "ID", 2019,
        note="BOE = 3.6 / 0.6130 = 5.8728 GJ")
    heesi = {}
    for lab, v in (("Kalimantan Coal", 4.2000), ("Imported Coal", 4.2766), ("Anthracite", 4.9893), ("Ombilin Coal", 4.8452), ("Tanjung Enim Coal", 3.7778),
                   ("Lignite", 3.0649), ("Briquette", 3.5638), ("Charcoal", 4.9713), ("Firewood", 2.2979)):
        find_num(h106, lab, v)
        heesi[lab] = ref("HEESI 2019 Conversion Factor", 106, "128", "Multiplier factor to BOE (source: Neraca Energi 1990-1994)", lab, "BOE/t", v, v * boe, "ID", 2019)
    R["heesi2019"] = heesi
    # Malaysia NEB 2019 (p.80): TJ / 1000 t, NCV basis (p.78)
    m80 = text(work, "my_neb2019", 80)
    neb = {}
    for lab, v in (("Hard coal", 29.3076), ("Coke/oven coke", 26.3768), ("Charcoal", 28.8888), ("Gas Oil/Diesel", 42.4960), ("Residual Fuel Oil", 41.4996),
                   ("Liquefied Petroleum Gas (LPG)", 45.5440), ("Petrol", 43.9614), ("Kerosene", 43.1994), ("Aviation Turbine Fuel (ATF)", 43.1994),
                   ("Naphtha", 44.1289), ("Lubricants", 42.1401), ("Bitumen (Asphalt)", 41.8000), ("Petroleum Coke", 36.4000), ("Petroleum Waxes", 43.3334),
                   ("Aviation Gasoline (AV GAS)", 43.9614)):
        find_num(m80, lab, v)
        neb[lab] = ref("Malaysia National Energy Balance 2019", 80, "80", "Conversion coefficients and equivalence (TJ/1000 t; NCV basis, p.78)", lab, "TJ/kt", v, v, "MY", 2019)
    assert "Assuming 9.7 TJ/1000 cu m" in m80
    neb["Fuelwood (m3)"] = ref("Malaysia National Energy Balance 2019", 80, "80", "note 2", "Fuelwood", "TJ per 10^3 m3", 9.7, 9.7, "MY", 2019)
    R["neb2019"] = neb
    # Thailand EPPO Energy Statistics 2021 (B.E. 2564), conversion factors (NCV) p.226-227 (printed 224-225), MJ per unit
    e226, e227 = text(work, "th_eppo2564", 226), text(work, "th_eppo2564", 227)
    eppo = {}
    for tx, pg, pr, lab, v in ((e226, 226, "224", "COAL IMPORT (kg.)", 26.37), (e226, 226, "224", "COKE (kg.)", 27.63), (e226, 226, "224", "ANTHRACITE (kg.)", 31.40),
                               (e227, 227, "225", "MAE MOH (kg.)", 10.47), (e227, 227, "225", "LI (kg.)", 18.42), (e227, 227, "225", "KRABI  (kg.)", 10.88),
                               (e227, 227, "225", "CHAE KHON (kg.)", 15.11), (e227, 227, "225", "FUEL WOOD (kg.)", 15.99), (e227, 227, "225", "CHARCOAL (kg.)", 28.88),
                               (e227, 227, "225", "BAGASSE (kg.)", 7.53), (e227, 227, "225", "PADDY HUSK (kg.)", 14.40)):
        line = next(ln for ln in tx.splitlines() if lab in ln)
        nums = [float(x) for x in re.findall(r"\d+\.\d+|\d+", line.split(lab)[0])]
        if abs(nums[-3] - v) > 1e-9:   # columns: kcal, toe/10^6, MJ, 10^3 Btu, then the item number of the English label
            raise ValueError((lab, nums, v))
        eppo[lab] = ref("EPPO Energy Statistics of Thailand 2021 (B.E. 2564)", pg, pr, "Energy content of fuel (net calorific value), source DEDE annual report",
                        lab, "MJ/kg", v, v, "TH", 2021, note="report year 2021; factors stated without year (applied to 2019: INFERENCE)")
    assert "600" in e227 and "cu.m. of solid wood" in e227
    eppo["fuelwood_m3"] = ref("EPPO Energy Statistics of Thailand 2021 (B.E. 2564)", 227, "225", "General", "1 m3 solid wood = 600 kg", "kg/m3", 600, 15.99 * 0.6,
                              "TH", 2021, note="fuelwood 15.99 MJ/kg x 0.600 t/m3 = 9.594 GJ/m3")
    R["eppo2564"] = eppo
    # APEC Energy Statistics 2022, 'Average net calorific values of energy products for 2022' (PDF p.197, printed 183), kJ/kg: image only
    apec = {("BN", "Sub-bituminous coal"): 22666, ("ID", "Anthracite"): 30525, ("ID", "Other bituminous coal"): 20096, ("ID", "Lignite"): 18751,
            ("ID", "Peat"): 15572, ("ID", "BKB/PB"): 21803, ("MY", "Other bituminous coal"): 26394, ("MY", "Coke oven coke"): 26377,
            ("PH", "Sub-bituminous coal"): 22098, ("SG", "Other bituminous coal"): 25800, ("TH", "Anthracite"): 31400, ("TH", "Coking coal"): 27630,
            ("TH", "Lignite"): 13720, ("VN", "Anthracite"): 21695, ("ID", "Fuel wood and wood waste"): 14059, ("PH", "Fuel wood and wood waste"): 13777,
            ("TH", "Fuel wood and wood waste"): 15990, ("PH", "Bagasse"): 17816, ("TH", "Bagasse"): 7530, ("ID", "Charcoal"): 30414, ("MY", "Charcoal"): 28889,
            ("PH", "Charcoal"): 25105, ("TH", "Charcoal"): 28880, ("VN", "Charcoal"): 30800, ("ID", "Gas/diesel oil"): 47687, ("ID", "Fuel oil"): 47321,
            ("MY", "Gas/diesel oil"): 42496, ("PH", "Gas/diesel oil"): 42072, ("TH", "Gas/diesel oil"): 42858, ("VN", "Gas/diesel oil"): 42676}
    for (cc, item), v in apec.items():
        ref("APEC Energy Statistics 2022 (May 2025)", 197, "183", "Average net calorific values of energy products for 2022", item, "kJ/kg", v, v / 1000, cc, 2022,
            status="TRANSCRIBED", grade="C", note="table is an image (no text layer); read from the page image; 2022 values; note: some economies report in energy units, NCV back-calculated")
    R["apec2022"] = {f"{k[0]}|{k[1]}": v / 1000 for k, v in apec.items()}
    # ADB 2016 Myanmar energy assessment: rank statement
    adb = "".join(text(work, "mm_adb2016", p, plain=True) for p in range(1, 34))
    assert "generally low-quality lignite and subbituminous" in adb.replace("\n", " ")
    ref("ADB 2016 Myanmar Energy Sector Assessment", "", "", "text", "coal rank", "-", "lignite and sub-bituminous", None, "MM", 2016, grade="C")
    return R


def gipt_ranks() -> pd.DataFrame:
    g = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", dtype=str, low_memory=False)
    c = g[g["Fuel (combustion only)"].fillna("").str.contains("coal", case=False) & g.Status.str.lower().eq("operating")].copy()
    c["mw"] = pd.to_numeric(c["Capacity (MW)"], errors="coerce")
    c["rank"] = c["Fuel (combustion only)"].str.extract(r"coal: ([a-z\- ]+)", expand=False).str.strip()
    t = c.pivot_table(index="Country/area", columns="rank", values="mw", aggfunc="sum").fillna(0.0)
    known = t.drop(columns=["unknown"], errors="ignore").sum(axis=1)
    for col in [x for x in t.columns if x != "unknown"]:
        t[f"share_known_{col}"] = t[col] / known.replace(0, np.nan)
    return t.reset_index()


def la_solve() -> dict:
    """LA: lignite (brown coal) and anthracite (hard coal) NCVs from the visualisation export (later vintage) and the 2025 UNdata export:
    production (lignite 15,263.562 + anthracite 161.494 kt), manufacturing (160 + 147.576), other consumers (250 + 0); least squares."""
    v = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/UNSD_EB_2019_LA.csv", dtype=str)
    tr = v.columns[1]
    def tj(label):
        z = v[v[tr].str.strip() == label]["Primary Coal and Peat"].iloc[0]
        return float(str(z).strip().lstrip("*"))
    fec, mfg, prod = tj("Final Energy Consumption"), tj("Manufacturing  const. and mining"), tj("Primary production")
    other = fec - mfg
    A = np.array([[15263.562, 161.494], [160.0, 147.576], [250.0, 0.0]])
    b = np.array([prod, mfg, other])
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    res = A @ x - b
    return dict(lignite_gj_t=float(x[0]), anthracite_gj_t=float(x[1]), tj_production=prod, tj_manufacturing=mfg, tj_other=other,
                residual_pct=[float(r_ / b_ * 100) for r_, b_ in zip(res, b)])


# ---------------------------------------------------------------- schemes ----------------------------------------------------------------
def schemes(R: dict, S: pd.DataFrame, la: dict, conv: dict) -> pd.DataFrame:
    """Factor per country x commodity (GJ per t, fuelwood GJ per m3) for (a)-(d). Only commodities whose factor differs from v3 in some scheme
    are listed explicitly; everything else keeps the v3 factor (listed once as 'v3 elsewhere')."""
    up = {k: v * 3600 for k, v in conv.items()}   # GJ/t (TWh/kt x 3600)
    imp = S[S.status.str.startswith("VERIFIED")].set_index(["country", "commodity"]).implied_gj_per_t
    rows = []

    def add(cc, com, scheme, gj, source, status, grade, basis):
        rows.append(dict(country=cc, commodity=com, scheme=scheme, gj_per_unit=gj, v3_gj_per_unit=up.get(com, np.nan),
                         change_vs_v3_pct=(gj / up[com] - 1) * 100 if com in up and up[com] else np.nan, source=source, status=status, grade=grade, basis=basis))

    u14 = R["unsd2014"]; h = R["heesi2019"]; n = R["neb2019"]; e = R["eppo2564"]; ap = R["apec2022"]; ip = R["ipcc"]
    for cc in cm.ISO:
        for com in ("Hard coal", "Brown coal", "Lignite", "Sub-bituminous coal", "Other bituminous coal", "Anthracite"):
            add(cc, com, "a", up[com], "pypsa-asean get_conv_factors (frozen)", "EXACT", "B", "v3: one value for all countries and years")
    # (b) UNSD country values
    for (cc, com), v in imp.items():
        if com in ("Hard coal", "Brown coal"):
            add(cc, com, "b", float(v), "UN Energy Balances 2019 TJ / UNdata 2025 kt (v4ncv_unsd_implied.py)", "VERIFIED", "B",
                ">= 2 flows with different quantities agree within 0.5 %")
    p_my, i_my = 3459.18, 29655.4   # MY 2019 production / imports kt (export); factors from the 2019 publication single flows
    f_p, f_i = 73052.0 / p_my, 872184.0 / i_my
    add("MY", "Hard coal", "b", (p_my * f_p + i_my * f_i) / (p_my + i_my), "UNSD method: production / imports weighted (2019 publication single flows)", "INFERENCE", "C",
        f"production {f_p:.3f}, imports {f_i:.3f} GJ/t; consumption flows not derivable (vintage)")
    p_th, i_th = 14078.0, 13393.0
    f_pth = 147875.0 / p_th
    add("TH", "Brown coal", "b", (p_th * f_pth + i_th * cm.UNSD_STD["Brown coal"]) / (p_th + i_th), "UNSD method: 2019 production factor; imports standard (no TH entry in 2014 list)",
        "INFERENCE", "C", f"production (lignite) {f_pth:.3f} GJ/t; imports 14.0; consumption flows not derivable")
    add("TH", "Hard coal", "b", u14["TH|Hard coal|imports"], "UNSD 2014 country list (imports)", "INFERENCE", "C", "TH has no hard-coal production; 2019 not derivable")
    add("LA", "Brown coal", "b", la["lignite_gj_t"], "UNSD visualisation export (later vintage) / UNdata kt, 3 flows least squares", "INFERENCE", "B",
        f"residuals {['%.2f' % r for r in la['residual_pct']]} %")
    add("LA", "Hard coal", "b", la["anthracite_gj_t"], "same solve", "INFERENCE", "B", "anthracite (LA hard coal = anthracite)")
    # (c) national handbook (2019-applicable) / APEC 2022 national submission proxy
    add("ID", "Hard coal", "c", h["Kalimantan Coal"], "HEESI 2019 Annex: Kalimantan coal 4.2000 BOE/t x 5.8728 GJ/BOE", "VERIFIED", "B", "factor HEESI applies before 2023 (HEESI 2025 note 1)")
    add("ID", "Brown coal briquettes", "c", h["Briquette"], "HEESI 2019: Briquette 3.5638 BOE/t", "VERIFIED", "B", "")
    add("ID", "Charcoal", "c", h["Charcoal"], "HEESI 2019: Charcoal 4.9713 BOE/t", "VERIFIED", "B", "")
    add("MY", "Hard coal", "c", n["Hard coal"], "Malaysia NEB 2019: hard coal 29.3076 TJ/kt (= 1 tce)", "VERIFIED", "B", "NCV basis per NEB p.78; value equals the tce convention")
    add("MY", "Coke-oven coke", "c", n["Coke/oven coke"], "Malaysia NEB 2019", "VERIFIED", "B", "")
    add("MY", "Charcoal", "c", n["Charcoal"], "Malaysia NEB 2019", "VERIFIED", "B", "")
    add("MY", "Fuelwood", "c", n["Fuelwood (m3)"], "Malaysia NEB 2019 note 2: 9.7 TJ per 1000 m3", "VERIFIED", "B", "")
    for com, lab in (("Gas Oil/ Diesel Oil", "Gas Oil/Diesel"), ("Fuel oil", "Residual Fuel Oil"), ("Liquefied petroleum gas (LPG)", "Liquefied Petroleum Gas (LPG)"),
                     ("Liquified Petroleum Gas (LPG)", "Liquefied Petroleum Gas (LPG)"), ("Motor Gasoline", "Petrol"), ("Kerosene-type Jet Fuel", "Aviation Turbine Fuel (ATF)"),
                     ("Naphtha", "Naphtha"), ("Lubricants", "Lubricants"), ("Bitumen", "Bitumen (Asphalt)"), ("Petroleum coke", "Petroleum Coke"),
                     ("Paraffin waxes", "Petroleum Waxes"), ("Aviation gasoline", "Aviation Gasoline (AV GAS)")):
        add("MY", com, "c", n[lab], f"Malaysia NEB 2019: {lab}", "VERIFIED", "B", "")
    add("TH", "Lignite", "c", e["MAE MOH (kg.)"], "EPPO 2564: Mae Moh lignite 10.47 MJ/kg", "INFERENCE", "B", "mine of TH industrial lignite unknown: Mae Moh (largest) used; range 10.47 (Mae Moh) - 18.42 (Li)")
    add("TH", "Sub-bituminous coal", "c", e["COAL IMPORT (kg.)"], "EPPO 2564: imported coal 26.37 MJ/kg", "INFERENCE", "B", "EPPO has one value for all imported coal; applied to sub-bituminous imports")
    add("TH", "Other bituminous coal", "c", e["COAL IMPORT (kg.)"], "EPPO 2564: imported coal 26.37 MJ/kg", "VERIFIED", "B", "")
    add("TH", "Anthracite", "c", e["ANTHRACITE (kg.)"], "EPPO 2564: anthracite 31.40 MJ/kg", "VERIFIED", "B", "")
    add("TH", "Coke-oven coke", "c", e["COKE (kg.)"], "EPPO 2564: coke 27.63 MJ/kg", "VERIFIED", "B", "")
    add("TH", "Fuelwood", "c", e["fuelwood_m3"], "EPPO 2564: fuel wood 15.99 MJ/kg x 600 kg per m3 solid wood", "VERIFIED", "B", "")
    add("TH", "Charcoal", "c", e["CHARCOAL (kg.)"], "EPPO 2564: charcoal 28.88 MJ/kg", "VERIFIED", "B", "")
    add("TH", "Bagasse", "c", e["BAGASSE (kg.)"], "EPPO 2564: bagasse 7.53 MJ/kg", "VERIFIED", "B", "")
    add("PH", "Brown coal", "c", ap["PH|Sub-bituminous coal"], "APEC 2022 table (PH sub-bituminous 22,098 kJ/kg); no PH handbook on disk", "TRANSCRIBED", "C", "2022 value as 2019 proxy")
    add("VN", "Hard coal", "c", ap["VN|Anthracite"], "APEC 2022 table (VN anthracite 21,695 kJ/kg); no VN handbook on disk", "TRANSCRIBED", "C", "2022 value as 2019 proxy")
    add("SG", "Hard coal", "c", ap["SG|Other bituminous coal"], "APEC 2022 table (SG other bituminous 25,800 kJ/kg)", "TRANSCRIBED", "C", "")
    # (d) IPCC 2006 by rank (rank judgement per country; reported children used where UNSD gives them)
    add("ID", "Hard coal", "d", ip["Sub-Bituminous Coal"][0], "IPCC T1.2 sub-bituminous 18.9", "INFERENCE", "C",
        "rank: GIPT operating coal units with known rank 84 % sub-bituminous; APEC 2022 ID 20.10 MJ/kg; HEESI average coal 3.4554 BOE = 20.29 GJ/t")
    add("VN", "Hard coal", "d", ip["Anthracite"][0], "IPCC T1.2 anthracite 26.7", "INFERENCE", "C", "rank: domestic coal is anthracite (APEC 2022 lists VN anthracite only; GIPT 59 % anthracite)")
    add("MM", "Hard coal", "d", ip["Sub-Bituminous Coal"][0], "IPCC T1.2 sub-bituminous 18.9", "INFERENCE", "C", "rank: ADB 2016 'generally low-quality lignite and subbituminous'")
    add("MY", "Hard coal", "d", ip["Other Bituminous Coal"][0], "IPCC T1.2 other bituminous 25.8", "INFERENCE", "C", "rank: GIPT 94 % bituminous; APEC MY other bituminous only")
    add("PH", "Brown coal", "d", ip["Sub-Bituminous Coal"][0], "IPCC T1.2 sub-bituminous 18.9", "INFERENCE", "C", "rank: APEC PH sub-bituminous only; GIPT 54 % sub-bit / 42 % bituminous")
    add("SG", "Hard coal", "d", ip["Other Bituminous Coal"][0], "IPCC T1.2 other bituminous 25.8", "VERIFIED", "B", "UNSD reports SG coal as other bituminous")
    for cc in ("TH", "KH", "LA"):
        add(cc, "Lignite", "d", ip["Lignite"][0], "IPCC T1.2 lignite 11.9", "VERIFIED", "B", "UNSD reports the rank (child commodity)")
        add(cc, "Sub-bituminous coal", "d", ip["Sub-Bituminous Coal"][0], "IPCC T1.2 sub-bituminous 18.9", "VERIFIED", "B", "UNSD reports the rank (child commodity)")
        add(cc, "Other bituminous coal", "d", ip["Other Bituminous Coal"][0], "IPCC T1.2 other bituminous 25.8", "VERIFIED", "B", "UNSD reports the rank (child commodity)")
        add(cc, "Anthracite", "d", ip["Anthracite"][0], "IPCC T1.2 anthracite 26.7", "VERIFIED", "B", "UNSD reports the rank (child commodity)")
    for cc in ("KH",):
        pass
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); a = ap.parse_args()
    conv, _ = cm.upstream_dicts()
    R = references(a.work)
    S = pd.read_csv(a.work / "ncv/UNSD_IMPLIED_COAL_NCV_2019.csv")
    la = la_solve()
    G = gipt_ranks()
    X = schemes(R, S, la, conv)
    out = a.work / "ncv"
    pd.DataFrame(REFS).to_csv(out / "NCV_REFERENCE_VALUES.csv", index=False, float_format="%.12g")
    X.to_csv(out / "NCV_FACTOR_SCHEMES.csv", index=False, float_format="%.12g")
    G.to_csv(out / "GIPT_COAL_RANK_CAPACITY.csv", index=False, float_format="%.12g")
    (out / "_references_evidence.json").write_text(json.dumps(dict(la_solve=la, n_reference_values=len(REFS), heesi_boe_gj=3.6 / 0.6130), indent=1) + "\n")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 70)
    print(json.dumps(la))
    print(X[X.scheme != "a"][["country", "commodity", "scheme", "gj_per_unit", "v3_gj_per_unit", "change_vs_v3_pct", "status"]].round(3).to_string())
    print(G.round(3).to_string())


if __name__ == "__main__":
    main()
