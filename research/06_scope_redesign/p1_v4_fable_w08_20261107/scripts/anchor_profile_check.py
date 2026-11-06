"""Fable W08 review, dimensions 5 and 6: anchor construction (RAS / IId / residue deduction) from the committed tables, and the G5 curve files.

usage: anchor_profile_check.py <repo> <OUT.json>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO, OUT = Path(sys.argv[1]), Path(sys.argv[2])
V4 = REPO / "research_inputs/industry_v4"
SEC = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
res = {}
rr = pd.read_csv(V4 / "RESIDUE_RECORDS_2019.csv", dtype={"tx": str, "code": str})
R = rr[rr.cls == "a"].groupby("country").mwh.sum().to_dict()
cov = pd.read_csv(V4 / "NATIONAL_BALANCE_BIOMASS_COVERAGE.csv").set_index("country")
adjc = {c: R[c] for c in R if str(cov.at[c, "balance_contains_self_produced_residues"]) == "as_unsd"}
res["residue_adjustment_mwh"] = adjc
sig = pd.read_csv(REPO / "research_inputs/demand_v5/DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv").set_index("sector").factor.to_dict()
dump = json.loads((V4 / "ANCHORS_V31_RAS_DUMP.json").read_text())
# v3 RAS rank-one check: tfa_cs / t19_cs = r_c x sigma_s -> ratios across countries proportional
rat = {c: {s: dump["tfa"][c][s] / dump["t19"][c][s] if dump["t19"][c][s] else None for s in SEC} for c in dump["tfa"] if c != "TL"}
rk = []
for c, d in rat.items():
    if d["Industry"]:
        rk.append(dict(country=c, **{s: (d[s] / d["Industry"]) / (sig[s] / sig["Industry"]) if d[s] else None for s in SEC}))
res["v31_ras_rank_one_ratio_check"] = rk
for mode in ("ras", "iid"):
    od = V4 / f"out_{mode}"
    an = pd.read_csv(od / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    cols = [c for c in an.columns if c.startswith("ras_sector_anchor_")]
    dv = pd.read_csv(od / "DEMAND_ANCHOR_C3_DEVIATION.csv").set_index("sector")
    rows = []
    for c in an.index:
        tfa = {s: float(an.at[c, f"ras_sector_anchor_{s}_mwh"]) for s in SEC}
        rs = sum(tfa.values()); A = float(an.at[c, "ats_tfec_2050_mwh"]); m = float(an.at[c, "industry_multiplier"])
        r = adjc.get(c, 0.0)
        rows.append(dict(country=c, row_sum_mwh=rs, ats_tfec_mwh=A, row_minus_A_mwh=rs - A, expected_minus_R_x_m_mwh=-r * m, residual_mwh=(rs - A) + r * m,
                         industry_anchor_mwh=float(an.at[c, "industry_anchor_mwh"]), industry_multiplier=m, industry_2019_seed_implied_mwh=float(an.at[c, "industry_anchor_mwh"]) / m if m else None))
    res[f"out_{mode}_rows"] = rows
    col = {s: float(sum(float(an.at[c, f"ras_sector_anchor_{s}_mwh"]) for c in an.index if c != "TL")) for s in SEC}
    res[f"out_{mode}_columns"] = {s: dict(asean10_sum=col[s], c3_x_k=float(dv.at[s, "c3_x_k_mwh"]), deviation_mwh=col[s] - float(dv.at[s, "c3_x_k_mwh"]), file_deviation=float(dv.at[s, "deviation_mwh"])) for s in SEC}
    res[f"out_{mode}_anchor_columns"] = cols[:12]
    # IId: tfa_cs proportional to seed_s x sigma_s -> tfa_cs / sigma_s should be proportional to the seed; the ATS 2019 base by sector (post moves) is only a proxy
    if mode == "iid":
        ats = pd.read_csv(od / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False, dtype=str)
        ats["b"] = pd.to_numeric(ats.base_2019_mwh, errors="coerce").fillna(0.0)
        chk = []
        for c in an.index:
            if c == "TL":
                continue
            seed = {s: float(ats[(ats.country == c) & (ats.sector == s)].b.sum()) for s in SEC}
            tfa = {s: float(an.at[c, f"ras_sector_anchor_{s}_mwh"]) for s in SEC}
            ratios = {s: tfa[s] / (seed[s] * sig[s]) if seed[s] else None for s in SEC}
            chk.append(dict(country=c, **{f"r_{s}": ratios[s] for s in SEC}, note="industry ratio differs where the ATS industry base was edited after the anchor (moves, (b) add, residue removal)"))
        res["iid_proportionality_proxy"] = chk
# ---- G5 curves
P = pd.read_parquet(V4 / "INDUSTRY_PROFILES_8760.parquet"); I = pd.read_csv(V4 / "INDUSTRY_PROFILE_INDEX.csv")
res["profiles"] = dict(curves=int(P.shape[1]), hours=int(P.shape[0]), index_rows=len(I), variants=sorted(set(I.variant)), etypes=sorted(set(I.etype)),
                       zones=sorted(set(I.zone))[:40], keys=sorted(set(I.subsector)),
                       mean_abs_dev_from_one_max=float((P.mean() - 1.0).abs().max()), min_value=float(P.min().min()), neg_curves=int((P.min() < 0).sum()),
                       flat_curves=int(((P.max() - P.min()) < 1e-12).sum()))
main = I[I.variant == "MAIN"]
res["main_index_counts"] = main.groupby(["etype"]).size().to_dict()
# zone shift consistency: MAIN elec curve of key k at UTC+7 vs UTC+8 -> one-hour roll
sh = []
for k in sorted(set(main.subsector)):
    for et in sorted(set(main.etype)):
        q = main[(main.subsector == k) & (main.etype == et)]
        z7 = q[q.zone.str.contains("UTC\\+7$")]; z8 = q[q.zone.str.contains("UTC\\+8$")]
        if len(z7) and len(z8):
            a = P[z7.curve_id.iloc[0]].to_numpy(); b = P[z8.curve_id.iloc[0]].to_numpy()
            best = min(range(-3, 4), key=lambda s: float(np.abs(np.roll(a, s) - b).max()))
            sh.append(dict(key=k, etype=et, best_roll_hours_7_to_8=best, max_abs_diff_at_best=float(np.abs(np.roll(a, best) - b).max()), flat=bool((a.max() - a.min()) < 1e-12)))
res["zone_shift_check"] = sh
W = pd.read_csv(V4 / "out_ras/INDUSTRY_CURVE_WEIGHTS_V4.csv")
res["weights_summary"] = dict(rows=len(W), countries=sorted(set(W.country)), zones_by_country={c: sorted(set(W[W.country == c].zone)) for c in sorted(set(W.country))},
                              keys_missing_in_index=sorted(set(W.key) - set(main.subsector)), elec_mwh_twh=float(W[W.etype == "elec"].mwh.sum()) / 1e6, heat_mwh_twh=float(W[W.etype == "heat"].mwh.sum()) / 1e6)
json.dump(res, open(OUT, "w"), indent=1, default=float)
pd.set_option("display.width", 250)
for mode in ("ras", "iid"):
    print(mode, "rows:"); print(pd.DataFrame(res[f"out_{mode}_rows"]).round(1).to_string()); print(mode, "columns:", {s: round(v["deviation_mwh"] / 1e6, 4) for s, v in res[f"out_{mode}_columns"].items()})
print("rank-one check (should be 1.0):"); print(pd.DataFrame(rk).round(9).to_string())
print("IId proportionality proxy:"); print(pd.DataFrame(res["iid_proportionality_proxy"]).drop(columns="note").round(6).to_string())
print("profiles:", json.dumps({k: v for k, v in res["profiles"].items() if k != "zones"}, default=str)); print("zones:", res["profiles"]["zones"])
print(pd.DataFrame(sh).to_string()); print("weights:", json.dumps(res["weights_summary"], default=str)[:1200])
