"""V4 S1 shared readers: paths, the HEESI 2025 rows used in S1 (from the page text of v4s1_pdf_text.py), the UNdata export rows of
Indonesia, the pypsa-asean conversion factors (parsed from _helpers.py without importing it), BPS parsed table access.

Every HEESI number used in S1 is read here from the page text and written with its page / table / column to
s1/HEESI_2025_VALUES_USED.csv by heesi_values(); row sums printed in the tables are checked where the table prints them.
"""
from __future__ import annotations

import ast
import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd

WORK = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_data_20261105")
REPO = Path("/home/jin/wt_v4_data")
PYPSA_ASEAN = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean")
UNSD_DIR = PYPSA_ASEAN / "data/demand/unsd/data"
HEESI_DIR = "extracted/heesi_2025/content-handbook-of-energy-and-economic-statistics-of-indonesia-2025"
HEESI_PDF = "work/p2_data_intake/v3_20261102/01_industry/content-handbook-of-energy-and-economic-statistics-of-indonesia-2025.pdf"
GIPT = "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv"
TWH_PER_PJ = 1 / 3.6


def num(tok: str) -> float:
    t = tok.strip().rstrip(")")
    if t.lower().strip(".") in ("n.a", "n,a", "na", "-", ""):
        return np.nan
    return float(t.replace(",", ""))


def heesi_year_rows(work: Path, page: int, year: str) -> list[list[float]]:
    """All lines of HEESI page text (PDF page index) that start with `year` (a footnote digit may follow, e.g. '20244)'); numbers only."""
    txt = (work / HEESI_DIR / f"p{page:03d}.txt").read_text(encoding="utf-8")
    out = []
    for line in txt.splitlines():
        s = re.sub(r"\s+", " ", line).strip()
        m = re.match(rf"^{year}\d?\)?\s+(.*)$", s)
        if m:
            out.append([num(t) for t in m.group(1).split(" ")])
    return out


def heesi_values(work: Path) -> pd.DataFrame:
    """The HEESI 2025 values used in S1, each with PDF page, printed page, table and column; sums checked where printed."""
    rows = []

    def add(page, printed, table, column, year, value, unit, note=""):
        rows.append(dict(source="HEESI 2025", pdf_page=page, printed_page=printed, table=table, column=column, year=year, value=value, unit=unit, note=note))

    r = heesi_year_rows(work, 60, "2019")[0]   # 5.1.1 industrial sector, original units (19 values)
    assert len(r) == 18, r   # biomass, geothermal, coal, briquette, gas, 10 oil-fuel columns, total oil, LPG, electricity
    add(60, 44, "5.1.1 Energy Consumption in Industrial Sector (Original Unit)", "Coal", 2019, r[2] * 1e3, "t")
    add(60, 44, "5.1.1", "Gas", 2019, r[4], "MMSCF")
    add(60, 44, "5.1.1", "Total oil fuel", 2019, r[15], "kL")
    add(60, 44, "5.1.1", "LPG", 2019, r[16] * 1e3, "t")
    add(60, 44, "5.1.1", "Electricity", 2019, r[17], "GWh", "2015-2017 equal PLN industrial sales (6.4.4); from 2018 higher")
    add(60, 44, "5.1.1", "Industrial biomass", 2019, r[0] * 1e3, "t")
    r = heesi_year_rows(work, 62, "2019")[0]   # 5.1.2 same, energy units (thousand BOE)
    add(62, 46, "5.1.2 Energy Consumption in Industrial Sector (Energy Unit)", "Coal", 2019, r[2] * 1e3, "BOE")
    add(62, 46, "5.1.2", "Electricity", 2019, r[17] * 1e3, "BOE")
    add(62, 46, "5.1.2", "Total", 2019, r[18] * 1e3, "BOE")
    for y in ("2018", "2019"):
        r = heesi_year_rows(work, 90, y)[0]   # 6.1.4 domestic coal sales (t)
        assert abs(sum(r[1:]) - r[0]) < 2, (y, r)
        for k, c in enumerate(["Total", "Iron, Steel & Metallurgy", "Power Plant", "Cement, Textile, Fertilizer", "Pulp & Paper", "Briquette", "Others"]):
            add(90, 74, "6.1.4 Domestic Coal Sales", c, int(y), r[k], "t", "note 1: 2018-2019 acceleration for downstream mineral industry" if k == 1 else "")
    r = heesi_year_rows(work, 116, "2019")   # 6.4.1A installed capacity: first row on-grid (17 values), second off-grid
    on = r[0]; assert len(on) == 17 and abs(np.nansum(on[:-1]) - on[-1]) < 0.05, on
    add(116, 100, "6.4.1A Power Plant Installed Capacity (on grid incl. PPU and IUPTLS, note 1)", "Steam PP", 2019, on[1], "MW", "note 3: Diesel PP including captive power")
    add(116, 100, "6.4.1A", "On-grid total", 2019, on[-1], "MW")
    off = r[1]
    add(116, 100, "6.4.1A", "Off-grid sub total", 2019, off[-2], "MW", "off-grid columns: hydro, micro, mini, solar, wind, biomass+bionabati, biogas, coal gasification, hybrid ...; no coal steam before 2024")
    r24 = heesi_year_rows(work, 116, "2024")[1]
    add(116, 100, "6.4.1A", "Off-grid steam PP", 2024, r24[10], "MW", "first year with off-grid coal steam")
    r = heesi_year_rows(work, 118, "2025")   # 6.4.1B 2025 by ownership: PLN, PPU, IUPTLS
    ppu, iup = r[1], r[2]
    assert abs(sum(ppu[:-1]) - ppu[-1]) < 0.05 and abs(sum(iup[:-2]) - iup[-2]) < 0.05, (ppu, iup)
    add(118, 102, "6.4.1B Power Plant Installed Capacity 2025", "PPU Steam", 2025, ppu[5], "MW")
    add(118, 102, "6.4.1B", "PPU Coal Gasification", 2025, ppu[9], "MW")
    add(118, 102, "6.4.1B", "IUPTLS Steam", 2025, iup[10], "MW", "IUPTLS = generators owned for own use (note 7)")
    add(118, 102, "6.4.1B", "IUPTLS Coal Gasification", 2025, iup[14], "MW")
    r = heesi_year_rows(work, 120, "2019")[0]   # 6.4.2 PLN production (GWh)
    assert len(r) == 16 and abs(np.nansum([r[i] for i in (0, 1, 2, 3, 8, 9, 10, 12, 13, 14)]) - r[15]) < 2, r
    add(120, 104, "6.4.2 Power Plant Production (PLN)", "Steam PP Coal", 2019, r[4], "GWh")
    add(120, 104, "6.4.2", "Steam PP Total", 2019, r[8], "GWh")
    for y in range(2015, 2025):
        rr = heesi_year_rows(work, 120, str(y))[0]
        v = rr[4] * (1e3 if rr[4] < 1000 else 1.0)   # the 2024 row prints '114.158' with dots as thousands separators
        add(120, 104, "6.4.2", "Steam PP Coal", y, v, "GWh", "2024 printed with '.' thousands separators" if y == 2024 else "")
    r = heesi_year_rows(work, 122, "2019")   # 6.4.2A purchases from captive power and IPP (on grid) + off grid
    on = r[0]; assert len(on) == 16 and abs(np.nansum([on[i] for i in (0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14)]) + 193543 - on[15]) < 2, on
    add(122, 106, "6.4.2A PLN Electricity Purchase from Captive Power & IPP", "Steam PP Coal", 2019, on[4], "GWh")
    add(122, 106, "6.4.2A", "Steam PP Total", 2019, on[7], "GWh")
    add(122, 106, "6.4.2A", "Total On Grid", 2019, on[15], "GWh")
    off = r[1]; assert abs(sum(off[:-2]) - off[-2]) < 2, off
    for k, c in enumerate(["Off-grid Hydro", "Off-grid Micro Hydro", "Off-grid Mini Hydro", "Off-grid Solar", "Off-grid Wind", "Off-grid Biomass + Bionabati",
                           "Off-grid Biogas", "Off-grid Hybrid", "Off-grid Total", "Grand Total"]):
        add(122, 106, "6.4.2A", c, 2019, off[k], "GWh", "note 1: off grid = captive power from PPU, state-budget and non-governmental plants" if k == 8 else "")
    r = heesi_year_rows(work, 124, "2025")   # 6.4.2B 2025 by ownership
    iu = r[-1]
    add(124, 108, "6.4.2B Power Plant Production 2025", "IUPTLS & PPU Steam PP", 2025, iu[3], "GWh", "note 4: including coal gasification")
    add(124, 108, "6.4.2B", "IUPTLS & PPU Sub Total", 2025, iu[6], "GWh")
    r = heesi_year_rows(work, 128, "2019")[0]   # 6.4.4 electricity utilization
    assert abs(sum(r[:7]) - r[7]) < 2 and abs(sum(r[8:13]) - r[13]) < 2, r
    add(128, 112, "6.4.4 Electricity Utilization", "PLN sales Industry", 2019, r[2], "GWh")
    add(128, 112, "6.4.4", "Non PLN consumption Industry", 2019, r[10], "GWh", "glossary p.147: non-PLN consumption includes industrial own use")
    add(128, 112, "6.4.4", "Non PLN consumption Total", 2019, r[13], "GWh")
    for y in range(2015, 2025):
        rr = heesi_year_rows(work, 132, str(y))[0]
        add(132, 116, "6.4.7 Fuel Consumption of PLN Power Plant", "Coal", y, rr[0], "t")
    txt = (work / HEESI_DIR / "p170.txt").read_text(encoding="utf-8")
    for name in ("Kalimantan Coal1)", "Average Coal", "Briquette", "Natural Gas", "LPG", "Gasoil", "Premium", "Kerosene", "MDF", "FO", "Electric Power"):
        m = re.search(r"^\s*" + re.escape(name) + r"\s+(\S.*?)\s+([\d.]+)\s*$", txt, re.M)
        if not m:
            raise ValueError(f"Annex 03: {name} not found")
        add(170, 154, "Annex 03 Conversion Factor (multiplier to BOE)", name.replace("1)", ""), None, float(m.group(2)), f"BOE per {m.group(1).strip()}",
            "note 1: Kalimantan coal factor before 2023, average coal after" if name.startswith("Kalimantan") else "")
    return pd.DataFrame(rows)


def hv(H: pd.DataFrame, column: str, year=None, table_prefix=None) -> float:
    z = H[H.column == column]
    if year is not None:
        z = z[z.year == year]
    if table_prefix:   # 'X ' (trailing space) matches table 'X' or 'X ...' only, not 'XA'
        z = z[(z.table == table_prefix.strip()) | z.table.str.startswith(table_prefix)]
    if len(z) != 1:
        raise KeyError((column, year, table_prefix, len(z)))
    return float(z.value.iloc[0])


def boe_gj(H: pd.DataFrame) -> float:
    """GJ per HEESI BOE from Annex 03 'Electric Power 0.6130 BOE per MWh' (1 MWh = 3.6 GJ)."""
    return 3.6 / hv(H, "Electric Power")


def unsd(country: str = "Indonesia", year: str = "2019") -> pd.DataFrame:
    df = pd.concat((pd.read_csv(f, sep=";", dtype=str) for f in sorted(glob.glob(str(UNSD_DIR / "*.txt")))), ignore_index=True)
    df = df[df["Country or Area"].eq(country) & df.Year.eq(year)].copy()
    sp = df["Commodity - Transaction"].str.split(" - ", n=1, expand=True)
    df["commodity"], df["transaction"] = sp[0].str.strip(), sp[1].fillna("").str.strip()
    df["q"] = pd.to_numeric(df.Quantity, errors="coerce")
    return df[["commodity", "transaction", "Unit", "q"]]


def conv_factors() -> dict:
    """pypsa-asean scripts/_helpers.py get_conv_factors('industry'): {fuel: TWh per kt (or per TJ / GWh)}, read with ast (no import)."""
    src = (PYPSA_ASEAN / "scripts/_helpers.py").read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_conv_factors":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.Dict) and len(sub.value.keys) > 10:
                    return ast.literal_eval(sub.value)
    raise ValueError("conversion dictionary not found")


def bps_raw(work: Path) -> pd.DataFrame:
    return pd.read_csv(work / "s1/ID_BPS_IBS_2019_RAW.csv", dtype={"code": str})
