"""W12-2: rail non-electric fuel loaded twice (TransportEmbeddedFuelParent + its RailNonElectric child).

Code facts (VERIFIED by reading): reconstruct_base_accounts.py:227-234 adds RailNonElectric children and keeps the parent account;
m08b_demand.py:230/268-272 builds the transport base and m_tr over ALL non-electric Transport rows (parent and child both in);
s2_layers.py:25/:773 loads the parent inside the land-transport EV load, :789-803 loads RailNonElectric as rail oil meters.

This script (read-only for the repository):
  A. reads both demand tables (D1 ratio table = RAS seed; ATS anchor table = network input) for the parent / child rows;
  B. reads the four v3.1 HPC 2920x3h networks and the v3.1 56x3h smoke network: rail oil loads and the parent's part of the EV loads
     (EV load = land rows x ev_share x oil_to_electricity; parent fraction = parent / land rows of the ATS table);
  C. re-runs m08b_demand.py and s3_0_industry.py in a scratch copy OUTSIDE the repository (/home/jin/v4w07_w12/chain):
     first unmodified (must reproduce the repository outputs byte for byte, instruction A1), then with the parent rows blanked in the
     D1 table (fix variant b: parent neither in the RAS seed / transport base nor in the network). Variant a (network-only: drop the
     parent from LAND_TRANSPORT_ACCOUNTS) is computed analytically from the ATS table.
Writes tables/W12_2_*.csv and evidence/W12_2.json. Nothing is solved.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402

CHAIN = Path("/home/jin/v4w07_w12/chain")
DV = "research_inputs/demand_v5"
D1 = f"{DV}/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
ATS = f"{DV}/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
M08B_OUT = ["DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_OUTPUT_BASE_M08B.csv"]
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
S3_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY, "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
LAND = {"RoadResidualFuel", "TransportNEC", "TransportEmbeddedFuelParent"}   # s2_layers.py:25
PARENT, CHILD = "TransportEmbeddedFuelParent", "RailNonElectric"


def run(script: str) -> float:
    t = time.time()
    r = subprocess.run([sys.executable, script], cwd=CHAIN / "scripts_project", capture_output=True, text=True, env=ENV)
    if r.returncode:
        raise RuntimeError(f"{script}: {r.stderr[-3000:]}")
    return time.time() - t


def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def network_part(ev: cm.Evidence, ats: pd.DataFrame, conv: dict):
    rows = []
    nets = [(f"hpc_package_v3_1/networks/{f.name}", f) for f in sorted(cm.HPC31.glob("*_unsolved.nc"))] + \
           [("smoke56_v31/F1 (solved)", cm.solved_nc(cm.SMOKE31 / "F1")), ("smoke56_v31/F2 (solved)", cm.solved_nc(cm.SMOKE31 / "F2"))]
    for label, f in nets:
        ds = xr.open_dataset(f)
        try:
            meta = cm.nc_meta(ds); P = meta["s2_demand_ledger"]["parameters"]
            li = [str(x) for x in ds["loads_i"].values]
            acc = pd.Series([str(x) for x in ds["loads_account"].values], index=li)
            cty = pd.Series([str(x) for x in ds["loads_country"].values], index=li)
            src = pd.Series([str(x) for x in ds["loads_source_account_id"].values], index=li)
            w = ds["snapshots_generators"].values.astype(float) if "snapshots_generators" in ds else None
            hours = float(w.sum())
            ps = pd.Series(ds["loads_p_set"].values.astype(float), index=li)
            annual = ps * hours
            if "loads_t_p_set" in ds and ds["loads_t_p_set"].shape[1] > 0:
                tcols = [str(x) for x in ds["loads_t_p_set_i"].values]
                tv = ds["loads_t_p_set"].values
                for j, c in enumerate(tcols):
                    annual[c] = float((tv[:, j] * w).sum())
            for c in cm.ASEAN:
                a = ats[ats.country == c]
                land = float(num(a[(a.sector == "Transport") & a.account.isin(LAND) & (a.carrier != "electricity")].value_2050_mwh).sum())
                par = float(num(a[(a.sector == "Transport") & (a.account == PARENT)].value_2050_mwh).sum())
                rail_tab = float(num(a[(a.sector == "Transport") & (a.account == CHILD)].value_2050_mwh).sum())
                evl = acc.index[(acc == "LandTransportEV") & (cty == c)]
                rl = acc.index[(acc == CHILD) & (cty == c)]
                ev_net = float(annual[evl].sum()); rail_net = float(annual[rl].sum())
                ev_expected = land * float(P["ev_share"]) * float(P["oil_to_electricity"])
                rows.append(dict(network=label, country=c, land_rows_2050_mwh=land, parent_2050_mwh=par, rail_child_2050_mwh=rail_tab,
                                 parent_fraction_of_land=(par / land if land else 0.0), ev_loads=len(evl), ev_annual_mwh_el=ev_net, ev_expected_mwh_el=ev_expected,
                                 ev_matches_table=bool(abs(ev_net - ev_expected) <= 1e-6 * max(1.0, ev_expected)),
                                 ev_from_parent_mwh_el=ev_net * (par / land if land else 0.0), rail_loads=len(rl), rail_annual_mwh_oil=rail_net,
                                 rail_matches_table=bool(abs(rail_net - rail_tab) <= 1e-6 * max(1.0, rail_tab)),
                                 parent_in_ev_source=bool(src[evl].str.contains(PARENT).all()) if len(evl) else None,
                                 ev_share=float(P["ev_share"]), oil_to_electricity=float(P["oil_to_electricity"]), hours=hours))
        finally:
            ds.close()
    cm.write_csv(rows, cm.TABLES / "W12_2_NETWORK_RAIL_EV_LOADS.csv")
    for r in rows:
        if r["parent_2050_mwh"] > 0:
            k = f"{r['network'].split('/')[-1].split(' ')[0]}.{r['country']}"
            ev.add(f"{k}.ev_from_parent_mwh_el", r["ev_from_parent_mwh_el"], "MWh_el/a", "EXACT", "C", r["network"],
                   "EV loads (account LandTransportEV) x parent / land rows of the ATS table")
            ev.add(f"{k}.rail_annual_mwh_oil", r["rail_annual_mwh_oil"], "MWh_oil/a", "VERIFIED", "A", r["network"], "loads with account RailNonElectric")
            ev.add(f"{k}.ev_and_rail_match_table", bool(r["ev_matches_table"] and r["rail_matches_table"]), "bool", "VERIFIED", "A", r["network"])
    return rows


def chain_part(ev: cm.Evidence):
    repo = cm.REPO
    if CHAIN.exists():
        shutil.rmtree(CHAIN)
    CHAIN.mkdir(parents=True)
    shutil.copytree(repo / "research_inputs", CHAIN / "research_inputs")
    shutil.copytree(repo / "scripts_project", CHAIN / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (CHAIN / "scripts_project/retired").mkdir(exist_ok=True)
    t = {"m08b": run("m08b_demand.py"), "s3_0": run("s3_0_industry.py")}
    repro = []
    for f in M08B_OUT + S3_OUT:
        a, b = repo / DV / f, CHAIN / DV / f
        same = a.read_bytes() == b.read_bytes()
        repro.append(dict(file=f"{DV}/{f}", repo_sha256=cm.sha256(a), copy_sha256=cm.sha256(b), identical=same))
    cm.write_csv(repro, cm.TABLES / "W12_2_CHAIN_REPRODUCTION.csv")
    ok = all(r["identical"] for r in repro)
    ev.add("chain.unmodified_reproduces_repo", ok, "bool", "VERIFIED", "A", "W12_2_CHAIN_REPRODUCTION.csv", f"{len(repro)} files byte for byte; m08b {t['m08b']:.1f} s, s3_0 {t['s3_0']:.1f} s")
    if not ok:
        raise SystemExit("STOP: unmodified scratch copy does not reproduce the repository outputs (instruction A1)")
    base = {f: pd.read_csv(CHAIN / DV / f, keep_default_na=False, dtype=str) for f in [M08B_OUT[0], M08B_OUT[1], SUMMARY]}
    # fix variant b: parent rows blanked in the D1 table (RAS seed + transport base + network)
    d1 = pd.read_csv(CHAIN / D1, keep_default_na=False, dtype=str)
    m = (d1.sector == "Transport") & (d1.account == PARENT)
    blanked = d1.loc[m, ["country", "base_2019_mwh", "value_2050_mwh"]].to_dict("records")
    d1.loc[m, ["base_2019_mwh", "value_2050_mwh"]] = ""
    d1.to_csv(CHAIN / D1, index=False, lineterminator="\n")
    t2 = {"m08b": run("m08b_demand.py"), "s3_0": run("s3_0_industry.py")}
    fix = {f: pd.read_csv(CHAIN / DV / f, keep_default_na=False, dtype=str) for f in [M08B_OUT[0], M08B_OUT[1], SUMMARY]}
    ev.add("chain.fix_b_parent_rows_blanked", len(blanked), "rows", "VERIFIED", "A", f"scratch {D1}", f"m08b {t2['m08b']:.1f} s, s3_0 {t2['s3_0']:.1f} s")
    return base, fix, repro


def compare(base: dict, fix: dict, ats_conv: float, ev: cm.Evidence):
    A0, A1 = base[M08B_OUT[0]].copy(), fix[M08B_OUT[0]].copy()
    for A in (A0, A1):
        A["v"] = num(A.value_2050_mwh); A["b"] = num(A.base_2019_mwh)
    key = ["country", "sector", "account", "carrier"]
    J = A0[key + ["b", "v", "multiplier_total"]].merge(A1[key + ["b", "v", "multiplier_total"]], on=key, suffixes=("_v3", "_fixb"))
    J["dv_mwh"] = J.v_fixb - J.v_v3
    cm.write_csv(J.to_dict("records"), cm.TABLES / "W12_2_ATS_TABLE_DIFF_FIXB.csv")
    out = []
    for c in cm.ASEAN:
        j = J[J.country == c]
        tr = j[(j.sector == "Transport") & (j.carrier != "electricity")]
        land_v3 = float(tr[tr.account.isin(LAND)].v_v3.sum()); land_b = float(tr[tr.account.isin(LAND)].v_fixb.sum())
        par = float(tr[tr.account == PARENT].v_v3.sum())
        rec = dict(country=c, parent_2019_mwh=float(tr[tr.account == PARENT].b_v3.sum()), parent_2050_mwh=par,
                   transport_fuel_2050_v3_mwh=float(tr.v_v3.sum()), transport_fuel_2050_fixb_mwh=float(tr.v_fixb.sum()),
                   m_tr_v3=float(pd.to_numeric(tr.multiplier_total_v3, errors="coerce").dropna().iloc[0]) if len(tr) else None,
                   m_tr_fixb=float(pd.to_numeric(tr[tr.account != PARENT].multiplier_total_fixb, errors="coerce").dropna().iloc[0]) if len(tr) else None,
                   # network loads implied (s2_layers formulas; ev_share 1, fcev 0, ice 0 in the v3.1 networks)
                   ev_el_v3_mwh=land_v3 * ats_conv, ev_el_fixa_mwh=(land_v3 - par) * ats_conv, ev_el_fixb_mwh=land_b * ats_conv,
                   rail_oil_v3_mwh=float(tr[tr.account == CHILD].v_v3.sum()), rail_oil_fixb_mwh=float(tr[tr.account == CHILD].v_fixb.sum()),
                   aviation_dom_v3_mwh=float(tr[tr.account == "DomesticAviationFuel"].v_v3.sum()), aviation_dom_fixb_mwh=float(tr[tr.account == "DomesticAviationFuel"].v_fixb.sum()),
                   shipping_dom_v3_mwh=float(tr[tr.account == "DomesticShippingFuel"].v_v3.sum()), shipping_dom_fixb_mwh=float(tr[tr.account == "DomesticShippingFuel"].v_fixb.sum()))
        for s in ["Residential", "Commercial", "AgricultureOthers", "Industry", "NonEnergyUse", "Transport"]:
            q = j[j.sector == s]
            rec[f"{s}_el_dv_mwh"] = float(q[q.carrier == "electricity"].dv_mwh.sum())
            rec[f"{s}_fuel_dv_mwh"] = float(q[q.carrier != "electricity"].dv_mwh.sum())
        out.append(rec)
    S0 = base[SUMMARY].set_index("country"); S1 = fix[SUMMARY].set_index("country")
    pe = [c for c in S0.columns if c.startswith("pe_")]
    for r in out:
        c = r["country"]
        if c in S0.index:
            r["T_v2_v3_mwh"] = float(num(S0.loc[[c], pe].stack()).sum()); r["T_v2_fixb_mwh"] = float(num(S1.loc[[c], pe].stack()).sum())
            r["T_v2_dv_mwh"] = r["T_v2_fixb_mwh"] - r["T_v2_v3_mwh"]
        r["ev_el_dv_fixa_mwh"] = r["ev_el_fixa_mwh"] - r["ev_el_v3_mwh"]; r["ev_el_dv_fixb_mwh"] = r["ev_el_fixb_mwh"] - r["ev_el_v3_mwh"]
    cm.write_csv(out, cm.TABLES / "W12_2_RAIL_FIX_EFFECT_BY_COUNTRY.csv")
    an0 = base[M08B_OUT[1]].set_index("country"); an1 = fix[M08B_OUT[1]].set_index("country")
    cols = [c for c in an0.columns if c.endswith("_mwh") or c.endswith("multiplier")]
    arow = []
    for c in an0.index:
        for k in cols:
            x0, x1 = pd.to_numeric(an0.at[c, k], errors="coerce"), pd.to_numeric(an1.at[c, k], errors="coerce")
            if pd.notna(x0) and pd.notna(x1) and abs(x1 - x0) > 1e-6 * max(1.0, abs(x0)):
                arow.append(dict(country=c, field=k, v3=float(x0), fix_b=float(x1), diff=float(x1 - x0)))
    cm.write_csv(arow, cm.TABLES / "W12_2_ANCHOR_CHANGES_FIXB.csv", ["country", "field", "v3", "fix_b", "diff"])
    for r in out:
        if r["parent_2050_mwh"] > 0 or abs(r.get("T_v2_dv_mwh", 0.0)) > 1:
            ev.add(f"{r['country']}.parent_2050_mwh", r["parent_2050_mwh"], "MWh_oil-eq/a", "VERIFIED", "A", f"{ATS} (worktree)", "TransportEmbeddedFuelParent value_2050_mwh")
            ev.add(f"{r['country']}.ev_el_dv_fixa_mwh", r["ev_el_dv_fixa_mwh"], "MWh_el/a", "EXACT", "C", "W12_2_RAIL_FIX_EFFECT_BY_COUNTRY.csv", "variant a: parent dropped from land transport only")
            ev.add(f"{r['country']}.ev_el_dv_fixb_mwh", r["ev_el_dv_fixb_mwh"], "MWh_el/a", "EXACT", "C", "scratch m08b re-run", "variant b: parent blanked in D1 (RAS seed + base + network)")
            ev.add(f"{r['country']}.rail_oil_dv_fixb_mwh", r["rail_oil_fixb_mwh"] - r["rail_oil_v3_mwh"], "MWh_oil/a", "EXACT", "C", "scratch m08b re-run")
            ev.add(f"{r['country']}.T_v2_dv_fixb_mwh", r.get("T_v2_dv_mwh"), "MWh/a", "EXACT", "C", "scratch s3_0 re-run", "sum pe_* of " + SUMMARY)
    return out, arow


def main():
    ev = cm.Evidence("W12_2")
    tabs = {}
    for f in (D1, ATS):
        d = pd.read_csv(cm.REPO / f, keep_default_na=False, dtype=str)
        tabs[f] = d
    rows = []
    for f, d in tabs.items():
        q = d[(d.sector == "Transport") & d.account.isin([PARENT, CHILD])]
        for r in q.itertuples():
            rows.append(dict(table=f, table_sha256=cm.sha256(cm.REPO / f), country=r.country, account=r.account, carrier=r.carrier, base_2019_mwh=r.base_2019_mwh,
                             value_2050_mwh=r.value_2050_mwh, multiplier_total=r.multiplier_total))
    cm.write_csv(rows, cm.TABLES / "W12_2_RAIL_ROWS_DEMAND_TABLES.csv")
    ats = tabs[ATS]
    for c in cm.ASEAN:
        a = ats[(ats.country == c) & (ats.sector == "Transport")]
        p19, c19 = float(num(a[a.account == PARENT].base_2019_mwh).sum()), float(num(a[a.account == CHILD].base_2019_mwh).sum())
        if p19 > 0:
            ev.add(f"{c}.parent_2019_mwh", p19, "MWh/a", "VERIFIED", "A", f"{ATS}", "TransportEmbeddedFuelParent base_2019_mwh")
            ev.add(f"{c}.child_2019_mwh", c19, "MWh/a", "VERIFIED", "A", f"{ATS}", "RailNonElectric base_2019_mwh (all carriers)")
    netrows = network_part(ev, ats, {})
    base, fix, repro = chain_part(ev)
    conv = float(pd.DataFrame(netrows).oil_to_electricity.iloc[0]) * float(pd.DataFrame(netrows).ev_share.iloc[0])
    out, arow = compare(base, fix, conv, ev)
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    N = pd.DataFrame(netrows)
    print(N[N.parent_2050_mwh > 0][["network", "country", "parent_2050_mwh", "parent_fraction_of_land", "ev_annual_mwh_el", "ev_matches_table", "ev_from_parent_mwh_el",
                                    "rail_annual_mwh_oil", "rail_matches_table", "parent_in_ev_source"]].to_string())
    print(pd.DataFrame(repro)[["file", "identical"]].to_string())
    O = pd.DataFrame(out)
    print(O[["country", "parent_2050_mwh", "m_tr_v3", "m_tr_fixb", "transport_fuel_2050_v3_mwh", "transport_fuel_2050_fixb_mwh", "ev_el_dv_fixa_mwh", "ev_el_dv_fixb_mwh",
             "rail_oil_v3_mwh", "rail_oil_fixb_mwh", "T_v2_dv_mwh"]].to_string())
    print(O[[c for c in O.columns if c.endswith("_dv_mwh")] + ["country"]].round(1).to_string())
    print(pd.DataFrame(arow).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
