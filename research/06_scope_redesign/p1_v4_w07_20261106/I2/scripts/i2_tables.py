"""I2 sections 2-3: tables and figures from the scratch results of i2_chain.py (/home/jin/v4i2/results/*.json).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_tables.py

Writes <CC>_V4_FINAL.csv (11 countries; record_type step / subsector / node / anchor), ASEAN_V4_SUMMARY.csv, tables/I2_STEPS_LONG.csv,
tables/I2_NODE_SHARES_BY_STEP.csv, tables/I2_ADDITIVITY.csv, tables/I2_AEO8_DEVIATION.csv, tables/I2_SENSITIVITY_RUNS.csv,
tables/I2_DEDUCTION_LOG.csv, tables/I2_V4_SUBSECTOR_CARRIER.csv (v3-table format, input of the curve weights), tables/I2_V4_DISPERSED_BY_UNSD_ROW.csv,
figures/fig_i2_*.png, evidence/I2_tables.json.
Node shares: carrier node shares = sum over sub-sectors of 2050 energy x the sub-sector node shares (v3_facility_shares.py rule: v3
INDUSTRY_NODE_SHARES_V3.csv, ammonia on the national v2 shares); new or re-located sub-sectors use the session shares (<CC>_NODE_SHARES.csv,
share_v4). Gate: at S0 the rule reproduces INDUSTRY_CARRIER_NODE_SHARES_V3.csv (case main).
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402

R = cm.SCRATCH / "results"
STEPS = ["S0", "S1", "S2", "S3", "S4", "S5a", "S5b", "S5c", "S5d", "S5e", "S5f", "S5g", "S6a", "S6b", "S6c", "S7"]
CC = ["ID", "VN", "TH", "MY", "PH", "SG", "MM", "KH", "LA", "BN", "TL"]
SEC = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
GRADE = {"S0": ("EXACT", "B/C"), "S1": ("PROPOSED (quantified)", "A/B"), "S2": ("PROPOSED (quantified)", "B/C"), "S3": ("PROPOSED (quantified)", "B"),
         "S4": ("PROPOSED (quantified)", "C"), "S5a": ("PROPOSED (quantified)", "B/C"), "S5b": ("PROPOSED (quantified)", "C"), "S5c": ("PROPOSED (quantified)", "B/C"),
         "S5d": ("PROPOSED (quantified)", "C"), "S5e": ("PROPOSED (quantified)", "C"), "S5f": ("PROPOSED (quantified)", "C"), "S5g": ("PROPOSED (quantified)", "C"),
         "S6a": ("PROPOSED (quantified)", "C"), "S6b": ("PROPOSED (quantified)", "C"), "S6c": ("PROPOSED (quantified)", "C"), "S7": ("PROPOSED (quantified)", "C")}


def load(name):
    return json.loads((R / f"{name}.json").read_text())


# ===================================================================================================================== node shares
class Nodes:
    SESSION_FILES = {"ID": "G0/ID_NODE_SHARES.csv", "MY": "G1/MY_NODE_SHARES.csv", "VN": "G2/VN_NODE_SHARES.csv", "TH": "G3/TH_NODE_SHARES.csv",
                     "PH": "G3/PH_NODE_SHARES.csv", "SG": "G3/SG_NODE_SHARES.csv", "MM": "G4/MM_NODE_SHARES.csv", "KH": "G4/KH_NODE_SHARES.csv",
                     "LA": "G4/LA_NODE_SHARES.csv", "BN": "G4/BN_NODE_SHARES.csv"}
    # parts key -> session sub-sector name (first match wins), per country
    SESSION_KEY = {"steel": ["steel"], "cement": ["cement"], "pulp_paper": ["pulp_paper", "pulp and paper", "MM_paper", "LA_pulp"],
                   "pulp_paper_new_lines": ["pulp_paper", "pulp and paper", "LA_pulp"], "hvc": ["ethylene", "hvc", "ethylene (HVC)"],
                   "hvc_new_plants": ["ethylene", "hvc", "ethylene (HVC)"], "methanol": ["methanol"], "glass": ["glass"], "alumina": ["alumina"],
                   "copper": ["MM_copper", "LA_copper"], "lime": ["lime"]}
    MY_OTHER = {"electricity": "other (electricity), proposal", "_": "other (heat bands and oil), proposal A"}   # G1 item 7 (decision 208: Sabah by NEB regions)

    def __init__(self):
        S = pd.read_csv(cm.IND_V3 / "INDUSTRY_NODE_SHARES_V3.csv")
        self.v3 = {(r.country, r.subsector): {} for r in S.itertuples()}
        for r in S.itertuples():
            self.v3[(r.country, r.subsector)][r.node] = float(r.share)
        A = pd.read_csv(cm.IND_V3 / "INDUSTRY_NODE_ALLOCATION_V2_V3.csv")
        self.base = {}
        for c, g in A.groupby("country"):
            t = g.v2_twh.sum(); self.base[c] = {r.node: float(r.v2_twh) / t for r in g.itertuples() if t > 0}
        self.sess = {}
        for c, f in self.SESSION_FILES.items():
            t = pd.read_csv(cm.W07 / f)
            for s, g in t.groupby("subsector"):
                w = {r.node: float(r.share_v4) for r in g.itertuples() if pd.notna(r.share_v4) and float(r.share_v4) > 0}
                tot = sum(w.values())
                if tot > 0:
                    self.sess[(c, s)] = {k: v / tot for k, v in w.items()}

    def shares(self, c, key, car, v3_only=False):
        if car == "ammonia" or key == "ammonia":
            return self.base[c], "v2 national (ammonia, v3 rule)"
        if not v3_only:
            if c == "MY" and key == "other":
                k = self.MY_OTHER["electricity" if car == "electricity" else "_"]
                if (c, k) in self.sess:
                    return self.sess[(c, k)], f"G1 {k}"
            if c == "MY" and key == "methanol_new_plants":
                return {"MY_Sarawak4 0": 1.0}, "Sarawak Petchem Bintulu -> MY_Sarawak4 0 (G1 ABF node, INFERENCE)"
            for s in self.SESSION_KEY.get(key, []):
                if (c, s) in self.sess:
                    return self.sess[(c, s)], f"session {s}"
            if key in ("methanol",) and (c, "petrochem") in self.v3:
                return self.v3[(c, "petrochem")], "v3 petrochem (INFERENCE)"
            if key in ("hvc", "hvc_new_plants") and (c, "petrochem") in self.v3:
                return self.v3[(c, "petrochem")], "v3 petrochem"
        if (c, key) in self.v3:
            return self.v3[(c, key)], f"v3 {key}"
        if (c, "dispersed") in self.v3 and not v3_only:
            return self.v3[(c, "dispersed")], "v3 dispersed (fallback)"
        return self.base[c], "v2 national (fallback)"

    def allocate(self, c, parts, v3_only=False):
        """{carrier: {node: MWh}} and the source of every part."""
        out, src = {}, {}
        for k, v in parts.items():
            for car, x in v.items():
                if abs(x) <= 0:
                    continue
                sh, s = self.shares(c, k, car, v3_only); src[k] = s
                d = out.setdefault(car, {})
                for n, f in sh.items():
                    d[n] = d.get(n, 0.0) + x * f
        return out, src


def norm(d):
    t = sum(d.values()); return {k: v / t for k, v in d.items()} if t else {}


# ===================================================================================================================== main
def main():
    ev = cm.Evidence("I2_tables")
    D = {s: load(f"step_{s}") for s in STEPS}
    meta = load("meta")
    an0 = pd.read_csv(cm.DEMAND / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    v3a = json.loads((cm.SCRATCH / "anchors_v3_ras.json").read_text())
    C3 = {s: sum(v3a["tfa"][c][s] for c in cm.ASEAN10) for s in SEC}   # = C.3 ATS 2050 x k (RAS column targets)
    # ---------------------------------------------------------------------------------------------- long table
    rows = []
    for s in STEPS:
        d = D[s]
        for c in CC:
            x = d["countries"][c]; a = d["ats_sectors"][c]
            r = dict(step=s, label=d["label"].split(" ", 1)[1] if " " in d["label"] else d["label"], country=c, T_v2_2050_TWh=x["T"] / 1e6, other_2050_TWh=x["other"] / 1e6,
                     other_share=x["share"], industry_2019_TWh=x["ind19_true"] / 1e6, industry_anchor_2050_TWh=x["ind_anchor"] / 1e6, industry_multiplier=x["ind_mult"],
                     ats_industry_2050_TWh=x["ind50_ats"] / 1e6, products_2050_TWh=x["prod50"] / 1e6, implied_industry_fe_2050_TWh=(x["ind50_ats"] + x["prod50"]) / 1e6,
                     aeo8_national_tfec_2050_TWh=float(an0.at[c, "ats_tfec_2050_mwh"]) / 1e6, v3_industry_anchor_TWh=float(an0.at[c, "industry_anchor_mwh"]) / 1e6,
                     transport_2050_TWh=a["sec2050"]["Transport"] / 1e6, residential_2050_TWh=a["sec2050"]["Residential"] / 1e6, commercial_2050_TWh=a["sec2050"]["Commercial"] / 1e6,
                     agriculture_2050_TWh=a["sec2050"]["AgricultureOthers"] / 1e6, neu_2050_TWh=a["sec2050"]["NonEnergyUse"] / 1e6, land_fuel_2050_TWh=a["land"] / 1e6,
                     ev_electricity_2050_TWh=a["ev"] / 1e6, residential_fuel_2050_TWh=a["resf"] / 1e6, rail_parent_2050_TWh=a["rail_parent"] / 1e6,
                     biomass_before_overflow_TWh=x["bio_before"] / 1e6, biomass_overflow_TWh=x["overflow"] / 1e6, solid_potential_cap_TWh=x["pot"] / 1e6,
                     s30_not_found_2019_TWh=x["s30_not_found"] / 1e6, methanol_dropped_2050_TWh=x["meoh_dropped"] / 1e6)
            r["national_model_2050_TWh"] = r["implied_industry_fe_2050_TWh"] + r["transport_2050_TWh"] + r["residential_2050_TWh"] + r["commercial_2050_TWh"] + r["agriculture_2050_TWh"]
            for k, col in cm.COLMAP.items():
                r[f"T_{col}"] = x["T_car"].get(k, 0.0) / 1e6
            for k, col in cm.COLMAP.items():
                r[f"other_{col}"] = x["other_car"].get(k, 0.0) / 1e6
            r["status"], r["grade"] = GRADE[s]
            rows.append(r)
    L = pd.DataFrame(rows)
    num = [c for c in L.columns if L[c].dtype != object and c not in ("other_share", "industry_multiplier")]
    A = L.groupby("step", sort=False)[num].sum().reset_index(); A["country"] = "ASEAN11"; A["label"] = L.groupby("step", sort=False).label.first().values
    A["other_share"] = A.other_2050_TWh / A.T_v2_2050_TWh; A["status"] = [GRADE[s][0] for s in A.step]; A["grade"] = [GRADE[s][1] for s in A.step]
    L = pd.concat([L, A], ignore_index=True)
    L["delta_T_TWh"] = L.groupby("country").T_v2_2050_TWh.diff().fillna(0.0)
    L["delta_other_TWh"] = L.groupby("country").other_2050_TWh.diff().fillna(0.0)
    v3T = L[L.step == "S0"].set_index("country").T_v2_2050_TWh; v3O = L[L.step == "S0"].set_index("country").other_2050_TWh
    L["cum_delta_T_vs_v3_TWh"] = L.T_v2_2050_TWh - L.country.map(v3T); L["cum_delta_other_vs_v3_TWh"] = L.other_2050_TWh - L.country.map(v3O)
    L["dev_industry_vs_v3_anchor_pct"] = (L.implied_industry_fe_2050_TWh / L.v3_industry_anchor_TWh - 1) * 100
    L["dev_national_vs_aeo8_pct"] = (L.national_model_2050_TWh / L.aeo8_national_tfec_2050_TWh - 1) * 100
    L.to_csv(cm.TABLES / "I2_STEPS_LONG.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- node shares
    N = Nodes()
    ref = pd.read_csv(cm.IND_V3 / "INDUSTRY_CARRIER_NODE_SHARES_V3.csv"); ref = ref[ref.case == "main"]
    dev = 0.0
    for c in CC:
        if not D["S0"]["countries"][c]["parts"]:
            continue
        al, _ = N.allocate(c, D["S0"]["countries"][c]["parts"], v3_only=True)
        for car, dd in al.items():
            sh = norm(dd); rr = ref[(ref.country == c) & (ref.carrier == car)].set_index("node").share
            for n in set(sh) | set(rr.index):
                dev = max(dev, abs(sh.get(n, 0.0) - float(rr.get(n, 0.0))))
    ev.add("gate.node_rule_reproduces_v3_carrier_node_shares", dev, "max abs share difference", "EXACT", "-", "INDUSTRY_CARRIER_NODE_SHARES_V3.csv (case main) vs the I2 rule at S0")
    if dev > 1e-9:
        print("WARNING node gate", dev)
    nrows, srcs = [], {}
    for s in STEPS:
        for c in CC:
            parts = D[s]["countries"][c]["parts"]
            if not parts:
                continue
            al, src = N.allocate(c, parts, v3_only=(s == "S0")); srcs[(s, c)] = src
            tot = {}
            for car, dd in al.items():
                for n, x in dd.items():
                    tot[n] = tot.get(n, 0.0) + x
            T = sum(tot.values()); el = al.get("electricity", {}); E = sum(el.values())
            for n in sorted(tot):
                nrows.append(dict(step=s, country=c, node=n, T_v2_2050_TWh=tot[n] / 1e6, share_T=tot[n] / T if T else 0.0, electricity_2050_TWh=el.get(n, 0.0) / 1e6,
                                  share_electricity=el.get(n, 0.0) / E if E else 0.0))
    NS = pd.DataFrame(nrows); NS.to_csv(cm.TABLES / "I2_NODE_SHARES_BY_STEP.csv", index=False, float_format="%.6f", lineterminator="\n")
    cm.write_json({f"{s}|{c}": v for (s, c), v in srcs.items() if s == "S7"}, cm.EVID / "I2_node_share_sources_S7.json")
    # ---------------------------------------------------------------------------------------------- composition for the curve weights (v3-table format)
    comp = []
    for c in CC:
        for k, v in D["S7"]["countries"][c]["parts"].items():
            for car, x in v.items():
                if abs(x) > 0:
                    comp.append(dict(case="main", country=c, subsector=k, carrier=car, mwh_2050=x))
    pd.DataFrame(comp).to_csv(cm.TABLES / "I2_V4_SUBSECTOR_CARRIER.csv", index=False, float_format="%.6f", lineterminator="\n")
    pzd = pd.DataFrame(D["S7"]["pz_dispersed"]); pzd = pzd[~pzd.unsd_row.isin(["other", "construction", "mining and quarrying"])]   # other bucket is not dispersed
    pzd["twh_2050"] = pzd.mwh_2050 / 1e6; pzd["basis"] = "I2 final (SDMX, IId; VN hybrid same run)"
    pzd[["country", "unsd_row", "pypsa_eur_sector", "mwh_2019", "twh_2050", "basis"]].to_csv(cm.TABLES / "I2_V4_DISPERSED_BY_UNSD_ROW.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- additivity
    S1 = L[L.step == "S1"].set_index("country"); S0 = L[L.step == "S0"].set_index("country"); S7 = L[L.step == "S7"].set_index("country")
    add = []
    singles = {s: load(f"single_{s}") for s in STEPS[2:]}
    for c in CC + ["ASEAN11"]:
        g = lambda d, k: (sum(d["countries"][x][k] for x in CC) if c == "ASEAN11" else d["countries"][c][k]) / 1e6
        sumT = sumO = 0.0
        for s, d in singles.items():
            sumT += g(d, "T") - S1.at[c, "T_v2_2050_TWh"]; sumO += g(d, "other") - S1.at[c, "other_2050_TWh"]
        combT = S7.at[c, "T_v2_2050_TWh"] - S1.at[c, "T_v2_2050_TWh"]; combO = S7.at[c, "other_2050_TWh"] - S1.at[c, "other_2050_TWh"]
        add.append(dict(country=c, base_step_S1_minus_v3_T_TWh=S1.at[c, "T_v2_2050_TWh"] - S0.at[c, "T_v2_2050_TWh"], sum_single_steps_on_S1_T_TWh=sumT, combined_S7_minus_S1_T_TWh=combT,
                        non_additive_T_TWh=combT - sumT, sum_single_steps_on_S1_other_TWh=sumO, combined_S7_minus_S1_other_TWh=combO, non_additive_other_TWh=combO - sumO))
    AD = pd.DataFrame(add); AD.to_csv(cm.TABLES / "I2_ADDITIVITY.csv", index=False, float_format="%.6f", lineterminator="\n")
    sing_rows = []
    for s, d in singles.items():
        for c in CC:
            sing_rows.append(dict(step=s, label=d["label"], country=c, dT_alone_on_S1_TWh=(d["countries"][c]["T"] - D["S1"]["countries"][c]["T"]) / 1e6,
                                  dT_in_sequence_TWh=float(L[(L.step == s) & (L.country == c)].delta_T_TWh.iloc[0]),
                                  dOther_alone_on_S1_TWh=(d["countries"][c]["other"] - D["S1"]["countries"][c]["other"]) / 1e6))
    pd.DataFrame(sing_rows).to_csv(cm.TABLES / "I2_SINGLE_STEPS.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- AEO8 deviations (final)
    dv = []
    F = L[L.step == "S7"].set_index("country"); V = L[L.step == "S0"].set_index("country")
    for c in CC:
        dv.append(dict(scope="country", country=c, industry_fe_2050_TWh=F.at[c, "implied_industry_fe_2050_TWh"], v3_industry_anchor_TWh=F.at[c, "v3_industry_anchor_TWh"],
                       industry_dev_TWh=F.at[c, "implied_industry_fe_2050_TWh"] - F.at[c, "v3_industry_anchor_TWh"], industry_dev_pct=F.at[c, "dev_industry_vs_v3_anchor_pct"],
                       national_model_TWh=F.at[c, "national_model_2050_TWh"], aeo8_national_tfec_TWh=F.at[c, "aeo8_national_tfec_2050_TWh"],
                       national_dev_TWh=F.at[c, "national_model_2050_TWh"] - F.at[c, "aeo8_national_tfec_2050_TWh"], national_dev_pct=F.at[c, "dev_national_vs_aeo8_pct"],
                       national_dev_v3_TWh=V.at[c, "national_model_2050_TWh"] - V.at[c, "aeo8_national_tfec_2050_TWh"],
                       note="industry FE = ATS industry rows 2050 (after moves) + explicit products (G0 definition); national = industry FE + transport + residential + commercial + agriculture (ATS, rail parent excluded); NEU outside"))
    a10 = [c for c in CC if c != "TL"]
    for s_, col in (("Industry", "implied_industry_fe_2050_TWh"), ("Transport", "transport_2050_TWh"), ("Residential", "residential_2050_TWh"), ("Commercial", "commercial_2050_TWh"),
                    ("AgricultureOthers", "agriculture_2050_TWh")):
        m = float(F.loc[a10, col].sum()); m3 = float(V.loc[a10, col].sum()); c3 = C3[s_] / 1e6
        dv.append(dict(scope="ASEAN10 sector vs C.3", country=s_, industry_fe_2050_TWh=m, v3_industry_anchor_TWh=c3, industry_dev_TWh=m - c3, industry_dev_pct=(m / c3 - 1) * 100,
                       national_model_TWh=m3, note="model 2050 (I2 final) vs C.3 ATS 2050 x k (RAS column target); national_model_TWh column = v3 value of the same sector"))
    DV = pd.DataFrame(dv); DV.to_csv(cm.TABLES / "I2_AEO8_DEVIATION.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- sensitivities
    sr = []
    for f in sorted(glob.glob(str(R / "sens_*.json"))):
        d = json.loads(Path(f).read_text()); nm = Path(f).stem[5:]
        for c in CC + ["ASEAN11"]:
            g = lambda dd, k: (sum(dd["countries"][x][k] for x in CC) if c == "ASEAN11" else dd["countries"][c][k]) / 1e6
            sr.append(dict(sensitivity=nm, label=d["label"][5:], country=c, dT_v2_TWh=g(d, "T") - g(D["S7"], "T"), dOther_TWh=g(d, "other") - g(D["S7"], "other"),
                           dOverflow_TWh=g(d, "overflow") - g(D["S7"], "overflow"), T_v2_TWh=g(d, "T"), other_TWh=g(d, "other")))
    SR = pd.DataFrame(sr); SR.to_csv(cm.TABLES / "I2_SENSITIVITY_RUNS.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- deduction log (final)
    dl = pd.DataFrame(D["S7"]["dlog"])
    for k in [k for k in dl.columns if k.endswith("_mwh")]:
        dl[k.replace("_mwh", "_TWh")] = dl.pop(k) / 1e6
    dl.to_csv(cm.TABLES / "I2_DEDUCTION_LOG.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- per-country final files
    sub_names = {"steel": "钢", "cement": "水泥", "ammonia": "合成氨", "dispersed": "分散（UNSD 分行）", "other": "其他", "nonferrous_nickel": "镍", "nonferrous_alumina": "氧化铝",
                 "nonferrous_aluminium_primary": "原铝", "nonferrous_copper": "铜（v3 有色）", "pulp_paper": "纸浆造纸", "pulp_paper_new_lines": "纸浆造纸新线", "hvc": "HVC（2019 装置）",
                 "hvc_new_plants": "HVC 新装置", "methanol": "甲醇（能源用途）", "methanol_new_plants": "甲醇新装置", "glass": "玻璃", "alumina": "氧化铝（显式）", "copper": "铜（显式）", "lime": "石灰"}
    for c in CC:
        out = []
        z = L[L.country == c]
        for r in z.itertuples(index=False):
            out.append(dict(record_type="step", **r._asdict()))
        parts = D["S7"]["countries"][c]["parts"]
        for k, v in parts.items():
            out.append(dict(record_type="subsector", country=c, step="S7", label=sub_names.get(k, k), subsector=k, T_v2_2050_TWh=sum(v.values()) / 1e6,
                            **{f"T_{col}": v.get(kk, 0.0) / 1e6 for kk, col in cm.COLMAP.items()}, status="PROPOSED (quantified)", grade="C"))
        if c != "TL":
            n0 = NS[(NS.step == "S0") & (NS.country == c)].set_index("node"); n7 = NS[(NS.step == "S7") & (NS.country == c)].set_index("node")
            for n in sorted(set(n0.index) | set(n7.index)):
                out.append(dict(record_type="node", country=c, step="S7", node=n, share_T_v3=float(n0.share_T.get(n, 0.0)), share_T_v4=float(n7.share_T.get(n, 0.0)),
                                share_electricity_v3=float(n0.share_electricity.get(n, 0.0)), share_electricity_v4=float(n7.share_electricity.get(n, 0.0)),
                                diff_T_pp=(float(n7.share_T.get(n, 0.0)) - float(n0.share_T.get(n, 0.0))) * 100, status="PROPOSED (quantified)", grade="C"))
        dd = DV[(DV.scope == "country") & (DV.country == c)].iloc[0].to_dict(); dd.pop("scope")
        out.append(dict(record_type="anchor", step="S7", **dd, status="PROPOSED (quantified)", grade="C"))
        pd.DataFrame(out).to_csv(cm.I2 / f"{c}_V4_FINAL.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- ASEAN summary
    sm = []
    for r in L[L.country == "ASEAN11"].itertuples():
        sm.append(dict(section="steps", item=f"{r.step} {r.label}", v3_TWh=float(v3T["ASEAN11"]), value_TWh=r.T_v2_2050_TWh, delta_TWh=r.delta_T_TWh, other_TWh=r.other_2050_TWh, other_share=r.other_share))
    for s_, col in (("Industry (FE, implied)", "implied_industry_fe_2050_TWh"), ("Industry T_v2", "T_v2_2050_TWh"), ("Transport", "transport_2050_TWh"), ("Residential", "residential_2050_TWh"),
                    ("Commercial", "commercial_2050_TWh"), ("AgricultureOthers", "agriculture_2050_TWh"), ("NonEnergyUse", "neu_2050_TWh"), ("land transport fuel", "land_fuel_2050_TWh"),
                    ("EV electricity", "ev_electricity_2050_TWh"), ("industrial biomass overflow", "biomass_overflow_TWh")):
        a3, a4 = float(V.loc[CC, col].sum()), float(F.loc[CC, col].sum())
        key = {"Industry (FE, implied)": "Industry"}.get(s_, s_)
        sm.append(dict(section="sectors 2050", item=s_, v3_TWh=a3, value_TWh=a4, delta_TWh=a4 - a3, c3_TWh=(C3[key] / 1e6 if key in C3 else None),
                       dev_vs_c3_pct=((float(F.loc[a10, col].sum()) / (C3[key] / 1e6) - 1) * 100 if key in C3 else None)))
    for c in sorted([c for c in CC if c != "TL"], key=lambda c: -F.at[c, "other_share"]):
        sh = F.at[c, "other_share"]
        sm.append(dict(section="other share by country (reference band 30-40 %, not a target)", item=c, v3_TWh=float(V.at[c, "other_2050_TWh"]), value_TWh=float(F.at[c, "other_2050_TWh"]),
                       other_share=sh, other_share_v3=float(V.at[c, "other_share"]), band=("above" if sh > 0.40 else ("inside" if sh >= 0.30 else "below"))))
    pd.DataFrame(sm).to_csv(cm.I2 / "ASEAN_V4_SUMMARY.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---------------------------------------------------------------------------------------------- evidence
    for r in L[L.step.isin(["S0", "S7"])].itertuples():
        ev.add(f"{r.country}.{r.step}", dict(T_v2=r.T_v2_2050_TWh, other=r.other_2050_TWh, share=r.other_share, industry_fe=r.implied_industry_fe_2050_TWh),
               "TWh (2050)", "EXACT" if r.step == "S0" else "PROPOSED", "C", "tables/I2_STEPS_LONG.csv")
    for r in AD.itertuples():
        ev.add(f"additivity.{r.country}", dict(non_additive_T=r.non_additive_T_TWh, non_additive_other=r.non_additive_other_TWh), "TWh", "EXACT", "C", "tables/I2_ADDITIVITY.csv")
    ev.write()
    figures(L, D, SR, DV)
    pd.set_option("display.width", 220)
    print(L[L.country == "ASEAN11"][["step", "label", "T_v2_2050_TWh", "delta_T_TWh", "other_2050_TWh", "other_share"]].round(2).to_string())
    print(AD.round(3).to_string()); print(DV.round(2).to_string())


def figures(L, D, SR, DV):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for fp in ("/mnt/c/Windows/Fonts/simhei.ttf", "/mnt/c/Windows/Fonts/msyh.ttc"):
        if Path(fp).exists():
            font_manager.fontManager.addfont(fp); matplotlib.rcParams["font.sans-serif"] = [font_manager.FontProperties(fname=fp).get_name()]; break
    matplotlib.rcParams["axes.unicode_minus"] = False
    cm.FIGS.mkdir(parents=True, exist_ok=True)
    lab = {"S0": "v3", "S1": "基年", "S2": "边界", "S3": "(ii)", "S4": "(i)自备", "S5a": "钢", "S5b": "水泥", "S5c": "镍", "S5d": "纸浆", "S5e": "HVC", "S5f": "甲醇",
           "S5g": "新装置", "S6a": "MY氨", "S6b": "玻璃等", "S6c": "VN拆分", "S7": "v4"}
    for c in CC + ["ASEAN11"]:
        z = L[L.country == c].set_index("step").loc[STEPS]
        if z.T_v2_2050_TWh.abs().max() == 0:
            continue
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw=dict(width_ratios=[3, 1.2]))
        prev = 0.0; xs = range(len(STEPS))
        for i, s in enumerate(STEPS):
            v = float(z.at[s, "T_v2_2050_TWh"])
            if s in ("S0", "S7"):
                ax[0].bar(i, v, color="#2a6f97"); ax[0].text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=7)
            else:
                d = v - prev; ax[0].bar(i, d, bottom=prev, color=("#7a9e7e" if d >= 0 else "#c97b63"))
                if abs(d) > 0.005 * float(z.T_v2_2050_TWh.max()):
                    ax[0].text(i, max(v, prev), f"{d:+,.1f}", ha="center", va="bottom", fontsize=6.5)
            prev = v
        vals = z.T_v2_2050_TWh.astype(float).values
        ax[0].set_ylim(max(0.0, 0.9 * vals.min() - 0.02 * vals.max()), 1.04 * vals.max())   # zoom: the steps are small against the totals
        ax[0].set_xticks(list(xs)); ax[0].set_xticklabels([lab[s] for s in STEPS], rotation=45, fontsize=8); ax[0].set_ylabel("T_v2 2050（TWh；纵轴不从 0 起）")
        ax[0].set_title(f"{c}：v3 → v4 逐步变化（T_v2）", loc="left", fontsize=10)
        ax[1].plot(list(xs), z.other_share.values * 100, marker="o", color="#5c4d7d", lw=1.2, ms=3)
        ax[1].axhspan(30, 40, color="#ddd", alpha=0.6, lw=0); ax[1].set_ylim(0, 100); ax[1].set_xticks([0, 15]); ax[1].set_xticklabels(["v3", "v4"])
        ax[1].set_title("“其他”占比（%；灰带 30–40 % 只作参照）", loc="left", fontsize=9)
        fig.tight_layout(); fig.savefig(cm.FIGS / f"fig_i2_waterfall_{c}.png", dpi=140); plt.close(fig)
    F = L[(L.step == "S7") & L.country.isin([c for c in CC if c != "TL"])].sort_values("other_share", ascending=False)
    V = L[L.step == "S0"].set_index("country")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axhspan(30, 40, color="#ddd", alpha=0.7, lw=0, label="30–40 % 参照区间（不作目标）")
    ax.bar(range(len(F)), F.other_share * 100, color="#2a6f97", label="v4（I2 定稿）")
    ax.scatter(range(len(F)), [V.at[c, "other_share"] * 100 for c in F.country], color="#c97b63", zorder=3, label="v3", s=18)
    ax.set_xticks(range(len(F))); ax.set_xticklabels(F.country); ax.set_ylabel("“其他”占 T_v2（%）"); ax.legend(fontsize=8, frameon=False)
    ax.set_title("各国 2050 年“其他”占比：v3 与 v4", loc="left", fontsize=10); fig.tight_layout(); fig.savefig(cm.FIGS / "fig_i2_other_share.png", dpi=140); plt.close(fig)
    S = DV[DV.scope == "ASEAN10 sector vs C.3"]
    fig, ax = plt.subplots(figsize=(8, 4)); x = np.arange(len(S))
    ax.bar(x - 0.25, S.national_model_TWh, 0.25, label="v3", color="#9db4c0"); ax.bar(x, S.industry_fe_2050_TWh, 0.25, label="v4（I2）", color="#2a6f97")
    ax.bar(x + 0.25, S.v3_industry_anchor_TWh, 0.25, label="C.3 × k", color="#c97b63")
    ax.set_xticks(x); ax.set_xticklabels(["工业", "交通", "居民", "商业", "农业及其他"]); ax.set_ylabel("TWh（2050）"); ax.legend(fontsize=8, frameon=False)
    ax.set_title("东盟 10 国 2050 年各部门终端用能：v3、v4 与 C.3", loc="left", fontsize=10); fig.tight_layout(); fig.savefig(cm.FIGS / "fig_i2_asean_sectors.png", dpi=140); plt.close(fig)


if __name__ == "__main__":
    main()
