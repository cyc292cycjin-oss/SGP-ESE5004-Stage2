"""I2 section 3 item 4: sensitivity inventory (I2 re-runs on the final state, biomass-potential variants, and the session / I1 sensitivities that
were not re-run) and the ten largest by their effect on T_v2, 'other' or the solid-biomass potential.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_sens.py

Magnitude = max(|dT_v2|, |d other|, |d potential|) in TWh (2050), largest single-country or ASEAN effect. Session values are on their own base
(v3 export base, reading I) and are listed as order of magnitude only (status INFERENCE for the I2 state); I2 re-runs are EXACT for the stated
rule (status PROPOSED / EXACT chain). Duplicates (a session variant that the I2 re-run covers) are dropped in favour of the I2 value.
Writes SENSITIVITY_TOP10.csv, tables/I2_SENSITIVITY_ALL.csv, evidence/I2_sens.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402

W = cm.W07


def main():
    ev = cm.Evidence("I2_sens"); rows = []
    SR = pd.read_csv(cm.TABLES / "I2_SENSITIVITY_RUNS.csv")
    for nm, g in SR.groupby("sensitivity"):
        a = g[g.country == "ASEAN11"].iloc[0]; c = g[g.country != "ASEAN11"]
        top = c.loc[c.dT_v2_TWh.abs().idxmax()]; topo = c.loc[c.dOther_TWh.abs().idxmax()]
        rows.append(dict(sensitivity=a.label, key=nm, source="I2 re-run on the final state (S7)", re_run_in_I2=True, scope="ASEAN11",
                         dT_v2_TWh=a.dT_v2_TWh, dOther_TWh=a.dOther_TWh, dPotential_TWh=0.0, dOverflow_TWh=a.dOverflow_TWh,
                         largest_country=f"{top.country} {top.dT_v2_TWh:+.2f} (T_v2); {topo.country} {topo.dOther_TWh:+.2f} (other)",
                         magnitude_TWh=max(abs(a.dT_v2_TWh), abs(a.dOther_TWh), abs(top.dT_v2_TWh), abs(topo.dOther_TWh)), status="PROPOSED (quantified, chain run)", grade="C"))
    # ---- biomass potential variants
    B = pd.read_csv(cm.I2 / "BIOMASS_POTENTIAL_ADJ.csv")
    pks = B[B.category == "oil_palm_pks"].groupby("country").potential_v3_TWh.sum()
    for s_, lab in ((0.0, "PKS 厂内份额 0 %（潜力只扣纤维）"), (1.0, "PKS 厂内份额 100 %")):
        d = float(((0.5 - s_) * pks).sum())
        rows.append(dict(sensitivity=lab, key=f"pks_{int(s_ * 100)}", source="I2 biomass table", re_run_in_I2=True, scope="ASEAN11 potential", dT_v2_TWh=0.0, dOther_TWh=0.0, dPotential_TWh=d,
                         largest_country=f"ID {float((0.5 - s_) * pks.get('ID', 0.0)):+.2f}", magnitude_TWh=abs(d), status="PROPOSED (quantified)", grade="D"))
    ov = pd.read_csv(cm.G["W12"] / "tables/W12_3_BAGASSE_SUPPLY_OVERESTIMATE.csv")
    d = -float((ov.overestimate_mwh_R1.fillna(0) - ov.overestimate_mwh_R2.fillna(0)).sum()) / 1e6
    rows.append(dict(sensitivity="蔗渣热值读法 R1（湿基 7.718 GJ/t）代替 R2", key="bagasse_R1", source="W12 table", re_run_in_I2=False, scope="ASEAN11 potential", dT_v2_TWh=0.0, dOther_TWh=0.0,
                     dPotential_TWh=d, largest_country="TH (R1 31.89 vs R2 5.22 TWh)", magnitude_TWh=abs(d), status="PROPOSED (quantified, W12)", grade="C"))
    tot = B[(B.category == "TOTAL solid") & (B.country == "ASEAN11")].iloc[0]
    d = -float(tot.F4_self_use_TWh)
    rows.append(dict(sensitivity="潜力不扣厂内自用残渣（F4 关）", key="f4_off", source="I2 biomass table", re_run_in_I2=True, scope="ASEAN11 potential", dT_v2_TWh=0.0, dOther_TWh=0.0,
                     dPotential_TWh=d, largest_country=f"ID {-float(B[(B.category == 'TOTAL solid') & (B.country == 'ID')].F4_self_use_TWh.iloc[0]):+.2f}", magnitude_TWh=abs(d),
                     status="PROPOSED (quantified)", grade="C"))
    # ---- session sensitivities (not re-run; own base)
    def add(lab, src, cc, dT, dO, key, dup=None):
        rows.append(dict(sensitivity=lab, key=key, source=src, re_run_in_I2=False, scope=cc, dT_v2_TWh=dT, dOther_TWh=dO, dPotential_TWh=0.0, dOverflow_TWh=None, largest_country=cc,
                         magnitude_TWh=max(abs(dT), abs(dO)), status="INFERENCE for I2 (session value on the export base, reading I)", grade="C", duplicate_of=dup or ""))
    G0 = pd.read_csv(W / "G0/ID_G0_SENSITIVITY.csv")
    dup0 = {"captive low": "id_captive_low", "captive mid": "id_captive_mid", "nickel Case 3": "ni_case4", "nickel NIUPPER": "ni_upper", "ethylene excl. LINE": "no_new_plants",
            "fuelwood 2020-2021": "fw2021", "fuelwood UNSD 2019": "fwsdmx", "pulp/paper S2 spread": "", "bagasse also closed": "res_bagasse_kept"}
    for r in G0.itertuples():
        if r.sensitivity in ("main final",) or str(r.sensitivity).startswith("growth reading"):
            continue
        dup = next((v for k, v in dup0.items() if str(r.sensitivity).startswith(k) and v), None)
        add(f"ID：{r.sensitivity}", "G0 ID_G0_SENSITIVITY.csv", "ID", float(r.d_T_vs_main_twh), float(r.d_other_vs_main_twh), f"g0_{r.Index}", dup)
    for cc in ("TH", "PH", "SG"):
        T = pd.read_csv(W / f"G3/{cc}_OTHER_SHARE_STEPS.csv"); T = T[T.scenario.astype(str).str.startswith("sensitivity")]
        for r in T.itertuples():
            add(f"{cc}：{r.step.replace('sens: ', '')}", f"G3 {cc}_OTHER_SHARE_STEPS.csv", cc, float(r.delta_T_TWh), float(r.delta_TWh), f"g3_{cc}_{r.Index}",
                "eth_u075/u095/hvc_s2" if ("乙烯" in r.step or "HVC" in r.step) else ("pp_cap/pp_literal" if "纸浆" in r.step else ("sg_refgas" if "炼厂气" in r.step else
                                                                                                                                    ("res_bagasse_kept" if "蔗渣" in r.step else None))))
    V = pd.read_csv(W / "G2/tables/VN_SENSITIVITIES.csv")
    for r in V.itertuples():
        if str(r.sensitivity).startswith("main"):
            continue
        dup = "vnfw_export" if "fuelwood low" in r.sensitivity else ("res_bagasse_kept" if "bagasse" in r.sensitivity else ("no_new_plants" if "ethylene" in r.sensitivity else
                                                                                                                            ("pp_literal" if "pulp" in r.sensitivity else ("reading_I" if "diesel" in r.sensitivity else None))))
        add(f"VN：{r.sensitivity}", "G2 VN_SENSITIVITIES.csv", "VN", float(r.delta_T_vs_main_TWh), float(r.delta_other_vs_main_TWh), f"g2_{r.Index}", dup)
    M = pd.read_csv(W / "G1/tables/MY_CHAIN_SCENARIOS.csv"); comb = M[(M.sequence == "207") & (M.step == 10)].iloc[0]
    for r in M[M.sequence == "sensitivity"].itertuples():
        dup = "my_sabah_neu" if "Sabah" in r.scenario else ("no_new_plants" if "R4" in r.scenario else ("hvc_s2" if "HVC" in r.scenario else None))
        add(f"MY：{r.scenario.replace('sens ', '')}", "G1 MY_CHAIN_SCENARIOS.csv", "MY", float(r.T_2050_twh - comb.T_2050_twh), float(r.other_2050_twh - comb.other_2050_twh), f"g1_{r.Index}", dup)
    G4 = pd.read_csv(W / "G4/evidence/G4_SCENARIOS.csv"); main = G4[(G4.scenario == "4 products (closed loop)") & (G4.ncv_scheme == "207")].set_index("country")
    for r in G4[G4.scenario.astype(str).str.startswith("S ")].itertuples():
        if r.country not in main.index:
            continue
        dT = float(r.T_v2_2050_TWh - main.at[r.country, "T_v2_2050_TWh"]); dO = float(r.other_2050_TWh - main.at[r.country, "other_2050_TWh"])
        if abs(dT) < 1e-6 and abs(dO) < 1e-6:
            continue
        add(f"{r.country}：{r.scenario[2:]}", "G4 G4_SCENARIOS.csv", r.country, dT, dO, f"g4_{r.Index}", "res_nes_purchased" if "5150" in r.scenario else None)
    A = pd.DataFrame(rows)
    A["duplicate_of"] = A.get("duplicate_of", "").fillna("")
    A = A.sort_values("magnitude_TWh", ascending=False)
    # excluded from the ranking: f4_off / pot_v3 / no_f7 (the decided rule of decision 209 switched off), duplicates of an I2 re-run, and session rows
    # that compare a superseded rule rather than an alternative reading (v2 decomposition, S2 spread rule, 'comparison', a plain step)
    superseded = A.sensitivity.str.contains("v2 decomposition|comparison|main without|对照", regex=True)
    A["excluded_from_ranking"] = A.key.isin(["no_f7", "pot_v3", "f4_off"]) | superseded | (A.duplicate_of != "")
    A.to_csv(cm.TABLES / "I2_SENSITIVITY_ALL.csv", index=False, float_format="%.4f", lineterminator="\n")
    cand = A[~A.excluded_from_ranking]
    top = cand.head(10).copy(); top.insert(0, "rank", range(1, len(top) + 1))
    top.to_csv(cm.I2 / "SENSITIVITY_TOP10.csv", index=False, float_format="%.4f", lineterminator="\n")
    for r in top.itertuples():
        ev.add(f"top{r.rank}", dict(sensitivity=r.sensitivity, dT_v2=r.dT_v2_TWh, dOther=r.dOther_TWh, dPotential=r.dPotential_TWh, magnitude=r.magnitude_TWh),
               "TWh (2050)", "PROPOSED" if r.re_run_in_I2 else "INFERENCE", r.grade, r.source)
    ev.write()
    pd.set_option("display.width", 230); pd.set_option("display.max_colwidth", 60)
    print(top[["rank", "sensitivity", "source", "dT_v2_TWh", "dOther_TWh", "dPotential_TWh", "largest_country", "magnitude_TWh"]].round(2).to_string())


if __name__ == "__main__":
    main()
