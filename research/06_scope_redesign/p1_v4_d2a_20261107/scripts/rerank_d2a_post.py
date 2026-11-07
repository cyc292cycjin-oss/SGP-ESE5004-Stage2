"""V4 D2a section 4.5: post-processing of the D2a rerank run (rerank_with_results_d2a.py on the v31 (F1, F2) reference and the v31ev05 (F3, F4) control).

    python rerank_d2a_post.py --rerank <out dir> --w15 <work/p1_v31_w15_20261106> --inventory <C_GRADE_INVENTORY_D2A.csv> --out <delivery folder>

Writes RERANK_D2A_TOP30.csv, RERANK_D2A_OWEN_TOP10.csv, RERANK_D2A_VS_W15.csv (rank / dB6 differences to the W15 rerank, with the reason), W19_CANDIDATES.csv
(top rows by |dB6| and by |Owen|, mechanism, bias, data need; plus the D2a-identified candidates), evidence/RERANK_D2A_SUMMARY.json. No solver.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

NUM = ["abs_dB6", "dB6", "dZ_F1", "dZ_F2", "rank", "rank_v31ev05", "dB6_v31ev05", "owen_max_eur", "dB6_low", "dB6_high", "value", "notch_low", "notch_high"]
D2A_CANDIDATES = [
    dict(param_id="bunker_emissions_in_bunkering_country_net_zero", family_201="co2", country="SG/MY/ID", status="PROPOSED", mechanism="constraint_structure", bias_class="rhs",
         source="decision 218 (V4 D2a instruction section 0)", mechanism_note="international bunker emissions counted in the bunkering country's net-zero account instead of the ASEAN bunker account (W15 SUPP01: SG 78 % of bunkers; BUNKER Owen +0.886 bn at 3 h)",
         needs_new_data="no (model structure switch)", first_order="not available (constraint set changes); W15 bunker attribution SG 78 %"),
    dict(param_id="biomass_potential_oil_palm_trunk_energy_basis", family_201="biomass", country="ID/MY/TH/PH/KH", status="DATA_PENDING", mechanism="store_pot", bias_class="rhs",
         source="D2a T04 (EFB_BASIS.md): trunk potential = wet mass x 15 GJ/t while the trunk is 70-80 % water; dry LHV unsourced", mechanism_note="dry-matter basis would cut the trunk pools (231 TWh, all used in every solve) to 20-36 %; W15 rank 9 / Owen ID -20.85 bn for the trunk potential notch",
         needs_new_data="yes: oil palm trunk LHV (dry / as received) from >= 2 sources", first_order="W15 v31: biomass_potential_ID_oil_palm_trunk dZ_F1 -20.85 bn (high notch); the basis cut acts in the opposite direction"),
    dict(param_id="biomass_potential_oil_palm_efb_energy_basis", family_201="biomass", country="ID/MY/TH", status="REGISTERED (D2a main)", mechanism="store_pot", bias_class="rhs",
         source="D2a T04: v4 main = (1 - 0.60) x 18.0 GJ/t dry; range factor 0.348-0.545 of the W08 value", mechanism_note="EFB pools ID 216.6 -> 104.0, MY 88.1 -> 42.3, TH 15.9 -> 7.7 TWh; low / high of the moisture and LHV sources",
         needs_new_data="partly: mill-gate moisture of EFB by country (ID / MY / TH)", first_order="D2a smoke alarm line (SMOKE56_D2A.md section 1)"),
    dict(param_id="phs_candidates_asean_case", family_201="other", country="ID/LA/MY/MM/VN/PH/TH", status="SENSITIVITY", mechanism="su_pnom_max / store_cc", bias_class="cost+rhs",
         source="D2a section 3.4: research.supply.phs_case = asean (Lu et al. 2021 costs, ANU short-list energy caps, 6 / 12 / 24 h tiers)", mechanism_note="6 h tier annuity ~ 1/3 of technology-data; long-duration PHS may replace part of the 484 GW battery discharge of the 3 h solution (W15)",
         needs_new_data="ANU per-country site list (download candidate)", first_order="W15: potential_PHS_per_country_ALL_DATA_PENDING no binding candidate -> needs a solve"),
    dict(param_id="agricultural_residue_factor_moisture_basis", family_201="biomass", country="ASEAN", status="PROPOSED", mechanism="store_pot", bias_class="rhs",
         source="D2a T04: IRENA 2017a 15 GJ/t with Smeets et al. (2004) residue factors, moisture basis not stated", mechanism_note="rice / maize / sugarcane / cassava / coconut / other residues (~1,000 TWh); field-dried residues 10-20 % moisture, as-received LHV 13-16 GJ/t (INFERENCE)",
         needs_new_data="yes: residue factor basis (Smeets 2004) and as-received LHV of the field residues", first_order="not computed (range factor 0.87-1.07, INFERENCE)"),
]


def main():
    ap = argparse.ArgumentParser()
    for k in ("rerank", "w15", "inventory", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    R, W15, OUT = Path(a.rerank), Path(a.w15), Path(a.out)
    wide = pd.read_csv(R / "IMPACT_FIRST_ORDER.csv", keep_default_na=False, low_memory=False)
    for c in NUM:
        if c in wide:
            wide[c] = pd.to_numeric(wide[c], errors="coerce")
    wide["ranked"] = wide["ranked"].astype(str).isin(("True", "true", "1"))
    summ = json.loads((R / "RERANK_SUMMARY.json").read_text())
    inv = pd.read_csv(a.inventory, dtype=str, keep_default_na=False).set_index("param_id")
    rk = wide[wide.ranked].copy().sort_values("rank")
    cols = ["rank", "param_id", "family_201", "country", "status", "mechanism", "bias_class", "bias_dZ", "direction_max", "dB6", "dZ_F1", "dZ_F2", "owen_max_country", "owen_max_eur",
            "rank_v31ev05", "dB6_v31ev05", "notch_low", "notch_high", "flags"]
    top = rk.head(30)
    top[[c for c in cols if c in top]].to_csv(OUT / "RERANK_D2A_TOP30.csv", index=False, lineterminator="\n")
    ow = rk.assign(abs_owen=rk.owen_max_eur.abs()).sort_values("abs_owen", ascending=False).head(10)
    ow[[c for c in cols if c in ow] + ["owen_by_country"]].to_csv(OUT / "RERANK_D2A_OWEN_TOP10.csv", index=False, lineterminator="\n")
    # ---- difference to W15 (same reference v31; W15 = W10 method on the v31 results)
    w15 = pd.read_csv(W15 / "rerank" / "IMPACT_FIRST_ORDER.csv", keep_default_na=False, low_memory=False)
    for c in ("rank", "dB6", "dZ_F1", "owen_max_eur"):
        w15[c] = pd.to_numeric(w15[c], errors="coerce")
    w15["ranked"] = w15["ranked"].astype(str).isin(("True", "true", "1"))
    m = wide.set_index("param_id")[["rank", "dB6", "dZ_F1", "owen_max_eur", "ranked", "flags", "bias_class", "notch_low", "notch_high"]].join(
        w15.set_index("param_id")[["rank", "dB6", "dZ_F1", "owen_max_eur", "ranked", "flags", "notch_low", "notch_high"]], lsuffix="_d2a", rsuffix="_w15", how="outer")
    inact = set(pd.read_csv(R / "INACTIVE_BASIS_ROWS.csv").param_id) if (R / "INACTIVE_BASIS_ROWS.csv").exists() else set()
    upd = set(pd.read_csv(R / "INVENTORY_RANGE_UPDATES.csv").param_id) if (R / "INVENTORY_RANGE_UPDATES.csv").exists() and (R / "INVENTORY_RANGE_UPDATES.csv").stat().st_size > 5 else set()

    def reason(pid, r):
        why = []
        if pid in inact:
            why.append("4.2 S-B shipping row left the ranking (basis not active)")
        if pid in upd:
            why.append("4.4 notch refreshed from the physics-corrected registry range")
        if isinstance(r.flags_d2a, str) and "duplicate_bound" in r.flags_d2a:
            why.append("4.1 CO2 storage cap dual read from the Store e_nom bound")
        if bool(r.ranked_w15) and not bool(r.ranked_d2a) and pid not in inact:
            why.append("left the ranking")
        if (not why) and pd.notna(r.rank_d2a) and pd.notna(r.rank_w15) and r.rank_d2a != r.rank_w15:
            why.append("rank shift from rows above moving (same dB6)" if abs((r.dB6_d2a or 0) - (r.dB6_w15 or 0)) <= 1e-6 else "dB6 changed")
        return "; ".join(why)
    m["reason"] = [reason(pid, r) for pid, r in m.iterrows()]
    m["rank_change"] = m.rank_d2a - m.rank_w15
    m["dB6_change"] = m.dB6_d2a - m.dB6_w15
    diff = m[(m.reason != "") | (m.rank_change.fillna(0) != 0) | (m.dB6_change.fillna(0).abs() > 1e-6)].sort_values("rank_d2a")
    diff.index.name = "param_id"
    diff.reset_index().to_csv(OUT / "RERANK_D2A_VS_W15.csv", index=False, lineterminator="\n")
    # ---- W19 candidates: top 15 by |dB6| and top 10 by |Owen| of the ranked rows + the D2a-identified items
    pick = pd.concat([rk.head(15).assign(selected_by="|dB6| top 15"), ow.assign(selected_by="|Owen| top 10")]).drop_duplicates("param_id", keep="first")
    rows = []
    for r in pick.itertuples():
        i = inv.loc[r.param_id] if r.param_id in inv.index else None
        rows.append(dict(param_id=r.param_id, family_201=r.family_201, country=r.country, status=r.status, mechanism=r.mechanism, bias_class=r.bias_class, selected_by=r.selected_by,
                         rank_d2a=r.rank, dB6_eur=r.dB6, dZ_F1_eur=r.dZ_F1, owen_max_country=r.owen_max_country, owen_max_eur=r.owen_max_eur, direction_max=r.direction_max,
                         notch_low=r.notch_low, notch_high=r.notch_high, flags=r.flags,
                         needs_new_data=("yes (DATA_PENDING)" if r.status == "DATA_PENDING" else ("no (registered range / rule switch)" if "scenario_choice" in str(r.flags) or "discrete" in str(r.flags) else "range registered; better source = data item")),
                         why_C=(i.why_C if i is not None else ""), source="W10 inventory / D2a rerank (first order on v31 F1 / F2)"))
    for d in D2A_CANDIDATES:
        rows.append(dict(param_id=d["param_id"], family_201=d["family_201"], country=d["country"], status=d["status"], mechanism=d["mechanism"], bias_class=d["bias_class"], selected_by="D2a-identified",
                         rank_d2a=None, dB6_eur=None, dZ_F1_eur=None, owen_max_country="", owen_max_eur=None, direction_max="", notch_low=None, notch_high=None, flags=d["mechanism_note"],
                         needs_new_data=d["needs_new_data"], why_C=d["first_order"], source=d["source"]))
    pd.DataFrame(rows).to_csv(OUT / "W19_CANDIDATES.csv", index=False, lineterminator="\n")
    # ---- summary
    t0 = set(rk.head(30).param_id); w15rk = w15[w15.ranked].set_index("param_id")["rank"]; t1 = set(w15rk[w15rk <= 30].index)
    both = rk.set_index("param_id")["rank"].to_frame("d2a").join(w15rk.to_frame("w15"), how="inner")
    res = dict(reference="v31", control="v31ev05", ranked_rows=int(len(rk)), ranked_rows_w15=int(w15.ranked.sum()), inactive_basis_rows=sorted(inact), range_updates=sorted(upd),
               top30_overlap_with_w15=len(t0 & t1), entered=sorted(t0 - t1), left=sorted(t1 - t0), spearman_vs_w15=float(both.d2a.corr(both.w15, method="spearman")),
               stability_vs_v31ev05=summ.get("stability", {}).get("v31ev05"), b6_base=summ.get("b6_base"), duplicate_bounds=int(summ.get("d2a", {}).get("duplicate_bound_rows", 0)),
               bias_classes=rk.bias_class.value_counts().to_dict(), top30_abs_dB6_share=float(rk.head(30).abs_dB6.sum() / rk.abs_dB6.sum()) if rk.abs_dB6.sum() else None)
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "RERANK_D2A_SUMMARY.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    pd.set_option("display.width", 250)
    print(json.dumps({k: res[k] for k in ("ranked_rows", "inactive_basis_rows", "range_updates", "top30_overlap_with_w15", "entered", "left", "spearman_vs_w15", "duplicate_bounds", "bias_classes")}, ensure_ascii=False, default=str))
    print(top[["rank", "param_id", "bias_class", "dB6", "dZ_F1", "rank_v31ev05"]].head(30).to_string())
    print(diff.reset_index().rename(columns={"index": "param_id"})[["param_id", "rank_w15", "rank_d2a", "dB6_w15", "dB6_d2a", "reason"]].head(40).to_string())


if __name__ == "__main__":
    main()
