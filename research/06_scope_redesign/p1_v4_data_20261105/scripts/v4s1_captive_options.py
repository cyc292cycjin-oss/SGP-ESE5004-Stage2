"""V4 S1 section 1 item 8: options for the captive coal C (quantified only, nothing is implemented).

    PYTHONHASHSEED=0 python scripts/v4s1_captive_options.py --work <work dir> --repo /home/jin/wt_v4_data --chain /home/jin/v4s1/chain_captive

(a) status quo: T_v2 unchanged, the captive coal is only listed in the difference table.
(b) UNSD 2019 base: C leaves the ID industry coal ('other' row of the UNSD split and the D1 base), eta*C enters as industry electricity
    ('other' row and D1 base), the ATS industry multiplier is kept (growth anchor unchanged), the data chain s3_0_industry.py runs again and
    the v3 decomposition (v3_industry.decompose + non-ferrous + D163-6 a conservation) is applied to the new ID row.
(c) sensitivity only: the numbers of (b), used as a sensitivity case and not in the main case.
How: the repository data chain (research_inputs + scripts_project) is copied once to a scratch directory OUTSIDE the repository (as v3_industry
.run_vn_chain does for VN); for every case the two input files are restored and edited there and s3_0_industry.py is run in the copy.
An unmodified run must reproduce the repository ID row exactly (T_v2 and the v3 'other' bucket) before any case is used.
C and eta*C per level come from s1/ID_CAPTIVE_COAL_2019.csv (coal still in the industry row, model coal factor; generation that belongs to it).
Output s1/ID_CAPTIVE_OPTIONS.csv and s1/_captive_options_evidence.json. Nothing is solved; the repository is not written.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s1_common as cm   # noqa: E402

SUMMARY = "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv"
OUTC = ("electricity", "heat", "heat_medium_a", "heat_medium_b", "heat_high", "coal", "oil", "gas", "biomass", "hydrogen", "ammonia", "methanol")
CARS19 = ("coal", "oil", "gas", "biomass", "electricity")


def copy_chain(repo: Path, chain: Path):
    if chain.exists():
        shutil.rmtree(chain)
    chain.mkdir(parents=True)
    shutil.copytree(repo / "research_inputs", chain / "research_inputs")
    shutil.copytree(repo / "scripts_project", chain / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (chain / "scripts_project/retired").mkdir(exist_ok=True)


def run_case(chain: Path, orig: dict, c_mwh: float, e_mwh: float):
    """Restore the two inputs, move C (MWh, model coal basis) from ID industry coal to e_mwh industry electricity, run s3_0_industry.py."""
    cp = chain / "research_inputs/assembly_v1/sources/industry_cache.json"
    dp = chain / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv"
    cp.write_bytes(orig["cache"]); dp.write_bytes(orig["demand"])
    if c_mwh or e_mwh:
        cache = json.loads(orig["cache"])
        for r in cache["records"]:
            if r["country"] == "ID" and r["carrier"] == "coal":
                r["other"] = repr(float(r["other"]) - c_mwh)
            if r["country"] == "ID" and r["carrier"] == "electricity":
                r["other"] = repr(float(r["other"]) + e_mwh)
        cp.write_text(json.dumps(cache))
        d = pd.read_csv(dp, keep_default_na=False, dtype=str)
        for car, dv in (("coal", -c_mwh), ("electricity", e_mwh)):
            m = (d.country == "ID") & (d.sector == "Industry") & (d.carrier == car)
            if m.sum() != 1:
                raise ValueError(f"ID Industry {car}: {m.sum()} rows")
            b = float(d.loc[m, "base_2019_mwh"].iloc[0]) + dv
            d.loc[m, "base_2019_mwh"] = repr(b)
            d.loc[m, "value_2050_mwh"] = repr(b * float(d.loc[m, "multiplier_total"].iloc[0]))
        d.to_csv(dp, index=False)
    r = subprocess.run([sys.executable, "s3_0_industry.py"], cwd=chain / "scripts_project", capture_output=True, text=True,
                       env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"})
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])
    s = pd.read_csv(chain / "research_inputs/demand_v5" / SUMMARY).set_index("country")
    ob = pd.read_csv(chain / "research_inputs/demand_v5/INDUSTRY_2050_OTHER_BUCKET.csv")
    ob = ob[(ob["mode"] == "aeo8_ats_anchor") & (ob.country == "ID")].iloc[0]
    return s.loc["ID"], ob


def v3_id(v3, row, fut, nf):
    T = float(sum(row[v3.col(x)] for x in v3.CARRIERS))
    parts = v3.decompose(row, fut); parts.update(nf)
    expl = sum(sum(v.values()) for k, v in parts.items() if k != "other")
    so = sum(parts["other"].values()); f = (T - expl) / so
    other = {k: v * f for k, v in parts["other"].items()}
    return T, other, f, expl


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); ap.add_argument("--repo", type=Path, default=cm.REPO)
    ap.add_argument("--chain", type=Path, default=Path("/home/jin/v4s1/chain_captive")); a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402  (ROOT = repository worktree)
    fut = v3.future_vectors(); ne = v3.nickel_unit_energy()
    nf = v3.nonferrous(fut, "main", ne)[0]["ID"]
    E = pd.read_csv(a.work / "s1/ID_CAPTIVE_COAL_2019.csv")
    tot = E[E.group == "合计"].set_index("level")
    OV = pd.read_csv(a.work / "s1/ID_CAPTIVE_V3_OVERLAP.csv")
    copy_chain(a.repo, a.chain)
    orig = {"cache": (a.repo / "research_inputs/assembly_v1/sources/industry_cache.json").read_bytes(),
            "demand": (a.repo / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv").read_bytes()}
    # ---- reproduction check -------------------------------------------------------------------------------------------------
    repo_row = pd.read_csv(a.repo / "research_inputs/demand_v5" / SUMMARY).set_index("country").loc["ID"]
    base_row, base_ob = run_case(a.chain, orig, 0.0, 0.0)
    dev = max(abs(float(base_row[v3.col(x)]) - float(repo_row[v3.col(x)])) for x in v3.CARRIERS)
    T0, other0, f0, expl0 = v3_id(v3, base_row, fut, nf)
    sub = pd.read_csv(a.repo / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    sub = sub[(sub.case == "main") & (sub.country == "ID") & (sub.subsector == "other")].set_index("carrier").mwh_2050
    dev_v3 = max(abs(other0.get(k, 0.0) - float(sub.get(k, 0.0))) for k in other0)
    if dev > 1e-3 or dev_v3 > 1e-3:
        raise ValueError(f"unmodified chain does not reproduce the repository: T dev {dev} MWh, v3 other dev {dev_v3} MWh")
    dem = pd.read_csv(a.repo / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    did = dem[(dem.country == "ID") & (dem.sector == "Industry")]
    mult = float(did.multiplier_total.astype(float).iloc[0])
    e19_0 = float(did.base_2019_mwh.astype(float).sum())
    ev = dict(reproduction=dict(max_abs_dev_T_carriers_mwh=dev, max_abs_dev_v3_other_mwh=dev_v3, T_v2_id_twh=T0 / 1e6, v3_other_id_twh=sum(other0.values()) / 1e6,
                                other_scale=f0, explicit_twh=expl0 / 1e6, multiplier=mult, e19_id_twh=e19_0 / 1e6,
                                relation="T_v2(ID) = s3_0_industry route conversion of (D1 2019 base by carrier x ATS industry multiplier); multiplier = RAS industry energy-use anchor / 2019 industry energy use (m08b_demand.py lines 6-17, growth_method column); steel / cement / ammonia 2050 tonnes from the output rule"),
              cases={})
    dc_a = OV[OV.v3_subsector.isin(["nickel", "alumina", "cement", "steel"])].groupby("level").double_count_2050_twh.sum().to_dict()
    rows = []

    def record(option, level, C, Eel, row, ob, label):
        T, other, f, expl = v3_id(v3, row, fut, nf)
        e19 = e19_0 - C + Eel
        r = dict(option=option, level=level, label=label, captive_coal_removed_2019_twh=C / 1e6, captive_electricity_added_2019_twh=Eel / 1e6,
                 eta_model=(Eel / C if C else None), id_industry_2019_twh=e19 / 1e6, delta_industry_2019_twh=(e19 - e19_0) / 1e6,
                 other_2019_v2_twh=float(ob.other_2019_mwh) / 1e6, other_2019_v3eq_twh=float(ob.other_2019_mwh) * f / 1e6,
                 T_2050_twh=T / 1e6, delta_T_2050_twh=(T - T0) / 1e6, other_2050_v3_twh=sum(other.values()) / 1e6,
                 delta_other_2050_twh=(sum(other.values()) - sum(other0.values())) / 1e6, other_scale=f, explicit_2050_twh=expl / 1e6)
        for k in OUTC:
            r[f"delta_other_2050_{k}_twh"] = (other.get(k, 0.0) - other0.get(k, 0.0)) / 1e6
        for k in CARS19:
            r[f"other_2019_{k}_twh"] = float(ob[f"other_2019_{k}_mwh"]) / 1e6
        r["double_count_2050_explicit_twh"] = (dc_a.get(level, 0.0) if option == "a" else 0.0)
        rows.append(r)

    for lv in ("low", "central", "mid", "high"):
        record("a", lv, 0.0, 0.0, base_row, base_ob, "维持现状：T_v2 不变，自备用煤只记入差异表")
    for lv in ("low", "central", "mid", "high"):
        C = float(tot.at[lv, "coal_in_industry_twh_model"]) * 1e6
        Eel = float(tot.at[lv, "gen_in_industry_gwh"]) * 1e3
        row, ob = run_case(a.chain, orig, C, Eel)
        record("b", lv, C, Eel, row, ob, "UNSD 2019 基年移出 C、记入 η·C 工业用电；ATS 工业倍数不变")
        record("c", lv, C, Eel, row, ob, "只作敏感性：数值同 (b)，主算不变")
        ev["cases"][lv] = dict(C_twh=C / 1e6, E_twh=Eel / 1e6)
    run_case(a.chain, orig, 0.0, 0.0)   # leave the scratch copy unmodified
    O = pd.DataFrame(rows)
    O.to_csv(a.work / "s1/ID_CAPTIVE_OPTIONS.csv", index=False, float_format="%.6f")
    ev["options"] = O.drop(columns=["label"]).to_dict("records")
    (a.work / "s1/_captive_options_evidence.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(json.dumps(ev["reproduction"], indent=0, default=float)[:900])
    print(O[O.option != "c"][["option", "level", "captive_coal_removed_2019_twh", "captive_electricity_added_2019_twh", "eta_model", "delta_industry_2019_twh", "other_2019_v3eq_twh",
                              "T_2050_twh", "delta_T_2050_twh", "other_2050_v3_twh", "delta_other_2050_twh", "double_count_2050_explicit_twh"]].round(3).to_string())
    print(O[O.option == "b"][["level"] + [f"delta_other_2050_{k}_twh" for k in OUTC if k not in ("ammonia", "methanol", "hydrogen")]].round(3).to_string())


if __name__ == "__main__":
    main()
