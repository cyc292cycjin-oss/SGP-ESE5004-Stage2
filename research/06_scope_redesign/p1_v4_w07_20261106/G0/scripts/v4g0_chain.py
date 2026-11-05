"""V4 W07 G0 items 1, 2, 4: all confirmed Indonesian corrections (decisions 204, 206, 207) re-computed together in one scratch copy of the data chain.

    PYTHONHASHSEED=0 python scripts/v4g0_chain.py          (WSL pypsa-earth python; repository read only, nothing solved)

Order (instruction B-G0 item 1), each step one row of ID_OTHER_SHARE_STEPS.csv, cumulative, growth reading I (ATS multiplier unchanged):
  1  coal NCV 20.29 GJ/t (decision 207 item 2; UNSD 24.48 and IPCC 18.9 as sensitivities; v3 25.80 as the second full set)
  2  captive coal option (b), central level (S1: nickel mid, other sectors low); C re-converted from tonnes at the same NCV, E unchanged
  3a nickel on the 2023 base (Wei Case 3 for all products = S2)
  3b nickel unit energy by product from the original Wei 2020 (NPI -> Case 4-NPI, ferronickel / matte -> Case 3-FeNi; Case 3 path kept as 'alt')
  4  cement correction (ii)
  5  steel: spatial allocation only (no effect on T_v2 or 'other')
  6  pulp and paper under the closed-loop rule (decision 206 item 3): only purchased energy is explicit; 2019 deduction from 'other' =
     electricity + the non-biomass thermal part spread over the bucket's fossil mix (coal, oil, gas); the biomass part (black liquor, bark) is
     neither deducted from 'other' nor in T_v2 and is listed separately (2019 45.99, 2050 95.42 TWh)
  7  ethylene incl. LINE (2025 base, utilisation 0.85; 2019 deduction from the UNSD chemicals row at 860 kt x 0.85); excl. LINE as sensitivity
  8  fuelwood 'n.e.s. industry' at its 2010-2017 mean (S2 section 3); 2020-2021 mean and UNSD 2019 as sensitivities
Validation before any result: the unmodified copy reproduces the repository byte for byte (s3_0 outputs) and the ID row / v3 'other' to 0 MWh;
this code reproduces S2 'all (1-5)', the W11 NCV cases (b) and (d) for ID, W11 'NCV (b) + captive central' and the S2 fuelwood-low v3 line.
Outputs ID_OTHER_SHARE_STEPS.csv, ID_G0_SCENARIOS.csv, ID_G0_SENSITIVITY.csv, evidence/_chain_evidence.json, evidence/_chain_detail.json.
"""
from __future__ import annotations

import filecmp
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g0_common as cm   # noqa: E402
import v4g0_nickel as nk   # noqa: E402

STEP_LABEL = {"0": "v3", "1": "热值", "2": "+自备煤 (b) 中心值", "3a": "+镍 2023 基年（Case 3）", "3b": "+镍单耗按产品（NPI 用 Case 4）",
              "4": "+水泥 (ii)", "5": "+钢（只换空间）", "6": "+纸浆造纸（闭环规则）", "7": "+乙烯（含 LINE，u 0.85）", "8": "+燃料木材 2010–2017 年均"}
STEP_GRADE = {"0": "B/C", "1": "B", "2": "C", "3a": "B/C", "3b": "B/C", "4": "C", "5": "B/C", "6": "C", "7": "C", "8": "B/C"}
COLMAP = {"electricity": "elec", "heat": "heat_lt150", "heat_medium_a": "heat_150_200", "heat_medium_b": "heat_200_400", "heat_high": "heat_gt400",
          "oil": "oil", "gas": "gas", "coal": "coal", "biomass": "biomass", "hydrogen": "H2", "ammonia": "ammonia", "methanol": "methanol"}


class Runner:
    def __init__(self):
        self.v3 = cm.import_v3()
        self.fut = self.v3.future_vectors(); self.ne = self.v3.nickel_unit_energy()
        self.nf_main = self.v3.nonferrous(self.fut, "main", self.ne)[0]["ID"]
        self.ni = {"case3": nk.vectors("case3")["total"], "by_product": nk.vectors("by_product")["total"]}
        self.niupper_scale = (self.v3.NI_UPPER_MWH_PER_T_NPI / self.v3.NI_NPI_NI_FRACTION) / (self.ne["electricity_mwh_per_t_ni"] + self.ne["fuel_mwh_per_t_ni"])
        cap = pd.read_csv(cm.S2D / "s1/ID_CAPTIVE_COAL_2019.csv"); tot = cap[cap.group == "合计"].set_index("level")
        self.captive = {lv: dict(C_v3_mwh=float(tot.at[lv, "coal_in_industry_twh_model"]) * 1e6, E_mwh=float(tot.at[lv, "gen_in_industry_gwh"]) * 1e3,
                             C_kt=float(tot.at[lv, "coal_in_industry_kt"])) for lv in ("low", "central", "mid", "high")}
        P = json.loads((cm.S2D / "s2/_products_evidence.json").read_text())["extra"]["chain_inputs"]
        self.pp19_el, self.pp19_fuel, self.pp19_bio = P["pp_2019_electricity_mwh"], P["pp_2019_fuel_mwh"], P["pp_2019_biomass_part_mwh"]
        self.pp50 = P["pp_2050"]; self.eth = P["eth"]; self.eth25 = P["eth_base2025_v2050"]
        B = {r["key"]: r["value"] for r in json.loads((cm.S2D / "s2/_biomass_evidence.json").read_text())["numbers"]}
        self.fw19 = B["3.unsd2019.Fuelwood.Consumption not elsewhere specified (industry)"]; self.f_fw = B["3.factor.Fuelwood"]
        self.fw_mean = {"m1017": B["3.series.industry_mean_2010_2017_km3"], "m2021": B["3.series.industry_mean_2020_2021_km3"]}
        self.bagasse_mwh = B["3.unsd2019.Bagasse.Consumption not elsewhere specified (industry)"] * B["3.factor.Bagasse"] * 1e6
        anc = pd.read_csv(cm.REPO / "research_inputs/demand_v5/DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
        self.anchor_mwh = float(anc.at["ID", "industry_anchor_mwh"]); self.tfec19_mwh = float(anc.at["ID", "tfec_2019_Industry_mwh"])
        self.ch = cm.Chain(); self.ch.copy(); self.ch.patch()
        self.repro = None
        self.inputs = {str(p.relative_to(cm.REPO) if str(p).startswith(str(cm.REPO)) else p): cm.sha256(p) for p in
                       (cm.S2D / "s1/ID_CAPTIVE_COAL_2019.csv", cm.S2D / "s2/_products_evidence.json", cm.S2D / "s2/_biomass_evidence.json",
                        cm.REPO / cm.CACHE_REL, cm.REPO / cm.ATS_REL, cm.REPO / cm.D1_REL, cm.REPO / cm.S30_REL)}

    # ------------------------------------------------------------------------------------------------------------------ reproduction
    def reproduce(self):
        self.ch.unpatch(); self.ch.restore()
        self.ch._exec("s3_0_industry.py", dict(cm.ENV))
        dd, rd = self.ch.chain / "research_inputs/demand_v5", cm.REPO / "research_inputs/demand_v5"
        same = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in cm.S3_OUT}
        row = pd.read_csv(dd / cm.SUMMARY).set_index("country").loc["ID"]; rrow = pd.read_csv(rd / cm.SUMMARY).set_index("country").loc["ID"]
        dev = max(abs(float(row[self.v3.col(x)]) - float(rrow[self.v3.col(x)])) for x in self.v3.CARRIERS)
        L = cm.v3_layer(self.v3, row, self.fut, self.nf_main)
        sub = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
        sub = sub[(sub.case == "main") & (sub.country == "ID") & (sub.subsector == "other")].set_index("carrier").mwh_2050
        dev3 = max(abs(L["other"].get(k, 0.0) - float(sub.get(k, 0.0))) for k in set(L["other"]) | set(sub.index))
        self.ch.patch(); self.ch._exec("s3_0_industry.py", dict(cm.ENV))
        same_p = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in cm.S3_OUT}
        self.ch._exec("m08b_demand.py", dict(cm.ENV)); self.ch._exec("s3_0_industry.py", dict(cm.ENV))   # growth reading II path, unmodified
        same_2 = {f: filecmp.cmp(dd / f, rd / f, shallow=False) for f in cm.M08B_OUT + cm.S3_OUT}
        self.ch.restore()
        self.repro = dict(byte_identical_unmodified=same, byte_identical_patched_no_env=same_p, byte_identical_mode2_unmodified=same_2,
                          max_abs_dev_T_carriers_mwh=dev, max_abs_dev_v3_other_mwh=dev3, T_v2_twh=L["T"] / 1e6, other_twh=L["other_total"] / 1e6)
        if not all(same.values()) or not all(same_p.values()) or not all(same_2.values()) or dev > 0 or dev3 > 1e-3:
            raise SystemExit(f"STOP (A8): the unmodified scratch copy does not reproduce the repository ID row: {self.repro}")
        return self.repro

    # ------------------------------------------------------------------------------------------------------------------ one scenario
    def scenario(self, name, ncv="v3", captive=None, nickel=None, cem=False, steel=False, pp=None, pp_case="main", eth=None, fw=None, bagasse=False, mode="I"):
        F = cm.NCV[ncv]
        moves, info = [], {}
        if captive:
            c = self.captive[captive]; C = c["C_v3_mwh"] * F / cm.NCV_V3; E = c["E_mwh"]   # same tonnes at the scheme NCV (W11 section 4.3)
            moves += [("other", "coal", C), ("other", "electricity", -E)]; info.update(C_mwh=C, E_mwh=E, C_kt=c["C_kt"])
        extra, pp_moves, eth_moves, closed_bio = {}, {}, {}, dict(y2019=0.0, y2050=0.0)
        if pp:
            _, ob0, _ = self.ch.run(F, moves, cem)   # bucket after the earlier steps (as S2)
            mix = {k: float(ob0[f"other_2019_{k}_mwh"]) for k in cm.CARS19}
            if pp == "closed":
                nonbio = self.pp19_fuel - self.pp19_bio
                pp_moves = cm.spread(nonbio, self.pp19_el, mix, fuels=cm.FOSSIL)
                v = {k: float(x) for k, x in self.pp50[pp_case].items()}
                closed_bio = dict(y2019=self.pp19_bio, y2050=v["biomass"]); v["biomass"] = 0.0
            elif pp == "spread":   # S2 rule (biomass part deducted from 'other' and explicit in T_v2) - comparison only
                pp_moves = cm.spread(self.pp19_fuel, self.pp19_el, mix)
                v = {k: float(x) for k, x in self.pp50[pp_case].items()}
            moves += [("other", k, x) for k, x in pp_moves.items()]
            extra["pulp_paper"] = v
        if eth:
            chem19 = self.ch.sub19(F, moves)[cm.CHEM]
            eq = self.eth["central"]
            eth_moves = cm.spread(eq["d19_mwh"] * (1 - eq["el_share"]), eq["d19_mwh"] * eq["el_share"], chem19)
            moves += [(cm.CHEM, k, x) for k, x in eth_moves.items()]
            src = self.eth25 if eth == "line" else eq["v2050"]
            extra["ethylene"] = {k: 0.0 for k in cm.OUTC}
            for k, x in src.items():
                extra["ethylene"][k] += float(x)
        if fw:
            d = (self.fw19 - self.fw_mean[fw]) * self.f_fw * 1e6
            moves.append(("other", "biomass", d)); info["fuelwood_move_mwh"] = d
        if bagasse:
            moves.append(("other", "biomass", self.bagasse_mwh)); info["bagasse_move_mwh"] = self.bagasse_mwh
        row, ob, pz = self.ch.run(F if ncv != "v3" else None, moves, cem, mode=mode)
        nf = dict(self.nf_main)
        if nickel:
            base = self.ni["case3" if nickel in ("case3", "niupper") else "by_product"]
            nf["nonferrous_nickel"] = {k: v * (self.niupper_scale if nickel == "niupper" else 1.0) for k, v in base.items()}
        L = cm.v3_layer(self.v3, row, self.fut, nf, extra)
        prod50 = sum(sum(v.values()) for v in extra.values())
        r = dict(scenario=name, ncv_scheme=ncv, ncv_gj_t=F, growth_mode=mode, captive=captive or "", nickel=nickel or "main(2019, Case 3)", cement_ii=cem,
                 steel_spatial=steel, pulp_paper=(f"{pp}:{pp_case}" if pp else ""), ethylene=eth or "", fuelwood=fw or "", bagasse_closed=bagasse,
                 T_v2_2050_twh=L["T"] / 1e6, other_2050_twh=L["other_total"] / 1e6, other_share=L["other_total"] / L["T"], other_scale=L["scale"],
                 explicit_2050_twh=L["explicit"] / 1e6, industry_2019_twh=self.ch.last["ats_2019_mwh"] / 1e6, other_2019_v2_twh=float(ob.other_2019_mwh) / 1e6,
                 ats_industry_2050_twh=self.ch.last["ats_2050_mwh"] / 1e6, products_2050_twh=prod50 / 1e6,
                 implied_industry_fe_2050_twh=(self.ch.last["ats_2050_mwh"] + prod50) / 1e6, aeo8_anchor_twh=self.anchor_mwh / 1e6,
                 cement_2019_twh=float(pz[pz.subsector == "cement"].mwh_2019.astype(float).sum()) / 1e6,
                 closed_loop_biomass_2019_twh=closed_bio["y2019"] / 1e6, closed_loop_biomass_2050_twh=closed_bio["y2050"] / 1e6,
                 C_twh=info.get("C_mwh", 0.0) / 1e6, E_twh=info.get("E_mwh", 0.0) / 1e6, ncv_delta_2019_twh=self.ch.last["log"].get("ncv", {}).get("_delta_mwh", 0.0) / 1e6,
                 fuelwood_move_2019_twh=info.get("fuelwood_move_mwh", 0.0) / 1e6, bagasse_move_2019_twh=info.get("bagasse_move_mwh", 0.0) / 1e6)
        r["anchor_dev_twh"] = r["implied_industry_fe_2050_twh"] - r["aeo8_anchor_twh"]; r["anchor_dev_pct"] = r["anchor_dev_twh"] / r["aeo8_anchor_twh"] * 100
        for k in cm.OUTC:
            r[f"other_{k}_twh"] = L["other"].get(k, 0.0) / 1e6
        for k, v in L["by_sub"].items():
            r[f"sub_{k}_twh"] = v / 1e6
        for k in cm.CARS19:
            r[f"other_2019_{k}_twh"] = float(ob[f"other_2019_{k}_mwh"]) / 1e6
            r[f"pp_move_2019_{k}_twh"] = pp_moves.get(k, 0.0) / 1e6
            r[f"eth_move_2019_{k}_twh"] = eth_moves.get(k, 0.0) / 1e6
        detail = dict(explicit_carriers=L["explicit_carriers"], other=L["other"], pz=pz.to_dict("records"), moves=self.ch.last["log"].get("moves", []),
                      ncv_cells=self.ch.last["log"].get("ncv", {}), extra=extra)
        return r, detail


def path(R, ncv, nickel_mode="by_product"):
    """Cumulative steps of the instruction; nickel_mode 'by_product' = main (3a then 3b), 'case3' = alternative (3b skipped)."""
    kw, rows, det = {}, [], {}
    seq = [("0", {}), ("1", dict(ncv=ncv)), ("2", dict(captive="central")), ("3a", dict(nickel="case3")), ("3b", dict(nickel="by_product")),
           ("4", dict(cem=True)), ("5", dict(steel=True)), ("6", dict(pp="closed")), ("7", dict(eth="line")), ("8", dict(fw="m1017"))]
    for code, add in seq:
        if code == "3b" and nickel_mode != "by_product":
            continue
        kw.update(add)
        r, d = R.scenario(f"{'main' if nickel_mode == 'by_product' else 'alt_ni_case3'}|{ncv}|{code}", **kw)
        r.update(step=code, step_label=STEP_LABEL[code], path=("main" if nickel_mode == "by_product" else "alt_ni_case3"), ncv_scheme=ncv)   # path scheme; ncv_gj_t = value applied in this row
        rows.append(r); det[code] = d
    return rows, det, dict(kw)


def main():
    t0 = time.time()
    R = Runner(); ev = cm.Ev("chain")
    rep = R.reproduce()
    for k, v in rep.items():
        if isinstance(v, dict):
            ev.put(f"reproduction.{k}", int(all(v.values())), "1 = all byte-identical", f"scratch copy vs repository: {sorted(v)}", "EXACT", "-")
        else:
            ev.put(f"reproduction.{k}", v, "MWh" if k.endswith("mwh") else "TWh", "scratch copy /home/jin/v4w07_g0/chain vs repository (worktree 07e08f38)", "EXACT", "-")
    # ---------------------------------------------------------------------------------------------------------- validation against S2 / W11
    val = []
    s2 = pd.read_csv(cm.S2D / "s2/ID_S2_COMBINED.csv").set_index("scenario")
    r, _ = R.scenario("val S2 all (1-5)", ncv="v3", captive="central", nickel="case3", cem=True, steel=True, pp="spread", eth="noline")
    val.append(dict(check="S2 'all (1-5)' (v3 NCV, Case 3, pulp spread rule, ethylene 2019 base)", here_T=r["T_v2_2050_twh"], ref_T=float(s2.at["all (1-5)", "T_2050_twh"]),
                    here_other=r["other_2050_twh"], ref_other=float(s2.at["all (1-5)", "other_2050_twh"])))
    w = pd.read_csv(cm.W11D / "ncv/NCV_IMPACT_COUNTRY.csv"); w = w[(w.country == "ID") & (w["mode"] == "I")].set_index("case")
    for sch, case in (("unsd", "b"), ("ipcc", "d")):
        r, _ = R.scenario(f"val W11 ({case})", ncv=sch)
        val.append(dict(check=f"W11 NCV case ({case}) ID, mode I", here_T=r["T_v2_2050_twh"], ref_T=float(w.at[case, "T_v2_2050_twh"]), here_other=r["other_2050_twh"], ref_other=float(w.at[case, "other_2050_twh"])))
    wc = pd.read_csv(cm.W11D / "ncv/NCV_S1_COMBINED.csv"); wc = wc[(wc.level == "central") & (wc.scheme == "b")].iloc[0]
    r, _ = R.scenario("val W11 (b) + captive central", ncv="unsd", captive="central")
    val.append(dict(check="W11 NCV (b) + S1 captive central (NCV_S1_COMBINED)", here_T=r["T_v2_2050_twh"], ref_T=float(wc.T_v3 + wc.dT_combined),
                    here_other=r["other_2050_twh"], ref_other=float(wc.other_v3 + wc.dO_combined)))
    st = pd.read_csv(cm.S2D / "s2/ID_OTHER_SHARE_STEPS.csv").set_index("step")
    r, _ = R.scenario("val S2 fuelwood-low v3 line", ncv="v3", fw="m1017")
    val.append(dict(check="S2 section 4 fuelwood-low line, v3 row", here_T=r["T_v2_2050_twh"], ref_T=float(st.at["v3", "fw_low_T_2050_twh"]),
                    here_other=r["other_2050_twh"], ref_other=float(st.at["v3", "fw_low_other_2050_twh"])))
    V = pd.DataFrame(val); V["dev_T"] = V.here_T - V.ref_T; V["dev_other"] = V.here_other - V.ref_other
    if V[["dev_T", "dev_other"]].abs().max().max() > 1e-6:
        raise SystemExit(f"validation failed:\n{V.to_string()}")
    for v in V.itertuples():
        ev.put(f"validation.{v.check[:60]}.dev_T", v.dev_T, "TWh", v.check, "EXACT", "-")
        ev.put(f"validation.{v.check[:60]}.dev_other", v.dev_other, "TWh", v.check, "EXACT", "-")
    # ---------------------------------------------------------------------------------------------------------- step paths
    rows, details, finals = [], {}, {}
    for ncv in ("207", "v3", "unsd", "ipcc"):
        for nm in ("by_product", "case3"):
            rr, dd, kw = path(R, ncv, nm)
            rows += rr; details[f"{nm}|{ncv}"] = dd; finals[f"{nm}|{ncv}"] = kw
    S = pd.DataFrame(rows)
    # ---------------------------------------------------------------------------------------------------------- sensitivities on the main final
    base_kw = dict(finals["by_product|207"])
    sens_def = [("captive low", dict(captive="low")), ("captive mid", dict(captive="mid")), ("nickel Case 3 for all products (v3 / S2 unit energy)", dict(nickel="case3")),
                ("nickel NIUPPER (Case 3 x 3.571, S2)", dict(nickel="niupper")), ("ethylene excl. LINE (2019 base, u 0.85)", dict(eth="noline")),
                ("fuelwood 2020-2021 mean", dict(fw="m2021")), ("fuelwood UNSD 2019 (unchanged)", dict(fw=None)),
                ("pulp/paper S2 spread rule (biomass in T_v2, comparison)", dict(pp="spread")), ("pulp/paper literal 2024 base (closed loop)", dict(pp_case="literal2024")),
                ("bagasse also closed loop (UNSD bagasse 14.93 TWh out of 'other')", dict(bagasse=True)),
                ("NCV UNSD 24.48", dict(ncv="unsd")), ("NCV IPCC 18.9", dict(ncv="ipcc")), ("NCV v3 25.80", dict(ncv="v3"))]
    sens = []
    rb, _ = R.scenario("main final (207)", **base_kw); rb["sensitivity"] = "main final"; sens.append(rb)
    for lab, ch_ in sens_def:
        kw = dict(base_kw); kw.update(ch_)
        r, _ = R.scenario(f"sens: {lab}", **kw); r["sensitivity"] = lab; sens.append(r)
    # growth reading II, NCV step only (comparison, A3 item 9)
    for ncv in ("207", "unsd", "ipcc"):
        r2, _ = R.scenario(f"mode II NCV only {ncv}", ncv=ncv, mode="II"); r2["sensitivity"] = f"growth reading II (AEO8 anchor absolute), NCV {cm.NCV_LABEL[ncv]} only"; sens.append(r2)
        r1, _ = R.scenario(f"mode I NCV only {ncv}", ncv=ncv); r1["sensitivity"] = f"growth reading I, NCV {cm.NCV_LABEL[ncv]} only"; sens.append(r1)
    SE = pd.DataFrame(sens)
    R.ch.restore(); R.ch.unpatch()   # leave the scratch copy unmodified
    # ---------------------------------------------------------------------------------------------------------- tables
    v3T, v3O = float(S.iloc[0].T_v2_2050_twh), float(S.iloc[0].other_2050_twh)
    S["delta_T_twh"] = S.groupby(["path", "ncv_scheme"]).T_v2_2050_twh.diff().fillna(0.0)
    S["delta_TWh"] = S.groupby(["path", "ncv_scheme"]).other_2050_twh.diff().fillna(0.0)
    S["cum_delta_T_vs_v3_twh"] = S.T_v2_2050_twh - v3T; S["cum_delta_other_vs_v3_twh"] = S.other_2050_twh - v3O
    S["grade"] = S.step.map(STEP_GRADE); S["status"] = ["EXACT" if s == "0" else "PROPOSED (quantified, chain run)" for s in S.step]
    S.to_csv(cm.WORK / "ID_G0_SCENARIOS.csv", index=False, float_format="%.6f")
    out = S.rename(columns={"T_v2_2050_twh": "T_v2_2050_TWh", "other_2050_twh": "other_2050_TWh", **{f"other_{k}_twh": v for k, v in COLMAP.items()}})
    cols = ["step", "step_label", "path", "ncv_scheme", "ncv_gj_t", "T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_TWh", "elec", "heat_lt150", "heat_150_200",
            "heat_200_400", "heat_gt400", "oil", "gas", "coal", "biomass", "H2", "grade", "status", "growth_mode", "delta_T_twh", "cum_delta_T_vs_v3_twh",
            "cum_delta_other_vs_v3_twh", "industry_2019_twh", "other_2019_v2_twh", "ats_industry_2050_twh", "products_2050_twh", "implied_industry_fe_2050_twh",
            "aeo8_anchor_twh", "anchor_dev_twh", "anchor_dev_pct", "closed_loop_biomass_2019_twh", "closed_loop_biomass_2050_twh", "C_twh", "E_twh", "ncv_delta_2019_twh",
            "sub_nonferrous_nickel_twh", "sub_pulp_paper_twh", "sub_ethylene_twh", "sub_dispersed_twh", "sub_cement_twh", "sub_steel_twh"]
    out = out[[c for c in cols if c in out.columns]]
    order = {"207": 0, "v3": 1, "unsd": 2, "ipcc": 3}
    out = out.assign(_o=out.ncv_scheme.map(order), _p=(out.path != "main").astype(int)).sort_values(["_p", "_o"], kind="stable").drop(columns=["_o", "_p"])
    out.to_csv(cm.WORK / "ID_OTHER_SHARE_STEPS.csv", index=False, float_format="%.6f")
    SE["d_T_vs_main_twh"] = SE.T_v2_2050_twh - float(rb["T_v2_2050_twh"]); SE["d_other_vs_main_twh"] = SE.other_2050_twh - float(rb["other_2050_twh"])
    SE["d_T_vs_v3_twh"] = SE.T_v2_2050_twh - v3T
    SE.to_csv(cm.WORK / "ID_G0_SENSITIVITY.csv", index=False, float_format="%.6f")
    # ---------------------------------------------------------------------------------------------------------- evidence
    for r in S.itertuples():
        for k in ("T_v2_2050_twh", "other_2050_twh", "other_share", "delta_TWh", "delta_T_twh", "cum_delta_T_vs_v3_twh", "anchor_dev_twh", "anchor_dev_pct", "C_twh",
                  "closed_loop_biomass_2050_twh", "implied_industry_fe_2050_twh"):
            ev.put(f"step.{r.path}.{r.ncv_scheme}.{r.step}.{k}", getattr(r, k), "-" if k == "other_share" else ("%" if k.endswith("pct") else "TWh"),
                   "ID_OTHER_SHARE_STEPS.csv (scratch chain run)", "EXACT" if r.step == "0" else "PROPOSED (quantified)", r.grade)
    for r in SE.itertuples():
        for k in ("T_v2_2050_twh", "other_2050_twh", "other_share", "d_T_vs_main_twh", "d_other_vs_main_twh", "anchor_dev_twh"):
            ev.put(f"sens.{r.sensitivity}.{k}", getattr(r, k), "-" if k == "other_share" else "TWh", "ID_G0_SENSITIVITY.csv (scratch chain run)", "PROPOSED (quantified)", "C")
    ev.put("ncv.207_gj_t", cm.NCV["207"], "GJ/t", "decision 207 item 2 (HEESI average coal 3.4554 BOE/t, from 2023)", "PROPOSED (decided)", "B")
    ev.put("ncv.heesi_avg_coal_exact", cm.HEESI_AVG_COAL_EXACT, "GJ/t", "3.4554 BOE/t x 3.6/0.6130 GJ/BOE (W11 2.2); the instruction's 20.29 is used", "EXACT", "B")
    ev.put("anchor.aeo8_industry_2050_ID", R.anchor_mwh / 1e6, "TWh", "DEMAND_ANCHOR_AEO8_ATS.csv industry_anchor_mwh (RAS industry energy-use anchor)", "VERIFIED", "B")
    ev.put("anchor.tfec_2019_industry_ID", R.tfec19_mwh / 1e6, "TWh", "DEMAND_ANCHOR_AEO8_ATS.csv tfec_2019_Industry_mwh", "VERIFIED", "B")
    ev.put("niupper_scale", R.niupper_scale, "-", "v3_industry NIUPPER / (Wei Case 3 el + fuel)", "EXACT", "C")
    ev.extra.update(reproduction=rep, validation=V.to_dict("records"), inputs_sha256=R.inputs, timing_s=time.time() - t0, patch=dict(old=cm.PATCH_OLD, new=cm.PATCH_NEW))
    ev.write(cm.WORK / "evidence/_chain_evidence.json")
    keep = {k: v for k, v in details.items() if k in ("by_product|207", "case3|207", "by_product|v3")}
    cm.jdump(dict(details=keep, finals=finals), cm.WORK / "evidence/_chain_detail.json")
    pd.set_option("display.width", 280); pd.set_option("display.max_columns", 30)
    print(json.dumps({k: v for k, v in rep.items() if not isinstance(v, dict)})); print(V.round(9).to_string())
    print(out[["step", "step_label", "path", "ncv_scheme", "T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_TWh", "delta_T_twh", "anchor_dev_twh", "anchor_dev_pct"]].round(3).to_string())
    print(SE[["sensitivity", "T_v2_2050_twh", "other_2050_twh", "other_share", "d_T_vs_main_twh", "d_other_vs_main_twh"]].round(3).to_string())
    print("seconds", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
