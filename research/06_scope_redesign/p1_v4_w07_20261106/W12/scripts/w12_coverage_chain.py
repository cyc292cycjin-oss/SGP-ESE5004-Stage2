"""W12-4 (b): model effect of the coverage gaps under the actual demand chain (reading II: AEO8 ATS anchors, m08b RAS re-solved), in the
scratch copy /home/jin/v4w07_w12/chain. The unmodified copy must reproduce the repository m08b + s3_0 outputs byte for byte first.

Cases (2019 MWh added to base_2019_mwh of the D1 ratio table, rows that exist only; tables/W12_4_MISSING_BY_COUNTRY_SECTOR_COMMODITY.csv):
  A  all SDMX-missing end-use quantities except industry 'Other Vegetal Material and Residues' (closed-loop residues, decision 206 item 3)
  B  VN diesel outside industry only (road, agriculture, commerce; the G2 hand-over; VN industry diesel is G2's case)
Reading I (multiplier unchanged) is in tables/W12_4_MODEL_SCALE_READING_I.csv. Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402

CHAIN = Path("/home/jin/v4w07_w12/chain")
DV = "research_inputs/demand_v5"
D1 = f"{DV}/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
ATS = "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
OUTS = [ATS, "DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_OUTPUT_BASE_M08B.csv", "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", SUMMARY,
        "INDUSTRY_2050_OTHER_BUCKET.csv", "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]
ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"}
CAR = {"biomass": "biomass", "oil": "oil", "gas": "gas", "coal": "coal"}


def run(script: str) -> float:
    t = time.time()
    r = subprocess.run([sys.executable, script], cwd=CHAIN / "scripts_project", capture_output=True, text=True, env=ENV)
    if r.returncode:
        raise RuntimeError(f"{script}: {r.stderr[-3000:]}")
    return time.time() - t


def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def snapshot():
    a = pd.read_csv(CHAIN / DV / ATS, keep_default_na=False, dtype=str); a["v"] = num(a.value_2050_mwh); a["b"] = num(a.base_2019_mwh)
    s = pd.read_csv(CHAIN / DV / SUMMARY, keep_default_na=False, dtype=str).set_index("country")
    pe = [c for c in s.columns if c.startswith("pe_")]
    t = {c: float(num(s.loc[c, pe]).sum()) for c in s.index}
    return a, t


def main():
    ev = cm.Evidence("W12_4b")
    if CHAIN.exists():
        shutil.rmtree(CHAIN)
    CHAIN.mkdir(parents=True)
    shutil.copytree(cm.REPO / "research_inputs", CHAIN / "research_inputs")
    shutil.copytree(cm.REPO / "scripts_project", CHAIN / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (CHAIN / "scripts_project/retired").mkdir(exist_ok=True)
    orig = (CHAIN / D1).read_bytes()
    run("m08b_demand.py"); run("s3_0_industry.py")
    ok = all((cm.REPO / DV / f).read_bytes() == (CHAIN / DV / f).read_bytes() for f in OUTS)
    ev.add("chain.unmodified_reproduces_repo", ok, "bool", "VERIFIED", "A", "scratch /home/jin/v4w07_w12/chain", f"{len(OUTS)} files byte for byte")
    if not ok:
        raise SystemExit("STOP: unmodified scratch copy does not reproduce the repository outputs (instruction A1)")
    A0, T0 = snapshot()
    miss = pd.read_csv(cm.TABLES / "W12_4_MISSING_BY_COUNTRY_SECTOR_COMMODITY.csv")
    miss = miss[miss.fuel_group.isin(list(CAR)) & (miss.d1_account != "NonEnergy")]
    cases = {"A_all_except_industry_closed_loop": miss[~((miss.d1_account == "IndustryFinalEnergy") & (miss.commodity == "Other Vegetal Material and Residues"))],
             "B_VN_diesel_outside_industry": miss[(miss.cc == "VN") & (miss.commodity == "Gas Oil/ Diesel Oil") & (miss.d1_account != "IndustryFinalEnergy")]}
    rows, applied = [], []
    for case, m in cases.items():
        (CHAIN / D1).write_bytes(orig)
        d1 = pd.read_csv(CHAIN / D1, keep_default_na=False, dtype=str)
        g = m.groupby(["cc", "d1_account", "fuel_group"]).tj.sum().reset_index()
        for r in g.itertuples():
            k = (d1.country == r.cc) & (d1.account == r.d1_account) & (d1.carrier == CAR[r.fuel_group])
            add = r.tj / 0.0036
            if k.sum() != 1 or d1.loc[k, "value_2050_mwh"].iloc[0] == "":
                applied.append(dict(case=case, country=r.cc, account=r.d1_account, carrier=CAR[r.fuel_group], add_mwh=add, applied=False, reason=f"{int(k.sum())} rows / blank 2050"))
                continue
            d1.loc[k, "base_2019_mwh"] = repr(float(d1.loc[k, "base_2019_mwh"].iloc[0]) + add)
            applied.append(dict(case=case, country=r.cc, account=r.d1_account, carrier=CAR[r.fuel_group], add_mwh=add, applied=True, reason=""))
        d1.to_csv(CHAIN / D1, index=False, lineterminator="\n")
        run("m08b_demand.py"); run("s3_0_industry.py")
        A1, T1 = snapshot()
        key = ["country", "sector", "account", "carrier"]
        J = A0[key + ["v"]].merge(A1[key + ["v"]], on=key, suffixes=("_v3", "_case"))
        for c in cm.ASEAN:
            j = J[J.country == c]
            rec = dict(case=case, country=c, T_v2_v3_twh=T0.get(c, 0.0) / 1e6, T_v2_case_twh=T1.get(c, 0.0) / 1e6, T_v2_dv_twh=(T1.get(c, 0.0) - T0.get(c, 0.0)) / 1e6)
            for s in ["Residential", "Commercial", "AgricultureOthers", "Transport", "Industry", "NonEnergyUse"]:
                q = j[j.sector == s]
                rec[f"{s}_2050_dv_twh"] = float((q.v_case - q.v_v3).sum()) / 1e6
                for car in ("oil", "biomass", "electricity"):
                    qq = q[q.carrier == car]
                    if len(qq):
                        rec[f"{s}_{car}_dv_twh"] = float((qq.v_case - qq.v_v3).sum()) / 1e6
            rows.append(rec)
        (CHAIN / D1).write_bytes(orig)
    cols = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("case", "country"), k))
    cm.write_csv(rows, cm.TABLES / "W12_4_CHAIN_READING_II.csv", cols)
    cm.write_csv(applied, cm.TABLES / "W12_4_CHAIN_APPLIED_ROWS.csv")
    for r in rows:
        if abs(r["T_v2_dv_twh"]) > 0.05 or abs(r.get("Transport_2050_dv_twh", 0)) > 0.05 or abs(r.get("Residential_2050_dv_twh", 0)) > 0.05:
            ev.add(f"{r['case']}.{r['country']}", {k: v for k, v in r.items() if k.endswith("_dv_twh")}, "TWh (2050)", "EXACT", "C", "scratch m08b + s3_0 re-run (reading II)")
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    R = pd.DataFrame(rows)
    print(pd.DataFrame(applied).to_string())
    print(R[["case", "country", "T_v2_dv_twh", "Residential_2050_dv_twh", "Commercial_2050_dv_twh", "AgricultureOthers_2050_dv_twh", "Transport_2050_dv_twh",
             "Industry_2050_dv_twh", "NonEnergyUse_2050_dv_twh"]].round(3).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
