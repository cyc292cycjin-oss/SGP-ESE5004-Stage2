"""V4 W08 checklist section 2 (decision 210 item 1 'rebuild in step'; items 4 a / b; decision 211 item 2): industry sub-sector cache from the same
UNSD SDMX 2019 records as the v4 base.

    PYTHONHASHSEED=0 python scripts_project/v4_industry_cache.py

Rules moved from the I2 scratch code without change (work/p1_v4_w07_20261106/I2/scripts/i2_items.py sdmx_industry_cells / build_cache / residues):
  cells     energy (MWh, S5p conversion: SDMX factors with NCV_EXCEPTIONS.csv) of every industry record by country x transaction (121 and the
            sub-rows 1211-1214O) x commodity; carrier from the extended dictionary; coal children replaced by parents per transaction;
  cache     MWh by sub-sector (s3_0_industry.py uses the within-carrier shares): 'other' = 1214O + the positive residual of 121 minus its reported
            sub-rows; a dropped record leaves the sub-row AND the 121 total; a scale factor applies to the sub-rows and the 121 total of a commodity;
  residues  RESIDUE_CLASSES.csv: bagasse (5120), black liquor (5140) in every row, 5150 in food / paper / wood / n.e.s. = self-produced (a);
            5150 elsewhere = purchased (c, kept). Decision 211 item 2: ID fuelwood of the paper row 1214G = self-produced (switch id_paper_fuelwood).
  ID fuelwood (decision 206 / 210 item 4 b): the ID fuelwood records are scaled to the 2010-2017 mean (FUELWOOD_OUTSIDE_BALANCE.csv, 29,510 thousand m3).
Writes research_inputs/industry_v4/SDMX_INDUSTRY_CELLS_2019.csv, RESIDUE_RECORDS_2019.csv and industry_cache_v4.json (the cache of the v4 main
switch set; other switch sets are built in memory by v4_industry.py from the cells table). Nothing is solved.
"""
from __future__ import annotations

import json

import pandas as pd

import reconstruct_base_accounts as rba
from v4_common import ASEAN, CARS19, SRC, V4_DIR, V4_MAIN, sha256

SUBTX = {"1211": "iron and steel", "1213": "chemical and petrochemical", "1214A": "non-ferrous metals", "1214B": "non-metallic minerals",
         "1214C": "transport equipment", "1214D": "machinery", "1214E": "mining and quarrying", "1214F": "food and tobacco", "1214G": "paper pulp and print",
         "1214H": "wood and wood products", "1214I": "construction", "1214J": "textile and leather", "1214O": "other"}
FW_CODE = "5110"
CELLS_CSV = V4_DIR / "SDMX_INDUSTRY_CELLS_2019.csv"
RESIDUES_CSV = V4_DIR / "RESIDUE_RECORDS_2019.csv"
CACHE_JSON = V4_DIR / "industry_cache_v4.json"


def residue_rules() -> dict:
    t = pd.read_csv(V4_DIR / "RESIDUE_CLASSES.csv", dtype=str)
    out = {}
    for r in t[(t.switch == "residue_boundary") & (t["class"] == "a")].to_dict("records"):
        rows = "all" if r["unsd_rows"].startswith("all") else set(r["unsd_rows"].split(";"))
        if rows == "all" or out.get(r["code"]) == "all":
            out[r["code"]] = "all"
        else:
            out[r["code"]] = out.get(r["code"], set()) | rows
    return out


def compute_cells() -> pd.DataFrame:
    """I2 sdmx_industry_cells (same records as the v4 base: capsule + extended dictionary + Recon 'd207' with the NCV exceptions)."""
    import v4_base_sdmx as B
    conv = B.ext_conversion(json.loads((SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text()))
    cap = json.loads(B.CAPSULE.read_text())["records"]
    R = B.Recon(dict(records=cap), conv, "d207", B.ncv_exceptions())
    rows = []
    for c in ASEAN:
        for t in list(SUBTX) + ["121"]:
            rs = [r for r in R.rows if r["Country"] == c and r.get("TransactionCode") == t]
            el = [r for r in rs if R.fuels.get(rba.commodity(r["Commodity"])) == "electricity"]
            fu = [r for r in rs if R.fuels.get(rba.commodity(r["Commodity"])) in ("oil", "gas", "coal", "biomass")]
            fu, _ = R.select_coal_hierarchy(fu)
            for r in el:
                rows.append(dict(country=c, tx=t, sub=SUBTX.get(t, "total"), code=r["CommodityCode"], commodity=r["Commodity"], carrier="electricity",
                                 unit=r["Unit"], quantity=float(r["Quantity"]), mwh=float(r["Quantity"]) * 1000.0, factor=""))
            for r in fu:
                rows.append(dict(country=c, tx=t, sub=SUBTX.get(t, "total"), code=r["CommodityCode"], commodity=r["Commodity"], carrier=R.fuels[rba.commodity(r["Commodity"])],
                                 unit=r["Unit"], quantity=float(r["Quantity"]), mwh=float(R.convert(r)[0]), factor=r.get("CONVERSION_FACTOR", "")))
    return pd.DataFrame(rows)


def load_cells() -> pd.DataFrame:
    return pd.read_csv(CELLS_CSV, dtype={"tx": str, "code": str, "factor": str}, keep_default_na=False, float_precision="round_trip")


def residues(cells: pd.DataFrame) -> pd.DataFrame:
    """Decision 210 item 4: self-produced residues (a) and purchased residues (c) in the 2019 industry sub-rows (MWh)."""
    rule = residue_rules()
    z = cells[(cells.tx != "121") & cells.code.isin(["5120", "5140", "5150"])].copy()
    z["cls"] = ["a" if (r.code in rule and (rule[r.code] == "all" or r.tx in rule[r.code])) else "c" for r in z.itertuples()]
    return z


def build_cache(cells: pd.DataFrame, drop: set | None = None, scale: dict | None = None) -> dict:
    """I2 build_cache: drop {(country, code, tx)} from the sub-row and the 121 total; scale {(country, code): factor} on the sub-rows and the 121 total."""
    drop, scale = drop or set(), scale or {}
    subs = sorted(set(SUBTX.values()))
    E = {c: {car: {s: 0.0 for s in subs} for car in CARS19} for c in ASEAN}
    tot = {c: {car: 0.0 for car in CARS19} for c in ASEAN}
    for r in cells.itertuples():
        f = scale.get((r.country, r.code), 1.0)
        if r.tx != "121" and (r.country, r.code, r.tx) in drop:
            continue
        v = r.mwh * f
        if r.tx == "121":
            v -= sum(cells[(cells.country == r.country) & (cells.code == r.code) & (cells.tx == t2)].mwh.sum() * f for (c2, k2, t2) in drop if c2 == r.country and k2 == r.code)
            tot[r.country][r.carrier] += v
        else:
            E[r.country][r.carrier][SUBTX[r.tx]] += v
    for c in ASEAN:
        for car in CARS19:
            res = tot[c][car] - sum(E[c][car].values())
            if res > 1e-6:
                E[c][car]["other"] += res
    recs = [dict(country=c, carrier=car, **{s: repr(v) for s, v in E[c][car].items()}) for c in ASEAN for car in CARS19]
    return dict(source="V4 W08 rebuild from UNSD SDMX 2019 (W12 responses), S5p conversion (v4_industry_cache.py = I2 build_cache)", source_sha256=sha256(CELLS_CSV) if CELLS_CSV.exists() else "",
                source_year=2019, meaning="MWh by industry sub-sector (shares only in s3_0); other = 1214O + positive residual of 121", numeric_acceptance="V4_W08", records=recs)


def fuelwood_mean(cells: pd.DataFrame, cc: str = "ID") -> dict:
    """Decision 206 / 210 item 4 b: SDMX fuelwood of the industry sub-rows, the 2010-2017 mean and the scale factor."""
    fw = cells[(cells.country == cc) & (cells.tx != "121") & (cells.carrier == "biomass") & (cells.code == FW_CODE)]
    t = pd.read_csv(V4_DIR / "FUELWOOD_OUTSIDE_BALANCE.csv").set_index("country")
    factor = float(fw.factor.astype(float).iloc[0]); km3 = float(t.at[cc, "mean_thousand_m3"])
    sdmx_mwh = float(fw.mwh.sum()); mean_mwh = km3 * factor * 1000.0 / 3.6
    paper = fw[fw.tx == "1214G"]
    return dict(factor_gj_m3=factor, sdmx_km3=float(fw.quantity.sum()), sdmx_mwh=sdmx_mwh, mean_km3=km3, mean_mwh=mean_mwh, scale=mean_mwh / sdmx_mwh,
                paper_sdmx_mwh=float(paper.mwh.sum()), paper_sdmx_km3=float(paper.quantity.sum()),
                share_non_paper=float(fw[fw.tx != "1214G"].mwh.sum()) / float(fw.mwh.sum()))


def drop_set(cells: pd.DataFrame, s: dict) -> set:
    """Records dropped from the cache under the switch set s: residues (a) when residue_boundary; the ID paper-row fuelwood when id_paper_fuelwood = residue."""
    out = set()
    if s.get("residue_boundary"):
        ra = residues(cells); ra = ra[ra.cls == "a"]
        out |= {(x.country, x.code, x.tx) for x in ra.itertuples()}
        if s.get("id_paper_fuelwood") == "residue":
            out |= {("ID", FW_CODE, "1214G")}
    return out


def cache_for(cells: pd.DataFrame, s: dict) -> dict:
    if s.get("base") != "sdmx_2019":
        return json.loads((SRC / "industry_cache.json").read_text())
    if not s.get("residue_boundary"):
        return build_cache(cells)
    return build_cache(cells, drop=drop_set(cells, s), scale={("ID", FW_CODE): fuelwood_mean(cells)["scale"]})


def main():
    cells = compute_cells()
    V4_DIR.mkdir(parents=True, exist_ok=True)
    cells.to_csv(CELLS_CSV, index=False, lineterminator="\n")
    res = residues(load_cells())
    res.to_csv(RESIDUES_CSV, index=False, lineterminator="\n")
    s = dict(V4_MAIN, anchor_mode="ras")
    cache = cache_for(load_cells(), s)
    CACHE_JSON.write_text(json.dumps(cache, indent=1) + "\n")
    fw = fuelwood_mean(load_cells())
    print(json.dumps(dict(cells=len(cells), residues_a=int((res.cls == "a").sum()), residues_a_twh=round(float(res[res.cls == "a"].mwh.sum()) / 1e6, 6),
                          fuelwood=fw, cache_sha256=sha256(CACHE_JSON)), indent=1))


if __name__ == "__main__":
    main()
