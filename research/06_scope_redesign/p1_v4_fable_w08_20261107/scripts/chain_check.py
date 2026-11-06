"""Fable W08 review, dimension 3: independent hand calculation of data chains from the raw UNSD SDMX responses to the v4 tables.

Own XML parser (no import of the repository modules). For every selected record: raw quantity x factor -> MWh, compared with
SDMX_INDUSTRY_CELLS_2019.csv (sub-rows), D1_BASE2019_SDMX.csv (seed rows), industry_cache_v4.json and the out_ras ATS table
(2050 = base x multiplier). Read-only; writes CHAIN_CHECK.json next to this script's parent folder.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}
SD = REPO / "research_inputs/assembly_v1/sources/unsd_sdmx_2019"
V4 = REPO / "research_inputs/industry_v4"

EXC = {("ID", "0100"): 20.29, ("ID", "0311"): 28.20}   # NCV_EXCEPTIONS.csv


def obs(cc):
    root = ET.parse(SD / f"{cc}_2019_all.xml").getroot()
    rows = {}
    for s in root.iter("{%s}Series" % NS["g"]):
        key = {v.get("id"): v.get("value") for v in s.find("g:SeriesKey", NS)}
        sa = s.find("g:Attributes", NS)
        satt = {v.get("id"): v.get("value") for v in (sa if sa is not None else [])}
        for o in s.findall("g:Obs", NS):
            oa = o.find("g:Attributes", NS)
            att = dict(satt)
            att.update({a.get("id"): a.get("value") for a in (oa if oa is not None else [])})
            rows[(key["COMMODITY"], key["TRANSACTION"])] = dict(value=float(o.find("g:ObsValue", NS).get("value")), unit=att.get("UNIT_MEASURE"),
                                                                 mult=int(att.get("UNIT_MULT", "0")), cf=att.get("CONVERSION_FACTOR"), status=att.get("OBS_STATUS"))
    return rows


def to_mwh(cc, code, r):
    """Own conversion: TN (thousand t when UNIT_MULT 3) x GJ/t x 1000 / 3.6; M3 (thousand m3) x GJ/m3 x 1000 / 3.6; TJ / 0.0036 (gas x 0.9); GWh x 1000."""
    q = r["value"] * 10 ** r["mult"]   # base units: t, m3, TJ, GWh(mult 0)
    if r["unit"] in ("TN", "M3"):
        f = EXC.get((cc, code), float(r["cf"]))
        return q * f / 3.6, f"{r['value']} x10^{r['mult']} {r['unit']} x {f} GJ/unit / 3.6"
    if r["unit"] == "TJ":
        if code == "3000":
            return q * 0.9 / 0.0036, f"{q} TJ GCV x 0.9 / 0.0036"
        return q / 0.0036, f"{q} TJ / 0.0036"
    if r["unit"] == "GWHR":
        return q * 1000.0, f"{q} GWh x 1000"
    raise ValueError(r)


SUB = {"121": "total", "1211": "iron and steel", "1213": "chemical and petrochemical", "1214B": "non-metallic minerals", "1214F": "food and tobacco",
       "1214G": "paper pulp and print", "1214O": "other", "1214H": "wood and wood products"}
CHAINS = [  # (country, commodity code, transaction code, label)
    ("ID", "0100", "121", "ID hard coal, industry total (NCV exception 20.29)"),
    ("ID", "5110", "1214G", "ID fuelwood, paper row"),
    ("ID", "5110", "121", "ID fuelwood, industry total"),
    ("ID", "4670", "121", "ID gas/diesel oil, industry total"),
    ("ID", "4652", "1231", "ID motor gasoline, households"),
    ("ID", "7000", "121", "ID electricity, industry"),
    ("ID", "5150", "1214G", "ID other vegetal residues, paper row (TJ)"),
    ("ID", "5120", "1214O", "ID bagasse, n.e.s. row"),
    ("VN", "4670", "121", "VN gas/diesel oil, industry total"),
    ("VN", "0100", "121", "VN hard coal, industry total"),
    ("VN", "7000", "121", "VN electricity, industry"),
    ("VN", "5120", "1214O", "VN bagasse, n.e.s. row"),
    ("TH", "0100", "121", "TH hard coal, industry total"),
    ("TH", "5120", "1214F", "TH bagasse, food row"),
    ("TH", "5150", "1214F", "TH other vegetal residues, food row (TJ)"),
    ("TH", "3000", "121", "TH natural gas, industry total (TJ GCV)"),
    ("TH", "7000", "121", "TH electricity, industry"),
    ("MY", "3000", "121", "MY natural gas, industry total (TJ GCV)"),
    ("MY", "0100", "121", "MY hard coal, industry total"),
    ("MY", "4670", "121", "MY gas/diesel oil, industry total"),
    ("KH", "0200", "121", "KH brown coal, industry total"),
    ("PH", "0100", "121", "PH hard coal, industry total"),
]
CARRIER = {"0100": "coal", "0200": "coal", "0311": "coal", "3000": "gas", "4670": "oil", "4652": "oil", "5110": "biomass", "5120": "biomass", "5150": "biomass", "7000": "electricity"}

cells = pd.read_csv(V4 / "SDMX_INDUSTRY_CELLS_2019.csv", dtype={"tx": str, "code": str}, keep_default_na=False)
base = pd.read_csv(V4 / "D1_BASE2019_SDMX.csv", keep_default_na=False)
hh = pd.read_csv(V4 / "HOUSEHOLD_GASOLINE_2019.csv").set_index("country")
cache = json.loads((V4 / "industry_cache_v4.json").read_text())
ats = pd.read_csv(V4 / "out_ras/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False, dtype=str)
summ = pd.read_csv(V4 / "out_ras/INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
anch = pd.read_csv(V4 / "out_ras/DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")

res = []
data = {cc: obs(cc) for cc in sorted({c[0] for c in CHAINS})}
for cc, code, tx, label in CHAINS:
    r = data[cc].get((code, tx))
    if r is None:
        res.append(dict(label=label, country=cc, code=code, tx=tx, raw="ABSENT"))
        continue
    mwh, how = to_mwh(cc, code, r)
    row = dict(label=label, country=cc, code=code, tx=tx, raw_value=r["value"], unit=r["unit"], unit_mult=r["mult"], sdmx_factor=r["cf"], status=r["status"],
               own_mwh=mwh, own_twh=mwh / 1e6, rule=how)
    # cells table (industry rows only)
    z = cells[(cells.country == cc) & (cells.code == code) & (cells.tx == tx)]
    if len(z):
        row["cells_mwh"] = float(z.mwh.iloc[0]); row["cells_diff_mwh"] = float(z.mwh.iloc[0]) - mwh
    # D1 seed: industry carrier row (121 totals) = sum of all commodities of the carrier in 121 (after blend / coal hierarchy) -> show the seed row for context
    if tx == "121":
        acc = "UNSD_electricity_Industry" if code == "7000" else "IndustryFinalEnergy"
        b = base[(base.country == cc) & (base.account == acc) & (base.carrier == CARRIER[code])]
        row["d1_seed_industry_carrier_mwh"] = float(b.base_2019_mwh.astype(float).sum()) if len(b) else None
        # all commodities of this carrier in 121 (own parse, coal hierarchy: parent 0100 / 0200 replace children)
        tot = 0.0; parts = {}
        for (k, t), rr in data[cc].items():
            if t != "121" or k not in CARRIER or CARRIER[k] != CARRIER[code]:
                continue
            if k in ("0110", "0121", "0129", "0210", "0220"):
                continue   # children replaced by the parents 0100 / 0200 when the parent is reported
            m, _ = to_mwh(cc, k, rr); tot += m; parts[k] = m
        row["own_sum_carrier_121_mwh_selected_codes"] = tot; row["own_parts"] = parts
        a = ats[(ats.country == cc) & (ats.sector == "Industry") & (ats.carrier == CARRIER[code])]
        if len(a):
            row["ats_base_2019_mwh"] = float(pd.to_numeric(a.base_2019_mwh).sum()); row["ats_value_2050_mwh"] = float(pd.to_numeric(a.value_2050_mwh, errors="coerce").fillna(0).sum())
            row["ats_multiplier"] = float(a.multiplier_total.iloc[0]); row["own_2050_check_mwh"] = row["ats_base_2019_mwh"] * row["ats_multiplier"]
            row["ats_2050_minus_own_mwh"] = row["ats_value_2050_mwh"] - row["own_2050_check_mwh"]
    if code == "4652" and tx == "1231":
        row["household_gasoline_table_mwh"] = float(hh.at[cc, "base_2019_mwh"]); row["diff_mwh"] = row["household_gasoline_table_mwh"] - mwh
        b = base[(base.country == cc) & (base.account == "ResidentialFuel") & (base.carrier == "oil")]
        row["d1_seed_residential_oil_mwh"] = float(b.base_2019_mwh.astype(float).sum())
    # cache cell (sub-row shares x ATS base): cache stores MWh per sub-sector
    if tx in SUB and tx != "121":
        rec = [x for x in cache["records"] if x["country"] == cc and x["carrier"] == CARRIER[code]]
        if rec:
            row["cache_cell_mwh_" + SUB[tx]] = float(rec[0][SUB[tx]])
    res.append(row)

# T_v2 chain for ID: ATS industry 2050 by carrier vs summary T columns
tv = {}
for cc in ("ID", "VN", "TH", "MY"):
    a = ats[(ats.country == cc) & (ats.sector == "Industry")].copy(); a["v"] = pd.to_numeric(a.value_2050_mwh, errors="coerce").fillna(0.0)
    by_car = a.groupby("carrier").v.sum().to_dict()
    S = summ.loc[cc]
    T_cols = [c for c in summ.columns if c.startswith("pe_") and c.endswith("_mwh") and "before" not in c and "band" not in c and "overflow" not in c]
    tv[cc] = dict(ats_industry_2050_by_carrier_mwh=by_car, ats_industry_2050_total_mwh=float(a.v.sum()), industry_multiplier=float(anch.at[cc, "industry_multiplier"]),
                  industry_anchor_mwh=float(anch.at[cc, "industry_anchor_mwh"]), summary_T_columns={c: float(S[c]) for c in T_cols})
json.dump(dict(chains=res, t_v2_context=tv), open(OUT, "w"), indent=1, default=float)
pd.set_option("display.width", 250)
df = pd.DataFrame([{k: v for k, v in r.items() if k in ("label", "raw_value", "unit", "sdmx_factor", "own_twh", "cells_diff_mwh", "d1_seed_industry_carrier_mwh", "own_sum_carrier_121_mwh_selected_codes", "ats_2050_minus_own_mwh", "diff_mwh")} for r in res])
print(df.to_string())
