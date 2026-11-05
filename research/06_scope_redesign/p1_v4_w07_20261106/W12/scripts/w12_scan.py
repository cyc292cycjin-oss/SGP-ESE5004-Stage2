"""W12-5: search for other 'parent and child both counted' / 'same quantity loaded twice' patterns (read-only).

A. Demand tables (D1 ratio table and ATS anchor table, worktree): rows of one country and sector with the same positive 2019 base under
   different accounts (the signature of the rail parent / child pair), and accounts named as parents.
B. Network (v3.1 HPC integrated 2920x3h, unsolved): every demand-table row id that appears in the source_account_id of loads of more than
   one load account family; per family the annual energy. Expected splits (one row spread over nodes or heat bands) are separated from
   rows loaded by two different families.
C. Biomass supply categories that are mill / plant residues burnt on site (closed loop, decision 206 item 3): potential_main_mwh per
   country (oil-palm fibre and kernel shell, sugarcane process residue = bagasse, wood-processing residues) next to the matching UNSD
   2019 demand rows of the export (bagasse, other vegetal material - absent, fuelwood in wood industry).
D. UNSD 2019 export rows whose transaction puts a transport fuel into a non-transport account (motor gasoline / diesel 'consumption by
   households' etc.).
Writes tables/W12_5_*.csv and evidence/W12_5.json. Nothing is solved.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402

DV = cm.REPO / "research_inputs/demand_v5"


def part_a(ev):
    rows = []
    for f in ("DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"):
        d = pd.read_csv(DV / f, keep_default_na=False, dtype=str)
        d["b"] = pd.to_numeric(d.base_2019_mwh, errors="coerce")
        for (c, s), g in d[d.b > 0].groupby(["country", "sector"]):
            for b, h in g.groupby("b"):
                if h.account.nunique() > 1:
                    rows.append(dict(table=f, country=c, sector=s, base_2019_mwh=b, rows=";".join(f"{a}|{k}" for a, k in zip(h.account, h.carrier)),
                                     value_2050_mwh=";".join(h.value_2050_mwh)))
        par = d[d.account.str.contains("Parent|Total|AllFuels", regex=True)]
        for r in par.itertuples():
            rows.append(dict(table=f, country=r.country, sector=r.sector, base_2019_mwh=r.b, rows=f"{r.account}|{r.carrier} (parent-type name)", value_2050_mwh=r.value_2050_mwh))
    A = pd.DataFrame(rows)
    cm.write_csv(A.to_dict("records"), cm.TABLES / "W12_5_TABLE_EQUAL_BASE_ROWS.csv")
    ev.add("A.equal_base_groups", int((~A.rows.str.contains("parent-type")).sum()), "groups", "EXACT", "A", "W12_5_TABLE_EQUAL_BASE_ROWS.csv",
           "same country, sector and positive 2019 base under different accounts")
    return A


def part_b(ev):
    f = cm.HPC31 / "integrated_2920_3h_unsolved.nc"
    ds = xr.open_dataset(f)
    try:
        li = [str(x) for x in ds["loads_i"].values]
        acc = pd.Series([str(x) for x in ds["loads_account"].values], index=li)
        src = pd.Series([str(x) for x in ds["loads_source_account_id"].values], index=li)
        cty = pd.Series([str(x) for x in ds["loads_country"].values], index=li)
        ps = pd.Series(ds["loads_p_set"].values.astype(float), index=li)
        w = ds["snapshots_generators"].values.astype(float)
        annual = ps * float(w.sum())
        if "loads_t_p_set" in ds and ds["loads_t_p_set"].shape[1]:
            tc = [str(x) for x in ds["loads_t_p_set_i"].values]
            tv = ds["loads_t_p_set"].values
            for j, c in enumerate(tc):
                annual[c] = float((tv[:, j] * w).sum())
    finally:
        ds.close()
    fam = defaultdict(lambda: defaultdict(float)); nloads = defaultdict(lambda: defaultdict(int))
    for l in li:
        for tok in [t.strip() for t in src[l].split(";") if t.strip()]:
            key = tok if ":" in tok else f"{cty[l]}:{tok}"
            fam[key][acc[l]] += float(annual[l]); nloads[key][acc[l]] += 1
    rows = []
    for k, d in sorted(fam.items()):
        if len(d) > 1:
            rows.append(dict(source_token=k, families=len(d), detail="; ".join(f"{a} n={nloads[k][a]} {v / 1e6:.3f} TWh" for a, v in sorted(d.items()))))
    B = pd.DataFrame(rows)
    cm.write_csv(B.to_dict("records"), cm.TABLES / "W12_5_NETWORK_SOURCE_MULTI_FAMILY.csv", ["source_token", "families", "detail"])
    ev.add("B.multi_family_tokens", int(len(B)), "tokens", "VERIFIED", "A", f"hpc_package_v3_1/networks/{f.name} loads_source_account_id")
    return B


def part_c(ev):
    pot = pd.read_csv(cm.REPO / "research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050.csv", keep_default_na=False)
    pot["p"] = pd.to_numeric(pot.potential_main_mwh, errors="coerce").fillna(0.0)
    bag = pd.read_csv(cm.TABLES / "W12_3_BAGASSE_SUPPLY_OVERESTIMATE.csv").set_index("country")
    miss = pd.read_csv(cm.TABLES / "W12_4_MISSING_BY_COUNTRY_SECTOR_COMMODITY.csv")
    u = cm.load_unsd_2019()
    rows = []
    for c in cm.ASEAN:
        p = pot[pot.country == c]
        solid = float(p[p.feedstock_group != "biogas"].p.sum())
        fib = float(p[p.category == "oil_palm_fibre"].p.sum()); pks = float(p[p.category == "oil_palm_pks"].p.sum())
        wood = float(p[p.category == "wood_processing_residues"].p.sum())
        bg = float(bag.at[c, "bagasse_mwh_15"]) if c in bag.index else 0.0
        ub = u[(u.ISO == c) & (u.commodity == "Bagasse")]
        bag_ind = float(ub[ub.transaction.str.contains("manufacturing|food|industr", regex=True, na=False)].q.max() if len(ub) else 0.0) * 7.718 / 3.6 * 1e3
        bag_tr = float(ub[ub.transaction.str.startswith("transformation in electricity", na=False)].q.sum()) * 7.718 / 3.6 * 1e3
        ovmr_ind = float(miss[(miss.cc == c) & (miss.d1_account == "IndustryFinalEnergy") & (miss.commodity == "Other Vegetal Material and Residues")].tj.sum()) / 0.0036
        rows.append(dict(country=c, solid_potential_mwh=solid, palm_fibre_mwh=fib, palm_kernel_shell_mwh=pks, bagasse_part_mwh=bg, wood_processing_residues_mwh=wood,
                         closed_loop_categories_mwh=fib + pks + bg + wood, closed_loop_share_of_solid=(fib + pks + bg + wood) / solid if solid else None,
                         unsd2019_bagasse_industry_mwh=bag_ind, unsd2019_bagasse_power_mwh=bag_tr, sdmx2019_industry_other_vegetal_mwh_absent_from_export=ovmr_ind))
    C = pd.DataFrame(rows)
    cm.write_csv(C.to_dict("records"), cm.TABLES / "W12_5_CLOSED_LOOP_SUPPLY_VS_DEMAND.csv")
    for r in C[C.closed_loop_categories_mwh > 1e6].itertuples():
        ev.add(f"C.{r.country}.closed_loop_categories_twh", r.closed_loop_categories_mwh / 1e6, "TWh (2050 potential)", "EXACT", "C",
               "BIOMASS_POTENTIAL_2050.csv + W12_3 bagasse split", f"share of solid potential {r.closed_loop_share_of_solid:.3f}")
    return C


def part_d(ev):
    u = cm.load_unsd_2019()
    tf = ["Motor Gasoline", "Motor gasoline", "Gas Oil/ Diesel Oil", "Kerosene-type Jet Fuel", "Aviation gasoline"]
    q = u[u.commodity.isin(tf) & u.transaction.isin(["consumption by households", "consumption by commerce and public services", "consumption by commercial and public services"])]
    fz = {"Motor Gasoline": 44.28, "Motor gasoline": 44.28, "Gas Oil/ Diesel Oil": 42.98, "Kerosene-type Jet Fuel": 44.10, "Aviation gasoline": 44.28}
    rows = [dict(country=r.ISO, commodity=r.commodity, transaction=r.transaction, kt=r.q, twh_approx=r.q * fz[r.commodity] / 3600.0, footnote=r["Quantity Footnotes"] if "Quantity Footnotes" in u.columns else "")
            for _, r in q.iterrows()]
    ats = pd.read_csv(DV / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False, dtype=str)
    for r in rows:
        accn = "ResidentialFuel" if "households" in r["transaction"] else "ServicesFuel"
        a = ats[(ats.country == r["country"]) & (ats.account == accn) & (ats.carrier == "oil")]
        r["d1_account"] = accn
        r["ats_account_oil_base_2019_twh"] = float(pd.to_numeric(a.base_2019_mwh, errors="coerce").sum()) / 1e6 if len(a) else None
        r["ats_account_oil_2050_twh"] = float(pd.to_numeric(a.value_2050_mwh, errors="coerce").sum()) / 1e6 if len(a) else None
        r["share_of_account_oil_base"] = (r["twh_approx"] / r["ats_account_oil_base_2019_twh"]) if r["ats_account_oil_base_2019_twh"] else None
    D = pd.DataFrame(rows).sort_values("twh_approx", ascending=False)
    cm.write_csv(D.to_dict("records"), cm.TABLES / "W12_5_TRANSPORT_FUELS_IN_BUILDINGS.csv")
    for r in D[D.twh_approx > 1].itertuples():
        ev.add(f"D.{r.country}.{r.commodity}.{r.transaction}", r.twh_approx, "TWh (2019, approx NCV)", "VERIFIED", "A", "UNdata export (pypsa-asean)", f"{r.kt} kt")
    return D


def main():
    ev = cm.Evidence("W12_5")
    A = part_a(ev); B = part_b(ev); C = part_c(ev); D = part_d(ev)
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20); pd.set_option("display.max_colwidth", 200); pd.set_option("display.max_rows", 200)
    print(A.to_string()); print(B.to_string()); print((C.set_index("country") / 1e6).round(2).to_string()); print(D.to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
