"""V4 D2b section 7: post-processing of the D2b rerank refresh (rerank_with_results_d2b.py on the v31 (F1, F2) reference, v31ev05 (F3, F4) control, this branch's
registry ranges and the D2b inventory overrides), compared with the D2a rerank. No solver.

    python rerank_d2b_post.py --rerank <D2b rerank dir> --d2a <D2a rerank dir> --inventory <C_GRADE_INVENTORY_D2B.csv> --out <delivery folder>

Writes RERANK_D2B_TOP30.csv, RERANK_D2B_OWEN_TOP10.csv, RERANK_D2B_VS_D2A.csv (rank / dB6 / notch differences to the D2a rerank, with the reason),
W19_CANDIDATES_D2B.csv (top 15 by |dB6| and top 10 by |Owen| + the D2a / D2b-identified items; column changed_by_d2b marks the rows whose notch, value basis or
rank changed through this step), evidence/RERANK_D2B_SUMMARY.json.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

NUM = ["abs_dB6", "dB6", "dZ_F1", "dZ_F2", "rank", "rank_v31ev05", "dB6_v31ev05", "owen_max_eur", "notch_low", "notch_high"]
D2B_CANDIDATES = [
    dict(param_id="biomass_potential_cassava_coconut_other_crop_energy_basis", family_201="biomass", country="ASEAN (ID / TH / PH / VN / MM / KH)", status="DATA_PENDING (T05 UNDETERMINED)",
         mechanism="store_pot", bias_class="rhs", changed_by_d2b="new (D2b 2.2)",
         flags="Smeets h = 1/HI - 1 (dry-weight framework) applied by IRENA 2017a to FRESH FAOSTAT production: cassava 1.0, coconut harvest 3.0 (palm-kernel group factor), fruit 2.03 / vegetables 0.41 not reproduced on any basis; 518 TWh kept, low ends cassava 31 / coconut 63 / other crops 40 TWh",
         needs_new_data="yes: Smeets 2004 harvest-index table; ASEAN measured RPR with moisture for cassava, coconut fronds, banana / fruit / vegetable residues",
         why_C="not computed (first order on v31: the registry low ends of the 37 country rows now reach the basis low)", source="D2b BIOMASS_BASIS_AUDIT.csv; RESIDUE_LITERATURE.json"),
    dict(param_id="biomass_potential_oil_palm_trunk_mass_factor", family_201="biomass", country="ID/MY/TH/PH/KH", status="REGISTERED (T05 main, factor 0.3135)", mechanism="store_pot", bias_class="rhs",
         changed_by_d2b="value changed (D2b 2.1: fresh mass x 15 GJ/t -> dry matter x LHV_dry)",
         flags="trunk pools 231.26 -> 72.50 TWh; residual question: the IRENA 2 t per palm is the whole above-ground fresh palm (Khalid 1999: trunk 1.51 t, dry 0.30 t) - the low end 0.147 uses the measured trunk dry mass",
         needs_new_data="partly: trunk-only fresh / dry mass per palm at replanting (Kosugi 2010, Yamada 2010, Khalid 2000 full texts); actual replanting rate (MY 2.2 %/a vs 4 %)",
         why_C="D2b smoke dV (SMOKE56_D2B.md)", source="D2b TRUNK_LITERATURE.json; tables/TRUNK_CHAIN_CHECK.csv"),
    dict(param_id="lng_regas_adder_vs_expansion_capex_overlap", family_201="other", country="ASEAN", status="PROPOSED", mechanism="gen_mc / gen_cc", bias_class="cost", changed_by_d2b="new (D2b 4.1)",
         flags="the published regulated tariffs (2.05 EUR2020/MWh, v4 main) are full-cost; on NEW terminal capacity the capital part (~0.9 EUR/MWh at full use) overlaps the expansion capex 8,020 EUR2020/MW/a; split capacity / commodity charge (TH Lc ~0.05-0.08 EUR/MWh)",
         needs_new_data="no (model structure choice)", why_C="first-order upper bound of the adder change: D2b smoke cost class +0.49 / +0.72 bn (56 h)", source="D2b DATA_UPGRADES.csv"),
    dict(param_id="ev_ice_fleet_weights_asean", family_201="route_share", country="ASEAN", status="SENSITIVITY", mechanism="ev_load_scale", bias_class="rhs", changed_by_d2b="range changed (D2b 4.4)",
         flags="fleet ratio mid 3.37 (+1.7 % of 3.31, kept); range 2.11-4.78 because the class weights contradict (TH two-wheeler share of road fuel 10 % IEA vs 27 % ADBI) and trucks have no comparable pair",
         needs_new_data="yes: road fuel by vehicle class per country", why_C="share_transport_electric_efficiency notch refreshed to 33.9-76.9", source="D2b DATA_UPG_B.json E01-E28"),
]
D2A_KEPT = ["bunker_emissions_in_bunkering_country_net_zero", "biomass_potential_oil_palm_efb_energy_basis", "phs_candidates_asean_case"]


def main():
    ap = argparse.ArgumentParser()
    for k in ("rerank", "d2a", "inventory", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    R, A, OUT = Path(a.rerank), Path(a.d2a), Path(a.out)

    def load(p):
        x = pd.read_csv(p / "IMPACT_FIRST_ORDER.csv", keep_default_na=False, low_memory=False)
        for c in NUM:
            if c in x:
                x[c] = pd.to_numeric(x[c], errors="coerce")
        x["ranked"] = x["ranked"].astype(str).isin(("True", "true", "1"))
        return x
    wide, d2a = load(R), load(A)
    summ = json.loads((R / "RERANK_SUMMARY.json").read_text())
    inv = pd.read_csv(a.inventory, dtype=str, keep_default_na=False).set_index("param_id")
    rk = wide[wide.ranked].copy().sort_values("rank")
    cols = ["rank", "param_id", "family_201", "country", "status", "mechanism", "bias_class", "bias_dZ", "direction_max", "dB6", "dZ_F1", "dZ_F2", "owen_max_country", "owen_max_eur",
            "rank_v31ev05", "dB6_v31ev05", "notch_low", "notch_high", "flags"]
    top = rk.head(30)
    top[[c for c in cols if c in top]].to_csv(OUT / "RERANK_D2B_TOP30.csv", index=False, lineterminator="\n")
    ow = rk.assign(abs_owen=rk.owen_max_eur.abs()).sort_values("abs_owen", ascending=False).head(10)
    ow[[c for c in cols if c in ow] + ["owen_by_country"]].to_csv(OUT / "RERANK_D2B_OWEN_TOP10.csv", index=False, lineterminator="\n")
    # ---- difference to the D2a rerank
    m = wide.set_index("param_id")[["rank", "dB6", "dZ_F1", "owen_max_eur", "ranked", "notch_low", "notch_high", "bias_class"]].join(
        d2a.set_index("param_id")[["rank", "dB6", "dZ_F1", "owen_max_eur", "ranked", "notch_low", "notch_high"]], lsuffix="_d2b", rsuffix="_d2a", how="outer")
    upd = set(pd.read_csv(R / "INVENTORY_RANGE_UPDATES.csv").param_id) if (R / "INVENTORY_RANGE_UPDATES.csv").exists() and (R / "INVENTORY_RANGE_UPDATES.csv").stat().st_size > 5 else set()
    upd_d2a = set(pd.read_csv(A / "INVENTORY_RANGE_UPDATES.csv").param_id) if (A / "INVENTORY_RANGE_UPDATES.csv").exists() and (A / "INVENTORY_RANGE_UPDATES.csv").stat().st_size > 5 else set()
    ovr = set(pd.read_csv(R / "INVENTORY_OVERRIDES_D2B.csv").param_id) if (R / "INVENTORY_OVERRIDES_D2B.csv").exists() else set()

    def notch_changed(r):
        f = lambda x, y: (pd.isna(x) and pd.isna(y)) or (pd.notna(x) and pd.notna(y) and abs(x - y) <= 1e-9 * max(1.0, abs(y)))   # noqa: E731
        return not (f(r.notch_low_d2b, r.notch_low_d2a) and f(r.notch_high_d2b, r.notch_high_d2a))

    def reason(pid, r):
        why = []
        if pid in ovr:
            why.append("D2b inventory override (4.3 / 4.6)")
        if notch_changed(r):
            why.append("notch refreshed from the D2b registry range" if pid in upd else "notch changed")
        if bool(r.ranked_d2a) != bool(r.ranked_d2b):
            why.append("entered the ranking" if bool(r.ranked_d2b) else "left the ranking")
        if (not why) and pd.notna(r.rank_d2b) and pd.notna(r.rank_d2a) and r.rank_d2b != r.rank_d2a:
            why.append("rank shift from rows above moving (same dB6)" if abs((r.dB6_d2b or 0) - (r.dB6_d2a or 0)) <= 1e-6 else "dB6 changed")
        return "; ".join(why)
    m["reason"] = [reason(pid, r) for pid, r in m.iterrows()]
    m["rank_change"] = m.rank_d2b - m.rank_d2a
    m["dB6_change"] = m.dB6_d2b - m.dB6_d2a
    m["changed_by_d2b"] = [("notch / basis: " + r.reason) if (pid in ovr or notch_changed(r)) else (r.reason if r.reason else "") for pid, r in m.iterrows()]
    diff = m[(m.reason != "") | (m.rank_change.fillna(0) != 0) | (m.dB6_change.fillna(0).abs() > 1e-6)].sort_values("rank_d2b")
    diff.index.name = "param_id"
    diff.reset_index().to_csv(OUT / "RERANK_D2B_VS_D2A.csv", index=False, lineterminator="\n")
    # ---- W19 candidates
    pick = pd.concat([rk.head(15).assign(selected_by="|dB6| top 15"), ow.assign(selected_by="|Owen| top 10")]).drop_duplicates("param_id", keep="first")
    rows = []
    for r in pick.itertuples():
        i = inv.loc[r.param_id] if r.param_id in inv.index else None
        rows.append(dict(param_id=r.param_id, family_201=r.family_201, country=r.country, status=r.status, mechanism=r.mechanism, bias_class=r.bias_class, selected_by=r.selected_by,
                         rank_d2b=r.rank, rank_d2a=m.at[r.param_id, "rank_d2a"], dB6_eur=r.dB6, dB6_d2a_eur=m.at[r.param_id, "dB6_d2a"], dZ_F1_eur=r.dZ_F1,
                         owen_max_country=r.owen_max_country, owen_max_eur=r.owen_max_eur, direction_max=r.direction_max, notch_low=r.notch_low, notch_high=r.notch_high,
                         changed_by_d2b=m.at[r.param_id, "changed_by_d2b"], flags=r.flags,
                         needs_new_data=("yes (DATA_PENDING)" if r.status == "DATA_PENDING" else ("no (registered range / rule switch)" if "discrete" in str(r.flags) else "range registered; better source = data item")),
                         why_C=(i.why_C if i is not None else ""), source="W10 inventory / D2b rerank refresh (first order on v31 F1 / F2; D2b registry ranges)"))
    d2a_c = pd.read_csv(OUT.parent / "p1_v4_d2a_20261107" / "W19_CANDIDATES.csv", keep_default_na=False) if (OUT.parent / "p1_v4_d2a_20261107" / "W19_CANDIDATES.csv").exists() else pd.DataFrame()
    for pid in D2A_KEPT:
        z = d2a_c[d2a_c.param_id == pid]
        if len(z):
            x = z.iloc[0]
            rows.append(dict(param_id=pid, family_201=x.family_201, country=x.country, status=x.status, mechanism=x.mechanism, bias_class=x.bias_class, selected_by="D2a-identified (kept)",
                             changed_by_d2b="", flags=x.flags, needs_new_data=x.needs_new_data, why_C=x.why_C, source=x.source))
    for d in D2B_CANDIDATES:
        rows.append(dict(param_id=d["param_id"], family_201=d["family_201"], country=d["country"], status=d["status"], mechanism=d["mechanism"], bias_class=d["bias_class"], selected_by="D2b-identified",
                         changed_by_d2b=d["changed_by_d2b"], flags=d["flags"], needs_new_data=d["needs_new_data"], why_C=d["why_C"], source=d["source"]))
    pd.DataFrame(rows).to_csv(OUT / "W19_CANDIDATES_D2B.csv", index=False, lineterminator="\n")
    # ---- summary
    t0 = set(rk.head(30).param_id); d2ark = d2a[d2a.ranked].set_index("param_id")["rank"]; t1 = set(d2ark[d2ark <= 30].index)
    both = rk.set_index("param_id")["rank"].to_frame("d2b").join(d2ark.to_frame("d2a"), how="inner")
    res = dict(reference="v31", control="v31ev05", ranked_rows=int(len(rk)), ranked_rows_d2a=int(d2a.ranked.sum()), range_updates_d2b=sorted(upd - upd_d2a), range_updates_all=len(upd),
               inventory_overrides=sorted(ovr), top30_overlap_with_d2a=len(t0 & t1), entered=sorted(t0 - t1), left=sorted(t1 - t0),
               spearman_vs_d2a=float(both.d2b.corr(both.d2a, method="spearman")), stability_vs_v31ev05=summ.get("stability", {}).get("v31ev05"), b6_base=summ.get("b6_base"),
               top30_abs_dB6_share=float(rk.head(30).abs_dB6.sum() / rk.abs_dB6.sum()) if rk.abs_dB6.sum() else None,
               w19_rows=len(rows), w19_changed_by_d2b=int(sum(1 for x in rows if x.get("changed_by_d2b"))))
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "RERANK_D2B_SUMMARY.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    pd.set_option("display.width", 250)
    print(json.dumps(res, ensure_ascii=False, default=str))
    print(top[["rank", "param_id", "bias_class", "dB6", "dZ_F1", "rank_v31ev05"]].head(30).to_string())
    print(diff.reset_index()[["param_id", "rank_d2a", "rank_d2b", "dB6_d2a", "dB6_d2b", "reason"]].head(50).to_string())


if __name__ == "__main__":
    main()
