"""V4 W08 checklist sections 7-10: the network-facing v4 tables of one switch set, written by `python scripts_project/v4_industry.py --anchor-mode <m>`
into research_inputs/industry_v4/out_<anchor_mode>/ (the v3.1 tables are not touched; the build reads this folder only with
research.demand.v4.enabled = true and refuses a folder whose V4_SWITCHES.json differs from the configured switch set).

Tables (final step S7 of v4_industry.build_steps):
  DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv  ATS table after the v4 seed, anchors and reading-I edits; BN methanol energy use taken out of the
                                                        BN NEU gas rows (decision 210 item 7; 2019 3.45 TWh, 2050 x growth);
  DEMAND_ANCHOR_AEO8_ATS.csv, INDUSTRY_OUTPUT_2050_M08B.csv, DEMAND_ANCHOR_C3_DEVIATION.csv   m08b outputs of the run;
  INDUSTRY_2050_SUMMARY_V4.csv           s3_0 heat-band summary with the carrier columns = T_v2 by carrier of the conservation layer (v3_industry rule);
  INDUSTRY_2050_SUBSECTOR_CARRIER_V4.csv parts (sub-sector x carrier, 2050);
  INDUSTRY_CARRIER_NODE_SHARES_V4.csv    carrier node shares = sum over parts of energy x sub-sector node shares (I2 i2_tables.Nodes rule: v3 sub-sector
                                         shares, ammonia on the v2 national shares, new / re-located sub-sectors on the W07 session shares share_v4);
  PROCESS_EMISSIONS_2050_V4.csv          EDGAR 2.A / 2.B / 2.C x the v4 ATS industry multiplier, 2.A.1 x cement 2050 / 2019 (s2_0_process_emissions.py rule);
  FEEDSTOCK_CARBON_TERRITORIAL_2050_V4.csv  2.B + 2.D x the v4 multiplier, plastics unchanged, full release from the v4 NEU rows (s2b_feedstock.py rule);
  INDUSTRY_CURVE_WEIGHTS_V4.csv          country x zone x curve key x energy type (v4_profiles.composition);
  SNAPSHOT.json, V4_SWITCHES.json        T_v2, 'other', sub-sectors per country; switch set + SHA256 of every table.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import v3_industry as v3   # noqa: E402
import v4_profiles as PR   # noqa: E402
from d1_common import HVC_FEEDSTOCK_ACCOUNTS, NEU_GAS_ACCOUNT   # noqa: E402
from v4_common import ASEAN, DEMAND_DIR, IND_V3, OUTC, REG_DIR, ROOT, V4_DIR, is_main_set, out_dir, sha256, switch_sha   # noqa: E402

EDGAR = REG_DIR / "sources/EDGAR2025_IPPU_FUGITIVE_WASTE_ASEAN11_2019.csv"
GROUPS = {"minerals": ["2.A.1", "2.A.2", "2.A.3", "2.A.4"], "chemicals": ["2.B"], "metals": ["2.C"]}   # = s2_0_process_emissions.GROUPS
EF = {"coal": 0.3361, "oil": 0.2571, "gas": 0.198}   # = s2b_feedstock.EF


class Nodes:
    """I2 i2_tables.Nodes (rule unchanged); session shares from NODE_SHARES_SESSIONS_V4.csv."""
    SESSION_KEY = {"steel": ["steel"], "cement": ["cement"], "pulp_paper": ["pulp_paper", "pulp and paper", "MM_paper", "LA_pulp"],
                   "pulp_paper_new_lines": ["pulp_paper", "pulp and paper", "LA_pulp"], "hvc": ["ethylene", "hvc", "ethylene (HVC)"],
                   "hvc_new_plants": ["ethylene", "hvc", "ethylene (HVC)"], "methanol": ["methanol"], "glass": ["glass"], "alumina": ["alumina"],
                   "copper": ["MM_copper", "LA_copper"], "lime": ["lime"]}
    MY_OTHER = {"electricity": "other (electricity), proposal", "_": "other (heat bands and oil), proposal A"}

    def __init__(self):
        S = pd.read_csv(IND_V3 / "INDUSTRY_NODE_SHARES_V3.csv")
        self.v3 = {(r.country, r.subsector): {} for r in S.itertuples()}
        for r in S.itertuples():
            self.v3[(r.country, r.subsector)][r.node] = float(r.share)
        A = pd.read_csv(IND_V3 / "INDUSTRY_NODE_ALLOCATION_V2_V3.csv")
        self.base = {}
        for c, g in A.groupby("country"):
            t = g.v2_twh.sum(); self.base[c] = {r.node: float(r.v2_twh) / t for r in g.itertuples() if t > 0}
        self.sess = {}
        T = pd.read_csv(V4_DIR / "NODE_SHARES_SESSIONS_V4.csv")
        for (c, s), g in T.groupby(["country", "subsector"], sort=False):
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


def norm(d: dict) -> dict:
    t = sum(d.values()); return {k: v / t for k, v in d.items()} if t else {}


def bn_neu_methanol(ats: pd.DataFrame, item: dict) -> dict:
    """Decision 210 item 7: BN methanol energy use (gas) leaves the BN NEU gas rows (2050 value; floored at 0, truncation reported)."""
    m = (ats.country == "BN") & (ats.sector == "NonEnergyUse") & (ats.carrier == "gas") & (ats.account == NEU_GAS_ACCOUNT) & (ats.value_2050_mwh != "")
    before = float(pd.to_numeric(ats.loc[m, "value_2050_mwh"]).sum()); want = float(item["gas_2050_mwh"])
    after = max(0.0, before - want)
    if before > 0:
        f = after / before
        for i in ats.index[m]:
            ats.at[i, "value_2050_mwh"] = repr(float(ats.at[i, "value_2050_mwh"]) * f)
            ats.at[i, "growth_method"] = str(ats.at[i, "growth_method"]) + f"; minus BN methanol energy use {want:.6g} MWh (V4 W08, decision 210 item 7)"
    return dict(before_mwh=before, deducted_mwh=min(want, before), truncated_mwh=max(0.0, want - before), after_mwh=after)


def process_and_feedstock(ats: pd.DataFrame, main_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ext = pd.read_csv(EDGAR)
    mult = ats[ats.sector == "Industry"].groupby("country").multiplier_total.first().astype(float).to_dict()
    proc = []
    for c in ASEAN:
        e = ext[ext.iso == c]
        val = lambda codes: float(e[e.ipcc_code_2006_for_standard_report.isin(codes)].kt_CO2_2019.sum()) * 1e3
        for g, codes in GROUPS.items():
            v19 = val(codes)
            if g == "minerals":
                v_cem = val(["2.A.1"]); c19 = float(main_summary.at[c, "cement_2019_t"]); c50 = float(main_summary.at[c, "cement_2050_t"])
                v50 = v_cem * (c50 / c19 if c19 > 0 else 0.0) + (v19 - v_cem) * mult[c]
            else:
                v50 = v19 * mult[c]
            proc.append(dict(country=c, group=g, tco2_2019=v19, industry_multiplier=mult[c], tco2_2050=v50))
    fc = pd.read_csv(REG_DIR / "FEEDSTOCK_CARBON_TERRITORIAL_2050_aeo8_ats_anchor.csv", keep_default_na=False, dtype=str)
    reg = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    hvc_primary = float(reg.loc["share_HVC_primary_fraction_2050", "value"])
    for i, r in fc.iterrows():
        c = r.country; m = mult.get(c, 1.0)
        p = (float(r.edgar_2B_2019_t) + float(r.edgar_2D_2019_t)) * m
        ne = ats[(ats.country == c) & (ats.sector == "NonEnergyUse")].copy(); ne["v"] = pd.to_numeric(ne.value_2050_mwh, errors="coerce").fillna(0.0)
        full = sum(float(x.v) * EF.get(x.carrier, 0.0) * (hvc_primary if (x.carrier == "oil" and x.account in HVC_FEEDSTOCK_ACCOUNTS) else 1.0) for x in ne.itertuples())
        fc.at[i, "industry_multiplier"] = repr(m); fc.at[i, "process_2B_2D_2050_t"] = repr(p)
        fc.at[i, "territorial_total_2050_t"] = repr(p + float(r.plastics_burned_co2_2050_t)); fc.at[i, "full_release_2050_t"] = repr(full)
        fc.at[i, "difference_full_minus_territorial_t"] = repr(full - (p + float(r.plastics_burned_co2_2050_t)))
    return pd.DataFrame(proc), fc


def write_tables(s: dict, chain=None) -> dict:
    import v4_industry as V
    ch = chain or V.Chain()
    I = V.Inputs()
    case = V.final_case(I, s)
    res = ch.run(case)
    od = out_dir(s)
    if od.exists():
        shutil.rmtree(od)
    od.mkdir(parents=True)
    ats = res["ats"].copy()
    neu = bn_neu_methanol(ats, I.items_for(s)["bn_neu_methanol"]) if s["products"] else None
    ats.to_csv(od / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", index=False, lineterminator="\n")
    mo = res["mo"]
    (od / "DEMAND_ANCHOR_AEO8_ATS.csv").write_bytes(mo["ANCH"]); (od / "INDUSTRY_OUTPUT_2050_M08B.csv").write_bytes(mo["OUTRULE"])
    if mo.get("DIR") is not None and (mo["DIR"] / "DEMAND_ANCHOR_C3_DEVIATION.csv").exists():
        shutil.copyfile(mo["DIR"] / "DEMAND_ANCHOR_C3_DEVIATION.csv", od / "DEMAND_ANCHOR_C3_DEVIATION.csv")
    # ---- industry summary (v3_industry rule: carrier columns = T_v2 by carrier of the conservation layer)
    S = res["S"].copy()
    parts_all, comp = {}, []
    for c, snap in res["snap"].items():
        L = snap["L"]
        if L["T"] <= 0:
            continue
        for k in v3.CARRIERS:
            S.at[c, v3.col(k)] = sum(v.get(k, 0.0) for v in L["parts"].values())
            if k == "biomass":
                S.at[c, "pe_biomass_mwh"] = S.at[c, v3.col(k)]
        parts_all[c] = L["parts"]
        for sub, v in L["parts"].items():
            for k, x in v.items():
                if abs(x) > 0:
                    comp.append(dict(case="main", country=c, subsector=sub, carrier=k, mwh_2050=x))
    S.reset_index().to_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv", index=False, lineterminator="\n")
    pd.DataFrame(comp).sort_values(["country", "subsector", "carrier"]).to_csv(od / "INDUSTRY_2050_SUBSECTOR_CARRIER_V4.csv", index=False, lineterminator="\n")
    # ---- carrier node shares
    N = Nodes(); rows, srcs = [], {}
    for c, parts in parts_all.items():
        al, src = N.allocate(c, parts); srcs[c] = src
        for car, d in al.items():
            for n_, x in sorted(norm(d).items()):
                rows.append(dict(case="main", country=c, carrier=car, node=n_, share=x))
    pd.DataFrame(rows).to_csv(od / "INDUSTRY_CARRIER_NODE_SHARES_V4.csv", index=False, lineterminator="\n")
    # ---- process emissions, feedstock carbon
    pr, fc = process_and_feedstock(ats, res["main"])
    pr.to_csv(od / "PROCESS_EMISSIONS_2050_V4.csv", index=False, lineterminator="\n"); fc.to_csv(od / "FEEDSTOCK_CARBON_TERRITORIAL_2050_V4.csv", index=False, lineterminator="\n")
    # ---- curve weights
    W = PR.composition(parts_all, PR.dispersed_rows(res["pz"]), N)
    W.to_csv(od / "INDUSTRY_CURVE_WEIGHTS_V4.csv", index=False, lineterminator="\n")
    # ---- snapshot and switches
    snap = V.pack(res, "final"); (od / "SNAPSHOT.json").write_text(json.dumps(snap, default=float))
    files = {p.name: sha256(p) for p in sorted(od.glob("*")) if p.is_file()}
    rec = dict(switches=s, switch_sha256=switch_sha(s), dir=od.name, main_set=is_main_set(s), asean_T_v2_TWh=sum(v["T"] for v in snap["countries"].values()) / 1e6,
               T_v2_TWh={c: v["T"] / 1e6 for c, v in snap["countries"].items()}, other_TWh={c: v["other"] / 1e6 for c, v in snap["countries"].items()},
               bn_neu_methanol=neu, node_share_sources=srcs, files=files, m08b_runs=ch.n_m08b, s30_runs=ch.n_s30)
    (od / "V4_SWITCHES.json").write_text(json.dumps(rec, indent=1, default=float) + "\n")
    print(json.dumps(dict(out=str(od.relative_to(ROOT)), asean_T_v2_TWh=rec["asean_T_v2_TWh"], bn_neu=neu), indent=1))
    return rec
