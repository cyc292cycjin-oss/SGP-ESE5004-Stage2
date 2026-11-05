"""G2-7: combined quantification for Viet Nam in the scratch copy (B-G2 item 5; A6 tables; template step 9).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_steps.py

Two NCV schemes (A3 item 7): 'v3' (25.8012 GJ/t) and '207' (UNSD 23.446 GJ/t, decision 207 default); the NCV is applied first at the UNSD
row level (ATS industry coal base and the UNSD cache cells), every tonne-based deduction (captive coal) uses the same NCV.
Cumulative steps (each PROPOSED, nothing implemented in the repository):
  0 v3 (scheme 207: NCV only)
  1 dispersed split: hybrid (UNSD explicit rows kept, steel coke stays in steel, bagasse to food, UNSD 2020 electricity rows of steel and
    chemicals back-cast; the n.e.s. rest by APEC 2022) - decomposition only, T_v2 unchanged by construction (v3 VN rule)
  2 captive coal option (b), central = 0 (GIPT 1,010 MW is covered by the UNSD autoproducer coal in transformation)
  3 steel: 2019 boundary aligned by step 1, 2050 and space unchanged in total (spatial shares: v4w07g2_nodes.py)
  4 cement correction (ii): grinding electricity on USGS 2019 cement 105.533 Mt
  5 pulp and paper (closed-loop rule): purchased energy only; own black liquor outside T_v2
  6 glass (ETSAP 2020) and alumina (USGS)
  7 biomass: keep the model fuelwood value (G2-5) - no change
  8 industry diesel lost by the truncated UNdata export (3,016 kt), growth mode I
Sensitivities on the final line (scheme 207). Writes VN_OTHER_SHARE_STEPS.csv, VN_SUBSECTORS_V4.csv, VN_CAPTIVE.csv, tables/VN_SENSITIVITIES.csv,
tables/VN_STEP_DISPERSED_ROWS.csv, tables/VN_STEPS_LONG.csv, evidence/_steps_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402
import v4w07g2_ncv as nv   # noqa: E402
import v4w07g2_split as sp   # noqa: E402
import v4w07g2_unsd as un   # noqa: E402

FF = cm.frozen_factors()
DIESEL_KT = {"iron and steel": 102.0, "chemical and petrochemical": 79.0, "other": 2835.0}   # SDMX 4670 2019 (missing from the export)
CEM_USGS_2019_T = 105533.0e3
NCV = {"v3": nv.V3_GJ, "207": 23.446, "c": 21.695, "d": 26.7}   # c: APEC 2022 VN anthracite; d: IPCC anthracite (W11 schemes)


class Case:
    """One configuration of edits (NCV, diesel, captive, products) -> matrices, moves and the chain call."""

    def __init__(self, ncv: str = "v3", split: str = "hybrid", captive: dict | None = None, cement_ii: bool = False, pp: str | None = None,
                 glass_alumina: bool = False, diesel: str | None = None, fuelwood_km3: float | None = None, bagasse_out: bool = False,
                 ap_fuelwood_in: bool = False, ethylene: bool = False):
        self.__dict__.update(locals()); del self.__dict__["self"]


def build(case: Case, ci: dict, bio: dict, A: pd.DataFrame, ats_e19: dict) -> dict:
    """Return the keyword arguments of Chain.run and the 2050 explicit extras for one case."""
    base_delta = {c: 0.0 for c in cm.CARS19}; cache_ratio = {}; cache_add = {}; d1_delta = None
    # --- NCV (UNSD row level first) ---
    if case.ncv != "v3":
        bd, cr = nv.ncv_edit(NCV[case.ncv]); base_delta["coal"] += bd["coal"]; cache_ratio.update(cr)
    # --- fuelwood vintage / bagasse / autoproducer fuelwood (biomass, all in the UNSD 'other' cell) ---
    bag_mwh = bio["bagasse_2019_export_kt"] * FF["Bagasse"] * 1e6
    if case.fuelwood_km3 is not None:
        d = (case.fuelwood_km3 - bio["fuelwood_industry_2019_export_km3"]) * FF["Fuelwood"] * 1e6
        base_delta["biomass"] += d; cache_add[("biomass", "other")] = cache_add.get(("biomass", "other"), 0.0) + d
    if case.bagasse_out:
        base_delta["biomass"] -= bag_mwh; cache_add[("biomass", "other")] = cache_add.get(("biomass", "other"), 0.0) - bag_mwh; bag_mwh = 0.0
    if case.ap_fuelwood_in:
        d = 4100.426929 * FF["Fuelwood"] * 1e6
        base_delta["biomass"] += d; cache_add[("biomass", "other")] = cache_add.get(("biomass", "other"), 0.0) + d
    # --- diesel (export truncation) ---
    nes_diesel = 0.0
    if case.diesel:
        tot = sum(DIESEL_KT.values()) * FF["Gas Oil/ Diesel Oil"] * 1e6
        for sub, kt in DIESEL_KT.items():
            cache_add[("oil", sub)] = cache_add.get(("oil", sub), 0.0) + kt * FF["Gas Oil/ Diesel Oil"] * 1e6
        nes_diesel = DIESEL_KT["other"] * FF["Gas Oil/ Diesel Oil"] * 1e6
        if case.diesel == "I":
            base_delta["oil"] += tot
        else:
            d1_delta = {"oil": tot}
    # --- matrices ---
    U = sp.unsd_matrix(cache_ratio, cache_add)
    if case.split == "hybrid" or case.split == "hybrid_no_el2020" or case.split == "hybrid_yearadj":
        U_h = U.copy(); U_h.at["other", "oil"] -= nes_diesel   # the n.e.s. diesel is spread separately (all APEC oil rows except steel / chemicals)
        Aw = A.copy()
        if case.split == "hybrid_yearadj":
            for sub, (q19, q22, _) in un.ACT_2019_2022.items():
                Aw.loc[sub] = Aw.loc[sub] * q19 / q22
        H = un.hybrid(U_h, Aw, bag_mwh, None if case.split == "hybrid_no_el2020" else sp.EL_ROWS)
        if nes_diesel:
            w = Aw["oil"].copy(); w[["iron and steel", "chemical and petrochemical"]] = 0.0
            H["oil"] += nes_diesel * w / w.sum()
        M = H
    elif case.split == "apec2022":
        M = A.copy()
    elif case.split == "unsd_only":
        M = U.copy()
    else:
        raise ValueError(case.split)
    # energy matrices (MWh of sub19) after the edits, for the allocation of the moves
    e19 = {c: ats_e19[c] + base_delta[c] + (d1_delta or {}).get(c, 0.0) for c in cm.CARS19}   # mode II: the ATS base is the edited D1 base
    EU = pd.DataFrame({c: e19[c] * U[c] / U[c].sum() if U[c].sum() else 0.0 * U[c] for c in cm.CARS19})
    EM = pd.DataFrame({c: e19[c] * M[c] / M[c].sum() if M[c].sum() else 0.0 * M[c] for c in cm.CARS19})
    mu, ma, extra = [], [], {}

    def take(E, row, amounts, moves, label):
        for c, amt in amounts.items():
            if amt <= 0:
                continue
            a = min(amt, max(0.0, float(E.at[row, c]))); rest = amt - a
            if a > 0:
                moves.append((row, c, a)); E.at[row, c] -= a
            if rest > 1e-6:
                b = min(rest, max(0.0, float(E.at["other", c]))); rest2 = rest - b
                if b > 0:
                    moves.append(("other", c, b)); E.at["other", c] -= b
                if rest2 > 1e-6:   # the remaining n.e.s. cells of the carrier, pro rata (they hold the spread UNSD n.e.s. amount)
                    pool = E[c].drop([row, "other"]).clip(lower=0.0)
                    if pool.sum() + 1e-6 < rest2:
                        raise ValueError(f"{label}: {c} rest {rest2} exceeds the remaining cells {pool.sum()}")
                    for r_, x in (rest2 * pool / pool.sum()).items():
                        if x > 0:
                            moves.append((r_, c, x)); E.at[r_, c] -= x

    def spread_fuel(E, row, fuel):
        f = {c: max(0.0, float(E.at[row, c])) for c in cm.FUELS}; s = sum(f.values())
        if s <= 0:
            f = {c: max(0.0, float(E.at["other", c])) for c in cm.FUELS}; s = sum(f.values())
        return {c: fuel * v / s for c, v in f.items()}

    # --- captive (b) (tonnes first, energy at the case NCV) ---
    if case.captive:
        C = case.captive["coal_kt"] * NCV[case.ncv] / 3.6 * 1e3; E_el = case.captive["E_mwh"]
        w = EM["coal"].copy(); w[["iron and steel", "chemical and petrochemical"]] = 0.0   # the n.e.s. coal cells (where captive coal would sit)
        for row, x in (C * w / w.sum()).items():
            if x > 0:
                ma.append((row, "coal", x)); EM.at[row, "coal"] -= x
        mu.append(("other", "coal", C)); EU.at["other", "coal"] -= C
        we = EM["electricity"] / EM["electricity"].sum()
        for row, x in (E_el * we).items():
            ma.append((row, "electricity", -x)); EM.at[row, "electricity"] += x
        mu.append(("other", "electricity", -E_el)); EU.at["other", "electricity"] += E_el
    # --- pulp and paper ---
    if case.pp:
        amt = {k: v for k, v in ci["pp_2019_purchased_mwh"].items() if v > 0}
        take(EM, "paper pulp and print", amt, ma, "pp apec-run"); take(EU, "paper pulp and print", amt, mu, "pp unsd-run")
        extra["pulp_paper"] = ci["pp_2050_main"] if case.pp == "main" else ci["pp_2050_literal"]
    # --- glass and alumina ---
    if case.glass_alumina:
        g = ci["glass_2019"]; amt = {"electricity": g["electricity"], **spread_fuel(EM, "non-metallic minerals", g["fuel"])}
        take(EM, "non-metallic minerals", amt, ma, "glass apec-run"); take(EU, "non-metallic minerals", amt, mu, "glass unsd-run")
        a_ = ci["alumina_2019"]; amt = {"electricity": a_["electricity"], **spread_fuel(EM, "other", a_["fuel"])}
        take(EM, "other", amt, ma, "alumina apec-run"); take(EU, "other", amt, mu, "alumina unsd-run")
        extra["glass"] = ci["glass_2050"]; extra["alumina"] = ci["alumina_2050"]
    if case.ethylene:
        extra["ethylene_r4"] = ci["ethylene_2050"]
    kw = dict(moves_unsd=mu, moves_apec=ma, base_delta={k: v for k, v in base_delta.items() if v},
              apec_override=M.rename(columns={c: cm.APEC_COL[c] for c in cm.CARS19}), cache_ratio=cache_ratio, cache_add=cache_add,
              cem_el_t19=CEM_USGS_2019_T if case.cement_ii else None, d1_delta=d1_delta)
    return kw, extra


def row_out(step, scheme, name, lay, prev_other, base, grade, res, extra):
    o = cm.band_row(lay)
    d = dict(step=step, step_name=name, ncv_scheme=scheme, T_v2_2050_TWh=lay["T"] / 1e6, other_2050_TWh=lay["other_total"] / 1e6, other_share=lay["other_total"] / lay["T"],
             delta_TWh=(lay["other_total"] - prev_other) / 1e6 if prev_other is not None else 0.0, **o, grade=grade,
             delta_T_vs_v3_TWh=(lay["T"] - base["T"]) / 1e6, delta_other_vs_v3_TWh=(lay["other_total"] - base["other_total"]) / 1e6,
             dispersed_2050_TWh=lay["by_sub"].get("dispersed", 0.0) / 1e6, steel_2050_TWh=lay["by_sub"].get("steel", 0.0) / 1e6, cement_2050_TWh=lay["by_sub"].get("cement", 0.0) / 1e6,
             ammonia_2050_TWh=lay["by_sub"].get("ammonia", 0.0) / 1e6, new_explicit_2050_TWh=sum(sum(v.values()) for v in extra.values()) / 1e6,
             other_scale=lay["scale"], T_decomposition_run_TWh=lay["T_apec_run"] / 1e6, industry_2019_TWh=sum(res["e19"].values()) / 1e6,
             other_2019_apec_run_TWh=float(res["ob_apec"].other_2019_mwh) / 1e6)
    return d


def main():
    v3 = cm.import_v3(); fut = v3.future_vectors()
    ci = json.loads((cm.WORK / "evidence/_chain_inputs.json").read_text())
    bio = json.loads((cm.WORK / "evidence/_biomass_chain_inputs.json").read_text())
    eth = pd.read_csv(cm.WORK / "tables/VN_ETHYLENE_SENS.csv").set_index("level")
    ci["ethylene_2050"] = cm.vec2050("HVC", float(eth.at["central", "hvc_2050_t"])); ci["ethylene_2050"]["naphtha"] = 0.0
    ci["ethylene_2050"] = {k: v for k, v in ci["ethylene_2050"].items() if k in cm.OUTC}
    cap = pd.read_csv(cm.WORK / "tables/VN_CAPTIVE_ESTIMATE.csv").set_index("level")
    A = pd.read_csv(cm.REPO / cm.APEC_REL).set_index("cache_subsector")
    A = A[[cm.APEC_COL[c] for c in cm.CARS19]].rename(columns={v: k for k, v in cm.APEC_COL.items()}).reindex(sp.unsd_matrix().index).fillna(0.0).astype(float)
    sp.matrices()   # sets EL_ROWS
    ats = pd.read_csv(cm.REPO / cm.ATS_REL)
    ats_e19 = {c: float(ats[(ats.country == cm.CC) & (ats.sector == "Industry") & (ats.carrier == c)].base_2019_mwh.iloc[0]) for c in cm.CARS19}
    ch = cm.Chain(); ch.copy(); ch.patch()

    def run(case: Case):
        kw, extra = build(case, ci, bio, A, ats_e19)
        res = ch.run(**kw)
        lay = cm.v3_layer(v3, res, fut, extra)
        return lay, res, extra

    # reproduction with the patched s3_0 and no environment variable (v3 split = APEC 2022 matrix)
    lay0, res0, _ = run(Case(split="apec2022"))
    sub = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    sub = sub[(sub.case == "main") & (sub.country == cm.CC)]
    dev = abs(lay0["other_total"] - sub[sub.subsector == "other"].mwh_2050.sum()) + abs(lay0["T"] - sub.mwh_2050.sum())
    if dev > 1e-3:
        raise SystemExit(f"STOP: patched copy does not reproduce the repository VN row (dev {dev} MWh)")
    steps = [(0, "v3", dict(split="apec2022")),
             (1, "dispersed split: hybrid (UNSD rows kept, steel coke in steel, bagasse to food, UNSD 2020 electricity rows; n.e.s. by APEC 2022)", dict(split="hybrid")),
             (2, "captive coal option (b), central = 0 (GIPT 1,010 MW covered by UNSD autoproducer coal 2,578.6 kt)", dict(split="hybrid")),
             (3, "steel: 2019 boundary aligned in step 1; 2050 total unchanged (space only)", dict(split="hybrid")),
             (4, "cement correction (ii): grinding electricity on USGS 2019 cement 105.533 Mt", dict(split="hybrid", cement_ii=True)),
             (5, "pulp and paper (closed-loop rule: purchased energy; own black liquor outside T_v2)", dict(split="hybrid", cement_ii=True, pp="main")),
             (6, "glass (ETSAP 2020) and alumina (USGS 2022 base)", dict(split="hybrid", cement_ii=True, pp="main", glass_alumina=True)),
             (7, "biomass: model fuelwood value kept (G2-5)", dict(split="hybrid", cement_ii=True, pp="main", glass_alumina=True)),
             (8, "industry diesel lost by the truncated UNdata export (3,016 kt), growth mode I", dict(split="hybrid", cement_ii=True, pp="main", glass_alumina=True, diesel="I"))]
    grades = {0: "EXACT", 1: "C", 2: "C", 3: "C", 4: "C", 5: "C", 6: "C", 7: "C", 8: "B"}
    out, longrows, disp, lays = [], [], [], {}
    base_v3 = lay0
    for scheme in ("v3", "207"):
        prev = None
        for k, name, kw in steps:
            lay, res, extra = run(Case(ncv=scheme, **kw))
            lays[(scheme, k)] = (lay, res, extra)
            r = row_out(k, scheme, name, lay, prev, base_v3, grades[k], res, extra)
            out.append(r); prev = lay["other_total"]
            for sname, v in lay["by_sub"].items():
                longrows.append(dict(step=k, ncv_scheme=scheme, subsector=sname, twh_2050=v / 1e6))
            for rr, x in sp.dispersed_rows(res["pz_apec"]).items():
                disp.append(dict(step=k, ncv_scheme=scheme, unsd_row=rr, dispersed_2050_twh=x))
    S = pd.DataFrame(out)
    cols = ["step", "ncv_scheme", "T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_TWh", "elec", "heat_lt150", "heat_150_200", "heat_200_400", "heat_gt400",
            "oil", "gas", "coal", "biomass", "H2", "grade"]
    S[cols + [c for c in S.columns if c not in cols]].to_csv(cm.WORK / "VN_OTHER_SHARE_STEPS.csv", index=False, float_format="%.6f")
    pd.DataFrame(longrows).to_csv(cm.WORK / "tables/VN_STEPS_LONG.csv", index=False, float_format="%.6f")
    pd.DataFrame(disp).to_csv(cm.WORK / "tables/VN_STEP_DISPERSED_ROWS.csv", index=False, float_format="%.6f")
    # ---------------- sensitivities on the final line (scheme 207) ----------------
    fin = dict(split="hybrid", cement_ii=True, pp="main", glass_alumina=True, diesel="I")
    fin7 = dict(split="hybrid", cement_ii=True, pp="main", glass_alumina=True)
    sens = [("main (step 8, NCV 207)", Case(ncv="207", **fin)),
            ("main without diesel (step 7, NCV 207)", Case(ncv="207", **fin7)),
            ("split: v3 APEC 2022 shares", Case(ncv="207", **{**fin, "split": "apec2022"})),
            ("split: hybrid without the UNSD 2020 electricity rows", Case(ncv="207", **{**fin, "split": "hybrid_no_el2020"})),
            ("split: hybrid with APEC rows scaled to 2019 activity", Case(ncv="207", **{**fin, "split": "hybrid_yearadj"})),
            ("split: UNSD only (v2 decomposition)", Case(ncv="207", **{**fin, "split": "unsd_only"})),
            ("NCV (c) APEC 2022 anthracite 21.695", Case(ncv="c", **fin)),
            ("NCV (d) IPCC anthracite 26.7", Case(ncv="d", **fin)),
            ("NCV v3 (25.8)", Case(ncv="v3", **fin)),
            ("captive mid (75 kt in industry)", Case(ncv="207", **fin, captive=dict(coal_kt=float(cap.at["mid", "coal_in_industry_kt"]), E_mwh=float(cap.at["mid", "E_twh"]) * 1e6))),
            ("captive high (3,657 kt, no deduction)", Case(ncv="207", **fin, captive=dict(coal_kt=float(cap.at["high", "coal_in_industry_kt"]), E_mwh=float(cap.at["high", "E_twh"]) * 1e6))),
            ("pulp and paper: rule read literally (all biomass rows outside T_v2)", Case(ncv="207", **{**fin, "pp": "literal"})),
            ("cement without correction (ii)", Case(ncv="207", **{**fin, "cement_ii": False})),
            ("fuelwood low: SDMX 2026 vintage 7,260 thousand m3", Case(ncv="207", **fin, fuelwood_km3=bio["fuelwood_industry_2019_sdmx_km3"])),
            ("bagasse outside T_v2 (closed-loop reading)", Case(ncv="207", **fin, bagasse_out=True)),
            ("autoproducer fuelwood moved into industry (+4,100 thousand m3)", Case(ncv="207", **fin, ap_fuelwood_in=True)),
            ("diesel in growth mode II (AEO8 anchors absolute)", Case(ncv="207", **{**fin, "diesel": "II"})),
            ("ethylene R4: Long Son 950 kt from 2023 (explicit 2050 only)", Case(ncv="207", **fin, ethylene=True))]
    srows = []
    lay_main = None
    for lab, c in sens:
        lay, res, extra = run(c)
        if lay_main is None:
            lay_main = lay
        srows.append(dict(sensitivity=lab, T_v2_2050_TWh=lay["T"] / 1e6, other_2050_TWh=lay["other_total"] / 1e6, other_share=lay["other_total"] / lay["T"],
                          dispersed_2050_TWh=lay["by_sub"].get("dispersed", 0.0) / 1e6, delta_T_vs_main_TWh=(lay["T"] - lay_main["T"]) / 1e6,
                          delta_other_vs_main_TWh=(lay["other_total"] - lay_main["other_total"]) / 1e6, delta_T_vs_v3_TWh=(lay["T"] - base_v3["T"]) / 1e6,
                          T_from_decomposition_run_TWh=lay["T_apec_run"] / 1e6 + sum(sum(v.values()) for v in extra.values()) / 1e6,
                          other_if_T_from_decomposition_run_TWh=(lay["T_apec_run"] + sum(sum(v.values()) for v in extra.values()) - lay["explicit"]) / 1e6,
                          industry_2019_TWh=sum(res["e19"].values()) / 1e6, industry_multiplier=float(res["main"].industry_multiplier)))
    SE = pd.DataFrame(srows); SE.to_csv(cm.WORK / "tables/VN_SENSITIVITIES.csv", index=False, float_format="%.6f")
    ch.unpatch(); ch.restore()
    # ---------------- A6: sub-sectors (final line, scheme 207) ----------------
    lay, res, extra = lays[("207", 8)]
    pz = res["pz_apec"]
    sub_rows = []
    rule = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_2050_M08B.csv").set_index("country").loc[cm.CC]
    for k, v in lay["explicit_carriers"].items():
        if k == "dispersed":
            continue
        meta = {"steel": ("crude steel: 30 % H2-DRI + 70 % scrap EAF (PyPSA-Eur 2050)", "worldsteel 2024 (v3 base)", 2024, rule.steel_base_mt * 1e6, rule.steel_2050_mt * 1e6, "PyPSA-Eur 2050", "iron and steel (UNSD coke + LPG/FO + UNSD 2020 electricity back-cast), hybrid"),
                "cement": ("cement (PyPSA-Eur 2050 ratio)", "USGS MYB 2023 cement T22 (v3 base)", 2023, rule.cement_base_mt * 1e6, rule.cement_2050_mt * 1e6, "PyPSA-Eur 2050 0.8655 MWh/t", "non-metallic minerals row, excess from other (correction ii)"),
                "ammonia": ("ammonia product (v3)", "USGS MYB 2022 nitrogen T12 (v3)", 2019, rule.ammonia_base_mt * 1e6, rule.ammonia_2050_mt * 1e6, "5.166 MWh NH3/t", "chemical row (DFX F2)"),
                "pulp_paper": ("pulp + paper (PyPSA-Eur 2050), own black liquor outside T_v2", "FAOSTAT FO, last year with new information", "item-wise", np.nan, np.nan, "PyPSA-Eur 2050 (biomass rows minus own black liquor)", "paper pulp and print row, excess from other"),
                "glass": ("glass (PyPSA-Eur 2050, all-electric)", "ETSAP v2.1.0 production 2020", 2020, 2155.8e3, 2155.8e3 * cm.growth(2020), "PyPSA-Eur 2050", "non-metallic minerals row"),
                "alumina": ("alumina, Bayer (PyPSA-Eur 2050)", "USGS MYB 2022 VN table 1", 2022, 1426000.0, 1426000.0 * cm.growth(2022), "PyPSA-Eur 2050", "other (no non-ferrous energy in UNSD / APEC)")}.get(k)
        if meta is None:
            continue
        ded = {"steel": float(pz[pz.subsector == "iron and steel"].mwh_2019.sum()), "cement": float(pz[pz.subsector == "cement"].mwh_2019.sum()),
               "ammonia": 0.0, "pulp_paper": sum(ci["pp_2019_purchased_mwh"].values()), "glass": sum(ci["glass_2019"].values()), "alumina": sum(ci["alumina_2019"].values())}[k]
        sub_rows.append(dict(subsector=k, route=meta[0], activity_source=meta[1], base_year=meta[2], activity_base=meta[3], activity_2050=meta[4], sec_source=meta[5],
                             energy_2019_deducted_TWh=ded / 1e6, deducted_from_row=meta[6], energy_2050_TWh=sum(v.values()) / 1e6,
                             **{f"c_{c}": v.get(c, 0.0) / 1e6 for c in cm.OUTC}, closed_loop_biomass_TWh=(ci["pp_closed_loop_2050_mwh"] / 1e6 if k == "pulp_paper" else 0.0),
                             grade="B (activity) / C (energy)"))
    for rr, x in sp.dispersed_rows(pz).items():
        r19 = float(pz[(pz.subsector == rr)].mwh_2019.sum())
        sub_rows.append(dict(subsector=f"dispersed: {rr}", route="energy fallback x efficiency factor (s3_0)", activity_source="UNSD 2019 x hybrid split", base_year=2019,
                             activity_base=np.nan, activity_2050=np.nan, sec_source="PyPSA-Eur mapped sectors", energy_2019_deducted_TWh=r19 / 1e6, deducted_from_row=rr,
                             energy_2050_TWh=x, closed_loop_biomass_TWh=0.0, grade="C"))
    sub_rows.append(dict(subsector="other", route="useful heat bands (v3)", activity_source="residual (D163-6 a)", base_year=2019, energy_2050_TWh=lay["other_total"] / 1e6,
                         **{f"c_{c}": lay["other"].get(c, 0.0) / 1e6 for c in cm.OUTC}, grade="C"))
    SB = pd.DataFrame(sub_rows); SB.to_csv(cm.WORK / "VN_SUBSECTORS_V4.csv", index=False, float_format="%.6f")
    # ---------------- A6: captive ----------------
    capt_eff = {}
    for lab in ("captive mid (75 kt in industry)", "captive high (3,657 kt, no deduction)"):
        z = SE.set_index("sensitivity").loc[lab]
        capt_eff[lab] = float(z.delta_T_vs_main_TWh)
    CP = pd.DataFrame([dict(inequality_result="holds: autoproducer combustible output 4,200 GWh (E) < fuel in transformation 33.46 TWh; implied efficiency 0.13",
                            gipt_captive_MW_2019=1010.0, gipt_captive_MW_2019_types="iron & steel 900 (Ha Tinh Formosa 450, Nhon Trach Formosa 450 - type questionable), pulp & paper 50, agriculture (Vedan) 60",
                            C_low_kt=float(cap.at["low", "coal_in_industry_kt"]), C_low_TWh_v3=float(cap.at["low", "C_twh_v3"]), C_low_TWh_207=float(cap.at["low", "C_twh_unsd_ncv"]),
                            C_central_kt=0.0, C_central_TWh=0.0,
                            C_mid_kt=float(cap.at["mid", "coal_in_industry_kt"]), C_mid_TWh_v3=float(cap.at["mid", "C_twh_v3"]), C_mid_TWh_207=float(cap.at["mid", "C_twh_unsd_ncv"]),
                            C_high_kt=float(cap.at["high", "coal_in_industry_kt"]), C_high_TWh_v3=float(cap.at["high", "C_twh_v3"]), C_high_TWh_207=float(cap.at["high", "C_twh_unsd_ncv"]),
                            E_low_TWh=float(cap.at["low", "E_twh"]), E_mid_TWh=float(cap.at["mid", "E_twh"]), E_high_TWh=float(cap.at["high", "E_twh"]),
                            central_rule="central = low (0): the GIPT mid estimate of captive coal (2,654 kt) equals the UNSD autoproducer coal already in transformation (2,578.6 kt) within 3 %",
                            option_b_effect_2050="central 0; T_v2 change mid %.2f / high %.2f TWh (scheme 207, final line)" % (capt_eff["captive mid (75 kt in industry)"], capt_eff["captive high (3,657 kt, no deduction)"]))])
    CP.to_csv(cm.WORK / "VN_CAPTIVE.csv", index=False, float_format="%.6f")
    # evidence
    ev = cm.Ev("steps")
    for r in S.itertuples():
        for k in ("T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_TWh", "dispersed_2050_TWh"):
            ev.put(f"{r.ncv_scheme}.step{r.step}.{k}", float(getattr(r, k)), "share" if k == "other_share" else "TWh", f"scratch chain: {r.step_name}", "EXACT" if r.step == 0 and r.ncv_scheme == "v3" else "PROPOSED", r.grade)
    for r in SE.itertuples():
        for k in ("T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_T_vs_main_TWh", "delta_other_vs_main_TWh", "other_if_T_from_decomposition_run_TWh"):
            ev.put(f"sens.{r.Index:02d}.{k}", float(getattr(r, k)), "share" if k == "other_share" else "TWh", f"sensitivity: {r.sensitivity}", "PROPOSED", "C")
    for r in SB.itertuples():
        ev.put(f"sub.{r.subsector}.energy_2050", float(r.energy_2050_TWh), "TWh", "VN_SUBSECTORS_V4.csv (final line, NCV 207)", "PROPOSED", "C")
    ev.put("reproduction.patched_copy_dev_mwh", dev, "MWh", "patched s3_0 without the environment variable vs repository VN row", "EXACT", "A")
    ev.write(cm.WORK / "evidence/_steps_evidence.json")
    pd.set_option("display.width", 250)
    print(S[["step", "ncv_scheme", "T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_TWh", "dispersed_2050_TWh", "new_explicit_2050_TWh", "delta_T_vs_v3_TWh", "industry_2019_TWh"]].round(3).to_string())
    print(SE[["sensitivity", "T_v2_2050_TWh", "other_2050_TWh", "other_share", "delta_T_vs_main_TWh", "delta_other_vs_main_TWh", "other_if_T_from_decomposition_run_TWh"]].round(3).to_string())
    print(SB[["subsector", "energy_2019_deducted_TWh", "energy_2050_TWh"]].round(3).to_string())


if __name__ == "__main__":
    main()
