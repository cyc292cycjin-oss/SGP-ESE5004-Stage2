"""S4B-2 (decisions 78, 79): caps of the geothermal, new hydro (reservoir / run-of-river) and new PHS candidates, node allocation, nuclear plan caps.

Caps (MW, per switch value research.candidates.hydro_geothermal_cap):
  national_potential (main, decision 78 a/b): country cap = A/B-grade national potential (S4A-3 section 3.2) minus the 2050 stock after S4B-1
      hydro (reservoir + run-of-river, PHS excluded): VN 40,000 (A), ID 94,470 (B), PH 23,375 (B), MM 46,000 (B), LA 26,000 (AEO8, C),
      MY 13,600 large hydro (-> reservoir) + 2,500 small hydro (-> run-of-river) (B); geothermal ID 23,590 (B), MY 229 (B); negative -> 0 (reported).
      Without an official potential (KH / TH / TL hydro, PH geothermal, PHS of every country, other geothermal): the GEM GIPT 2026-09 project
      pipeline (B). Units under construction are already 2050 stock after S4B-1 (decision 77), so the pipeline cap counts announced +
      pre-construction (pipeline_cap_statuses = announced_preconstruction, main); announced_preconstruction_construction = the literal reading
      of the instruction (double counts the construction units; reported, user decision). PH geothermal adds the existing units that retire
      before 2050 under the S1 30-a rule (rebuilt at the same site, per node).
  national_potential_la_mem_18gw: as main with LA hydro 18,000 MW (Ministry of Energy and Mines figure, sensitivity).
  gem_pipeline_only: every country uses the pipeline caps.   zero: every cap 0 (former DATA_PENDING state, comparison).
Node allocation (decision 78 c): country caps split by the capacity shares of the GEM projects (announced + pre-construction + construction,
  i.e. every identified site) mapped to the nearest AC node of the country; countries without projects use the shares of the same-type
  stock; MY geothermal (no projects, no stock) uses the MyRER regional split (Peninsular 162 / Sabah 67 MW) spread evenly over the region's
  nodes (grade C). New hydro is split between run-of-river and reservoir by the node's project technology (conventional and run-of-river 50/50,
  unknown -> the country's stock ratio); without projects by the country's stock ratio.
Nuclear (decision 79, implemented only): national_plans caps per country on nuclear + nuclear SMR: PH 4,800, VN 14,400, ID 10,000, TH 600 MW, others 0.

    python scripts_project/s4b_2_candidates_data.py --network results_project/s4b/build_s4b1/integrated/integrated_2920_3h_unsolved.nc
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

from d1_common import ASEAN, REG_DIR, ROOT, SRC_DIR, Registry, sha256, src_sha, write_csv, write_json
from s4a_2_fleet_data import GIPT, GIPT_XLSX_SHA, ZIP_SHA, nearest_node

SCRIPT = "scripts_project/s4b_2_candidates_data.py"
OUT = ROOT / "research_inputs/potentials_v5"
POT = {   # (country, key) -> (MW, grade, registry id of S4A-3, source)
    ("VN", "hydro"): (40000.0, "A", "potential_hydro_VN_pdp8_total_potential", "Decision 500/QD-TTg (PDP VIII) art. 1 III.1.b"),
    ("ID", "hydro"): (94470.0, "B", "potential_hydro_ID_ebtke_statistics", "EBTKE potential statistics"),
    ("PH", "hydro"): (23375.0, "B", "potential_hydro_PH_doe_resource_assessments", "DOE RE briefer p.6 (Luzon 17,366 / Visayas 2,448 / Mindanao 3,569)"),
    ("MM", "hydro"): (46000.0, "B", "potential_hydro_MM_adb_identified_projects", "ADB (2016) Myanmar energy assessment p.13 para 19"),
    ("LA", "hydro"): (26000.0, "C", "potential_hydro_LA_aeo8_potential", "AEO8 p.75 citing [44]"),
    ("MY", "hydro_large"): (13600.0, "B", "potential_hydro_MY_myrer_large_hydro", "SEDA MyRER large hydro (Peninsular 3.1 / Sabah 0.5 / Sarawak 10 GW)"),
    ("MY", "hydro_small"): (2500.0, "B", "potential_hydro_MY_myrer_large_hydro", "SEDA MyRER small hydro 2.5 GW"),
    ("ID", "geothermal"): (23590.0, "B", "potential_geothermal_ID_resource_potential", "Badan Geologi / PSDMBP 2024-08-26"),
    ("MY", "geothermal"): (229.0, "B", "potential_geothermal_MY_myrer", "SEDA MyRER (Peninsular 162 + Sabah 67 MW)"),
}
LA_MEM = 18000.0
MY_GEO_REGIONS = {"MY_Peninsular": 162.0, "MY_Sabah": 67.0}
NUCLEAR_PLANS = {"PH": 4800.0, "VN": 14400.0, "ID": 10000.0, "TH": 600.0}
NUCLEAR_SRC = {"PH": "PEP 2023-2050 Vol I p.19-20 (4,800 MW by 2050), grade B", "VN": "Decision 768/QD-TTg (2025): 4,000-6,400 MW to 2035 + ~8,000 MW to 2050 -> 14,400, grade A",
               "ID": "RUPTL / news ~10 GW by 2040, grade C", "TH": "draft PDP 600 MW SMR (2037), grade C"}
MODES = ["national_potential", "national_potential_la_mem_18gw", "gem_pipeline_only", "zero"]
VARIANTS = {"announced_preconstruction": ["announced", "pre-construction"], "announced_preconstruction_construction": ["announced", "pre-construction", "construction"]}


def hydro_kind(tech):
    t = str(tech).lower()
    if "pumped" in t:
        return "PHS"
    if t == "run-of-river":
        return "ror"
    if t == "conventional storage":
        return "hydro"
    if "conventional and run-of-river" in t:
        return "mixed"
    return "unknown"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    n = pypsa.Network(str(a.network)); nodes = n.buses[n.buses.carrier == "AC"][["x", "y", "country"]]
    gem = pd.read_csv(SRC_DIR / GIPT, low_memory=False); gem_sha = src_sha(GIPT); src = f"zip:{ZIP_SHA}|gipt:{GIPT_XLSX_SHA}|extraction:{gem_sha}"
    # ---- 2050 stock after S4B-1, by node and class --------------------------------------------------------------------------
    ids = n.meta["existing_unit_components"]
    st = pd.DataFrame([dict(node=v["node"], country=str(n.buses.country.get(v["node"], "")), cls=str(n.df(v["component_type"]).at[v["component"], "carrier"]), mw=float(v["capacity_mw"])) for v in ids.values()])
    stk = st.groupby(["country", "cls"]).mw.sum()
    def stock(c, cls):
        return float(stk.get((c, cls), 0.0))
    # ---- GEM pipeline units -----------------------------------------------------------------------------------------------
    pipe = gem[gem.Status.isin(["announced", "pre-construction", "construction"]) & gem.Type.isin(["hydropower", "geothermal"])].copy()
    pipe["kind"] = np.where(pipe.Type == "geothermal", "geothermal", pipe.Technology.map(hydro_kind))
    m = pipe.apply(lambda r: nearest_node(nodes, r.iso, r.Latitude, r.Longitude), axis=1, result_type="expand"); pipe["node"] = m[0]; pipe["node_distance_km"] = m[1]
    pipe = pipe[pipe.node.notna()]
    out_pipe = pipe[["GEM unit/phase ID", "Plant / Project name", "Unit / Phase name", "iso", "Type", "Technology", "kind", "Status", "Capacity (MW)", "Latitude", "Longitude", "node", "node_distance_km"]]
    write_csv(out_pipe.rename(columns={"GEM unit/phase ID": "gem_unit_id", "Plant / Project name": "plant", "Unit / Phase name": "unit", "iso": "country", "Capacity (MW)": "capacity_mw"}).to_dict("records"),
              OUT / "GEM_PIPELINE_2026-09_HYDRO_GEO_UNITS_NODES.csv", ["gem_unit_id", "plant", "unit", "country", "Type", "Technology", "kind", "Status", "capacity_mw", "Latitude", "Longitude", "node", "node_distance_km"])
    # PH geothermal retiring before 2050 (S1 30 a): rebuilt at the same site
    phg = gem[(gem.iso == "PH") & (gem.Type == "geothermal") & (gem.Status == "operating") & gem["Start year"].notna()].copy()
    phg = phg[phg["Start year"] + 30 <= 2050]
    m = phg.apply(lambda r: nearest_node(nodes, r.iso, r.Latitude, r.Longitude), axis=1, result_type="expand"); phg["node"] = m[0]
    rebuild = phg.groupby("node")["Capacity (MW)"].sum()
    # ---- country caps per mode / variant ---------------------------------------------------------------------------------
    def pipeline(c, kinds, variant):
        d = pipe[(pipe.iso == c) & pipe.kind.isin(kinds) & pipe.Status.isin(VARIANTS[variant])]
        return float(d["Capacity (MW)"].sum())
    caps, notes = [], []
    for variant in VARIANTS:
        for mode in MODES:
            for c in sorted(ASEAN):
                hy_stock = stock(c, "hydro existing") + stock(c, "ror existing")
                rec = dict(mode=mode, variant=variant, country=c)
                if mode == "zero":
                    caps.append(dict(rec, tech="hydro_all", cap_mw=0.0, basis="zero (former DATA_PENDING state)", grade="-"))
                    caps.append(dict(rec, tech="geothermal", cap_mw=0.0, basis="zero", grade="-")); caps.append(dict(rec, tech="PHS", cap_mw=0.0, basis="zero", grade="-")); continue
                # hydro
                if mode != "gem_pipeline_only" and c == "MY":
                    lg, sm = POT[("MY", "hydro_large")][0], POT[("MY", "hydro_small")][0]
                    caps.append(dict(rec, tech="hydro_reservoir_only", cap_mw=max(0.0, lg - stock(c, "hydro existing")), basis=f"MyRER large hydro {lg:,.0f} - reservoir stock {stock(c, 'hydro existing'):,.0f}", grade="B", raw=lg - stock(c, "hydro existing")))
                    caps.append(dict(rec, tech="hydro_ror_only", cap_mw=max(0.0, sm - stock(c, "ror existing")), basis=f"MyRER small hydro {sm:,.0f} - run-of-river stock {stock(c, 'ror existing'):,.0f}", grade="B", raw=sm - stock(c, "ror existing")))
                elif mode != "gem_pipeline_only" and (c, "hydro") in POT:
                    p, g, pid, s = POT[(c, "hydro")]
                    if c == "LA" and mode == "national_potential_la_mem_18gw":
                        p, g, s = LA_MEM, "C", "Ministry of Energy and Mines 18 GW excl. Mekong mainstream (ASEAN Post 2018), sensitivity"
                    caps.append(dict(rec, tech="hydro_all", cap_mw=max(0.0, p - hy_stock), basis=f"{s}: {p:,.0f} - stock {hy_stock:,.0f}", grade=g, raw=p - hy_stock))
                elif c in ("BN", "SG"):
                    caps.append(dict(rec, tech="hydro_all", cap_mw=0.0, basis="SOURCE_ZERO (no hydro resource, S4A-3)", grade="B"))
                else:
                    caps.append(dict(rec, tech="hydro_all", cap_mw=pipeline(c, ["hydro", "ror", "mixed", "unknown"], variant), basis=f"GEM pipeline ({'+'.join(VARIANTS[variant])})", grade="B"))
                # geothermal
                if mode != "gem_pipeline_only" and (c, "geothermal") in POT:
                    p, g, pid, s = POT[(c, "geothermal")]
                    caps.append(dict(rec, tech="geothermal", cap_mw=max(0.0, p - stock(c, "geothermal existing")), basis=f"{s}: {p:,.0f} - stock {stock(c, 'geothermal existing'):,.0f}", grade=g, raw=p - stock(c, "geothermal existing")))
                else:
                    pl = pipeline(c, ["geothermal"], variant); rb = float(rebuild.sum()) if c == "PH" else 0.0
                    caps.append(dict(rec, tech="geothermal", cap_mw=pl + rb, basis=f"GEM pipeline ({'+'.join(VARIANTS[variant])}) {pl:,.0f}" + (f" + PH existing retiring before 2050 rebuilt on site {rb:,.0f}" if c == "PH" else ""), grade="B"))
                # PHS
                caps.append(dict(rec, tech="PHS", cap_mw=pipeline(c, ["PHS"], variant), basis=f"GEM pipeline pumped storage ({'+'.join(VARIANTS[variant])})", grade="B"))
    cdf = pd.DataFrame(caps); cdf["raw"] = cdf.get("raw", np.nan)
    neg = cdf[(cdf.raw < 0)].drop_duplicates(["country", "tech"])
    write_csv(cdf.to_dict("records"), OUT / "CANDIDATE_CAPS_S4B2_BY_COUNTRY.csv", list(cdf.columns))
    # ---- node allocation ---------------------------------------------------------------------------------------------------
    rows = []
    country_ror_share = {}
    for c in sorted(ASEAN):
        h, r = stock(c, "hydro existing"), stock(c, "ror existing")
        country_ror_share[c] = (r / (h + r)) if (h + r) > 0 else 0.5
    for (mode, variant, c), d in cdf.groupby(["mode", "variant", "country"]):
        cn = nodes[nodes.country == c].index.tolist()
        for _, r in d.iterrows():
            cap = float(r.cap_mw)
            if cap <= 0:
                continue
            if r.tech in ("hydro_all", "hydro_reservoir_only", "hydro_ror_only"):
                pj = pipe[(pipe.iso == c) & pipe.kind.isin(["hydro", "ror", "mixed", "unknown"])]
                if r.tech == "hydro_reservoir_only":
                    pj = pj[pj.kind.isin(["hydro", "mixed", "unknown"])]
                if r.tech == "hydro_ror_only":
                    pj = pj[pj.kind.isin(["ror", "mixed", "unknown"])]
                if len(pj):
                    by = pj.groupby("node")["Capacity (MW)"].sum(); shares = by / by.sum(); how = "GEM project capacity shares"
                    ror_frac = {}
                    for nd, dd in pj.groupby("node"):
                        tot = dd["Capacity (MW)"].sum()
                        rr = dd.loc[dd.kind == "ror", "Capacity (MW)"].sum() + 0.5 * dd.loc[dd.kind == "mixed", "Capacity (MW)"].sum() + country_ror_share[c] * dd.loc[dd.kind == "unknown", "Capacity (MW)"].sum()
                        ror_frac[nd] = rr / tot if tot > 0 else country_ror_share[c]
                else:
                    sd = st[(st.country == c) & st.cls.isin(["hydro existing", "ror existing"])].groupby("node").mw.sum()
                    if not len(sd):
                        continue
                    shares = sd / sd.sum(); how = "same-type stock shares (no GEM project)"; ror_frac = {nd: country_ror_share[c] for nd in shares.index}
                for nd, s in shares.items():
                    f = 1.0 if r.tech == "hydro_ror_only" else (0.0 if r.tech == "hydro_reservoir_only" else ror_frac.get(nd, country_ror_share[c]))
                    if f < 1:
                        rows.append(dict(mode=mode, variant=variant, country=c, node=nd, carrier="hydro", p_nom_max_mw=cap * s * (1 - f), share=s, allocation=how, split=("reservoir share of the node projects" if how.startswith("GEM") else "country stock ratio")))
                    if f > 0:
                        rows.append(dict(mode=mode, variant=variant, country=c, node=nd, carrier="ror", p_nom_max_mw=cap * s * f, share=s, allocation=how, split=("run-of-river share of the node projects" if how.startswith("GEM") else "country stock ratio")))
            elif r.tech == "geothermal":
                rb = rebuild if c == "PH" else pd.Series(dtype=float)
                base = cap - float(rb.sum())
                pj = pipe[(pipe.iso == c) & (pipe.kind == "geothermal")]
                if len(pj):
                    by = pj.groupby("node")["Capacity (MW)"].sum(); shares = by / by.sum(); how = "GEM project capacity shares"
                else:
                    sd = st[(st.country == c) & (st.cls == "geothermal existing")].groupby("node").mw.sum()
                    if len(sd):
                        shares = sd / sd.sum(); how = "same-type stock shares (no GEM project)"
                    elif c == "MY":
                        parts = {}
                        for reg_, mw in MY_GEO_REGIONS.items():
                            rn = [x for x in cn if x.startswith(reg_)]
                            for x in rn:
                                parts[x] = parts.get(x, 0.0) + mw / len(rn)
                        shares = pd.Series(parts) / sum(MY_GEO_REGIONS.values()); how = "MyRER regional split (Peninsular 162 / Sabah 67 MW), even over the region's nodes (grade C)"
                    else:
                        continue
                for nd, s in shares.items():
                    rows.append(dict(mode=mode, variant=variant, country=c, node=nd, carrier="geothermal", p_nom_max_mw=base * s, share=s, allocation=how, split=""))
                for nd, mw in rb.items():
                    rows.append(dict(mode=mode, variant=variant, country=c, node=nd, carrier="geothermal", p_nom_max_mw=float(mw), share=np.nan, allocation="PH existing geothermal retiring before 2050, rebuilt on site", split=""))
            elif r.tech == "PHS":
                pj = pipe[(pipe.iso == c) & (pipe.kind == "PHS")]
                if not len(pj):
                    continue
                by = pj.groupby("node")["Capacity (MW)"].sum(); shares = by / by.sum()
                for nd, s in shares.items():
                    rows.append(dict(mode=mode, variant=variant, country=c, node=nd, carrier="PHS", p_nom_max_mw=cap * s, share=s, allocation="GEM pumped-storage project capacity shares", split=""))
    ndf = pd.DataFrame(rows).groupby(["mode", "variant", "country", "node", "carrier"], as_index=False).agg(p_nom_max_mw=("p_nom_max_mw", "sum"), allocation=("allocation", lambda s: "; ".join(sorted(set(s)))))
    chk = ndf.groupby(["mode", "variant", "country"]).p_nom_max_mw.sum(); ccap = cdf.groupby(["mode", "variant", "country"]).cap_mw.sum()
    unalloc = (ccap - chk.reindex(ccap.index).fillna(0.0)); unalloc = unalloc[unalloc.abs() > 1e-6]
    write_csv(ndf.round(6).to_dict("records"), OUT / "CANDIDATE_CAPS_S4B2_BY_NODE.csv", list(ndf.columns))
    nuc = [dict(country=c, cap_mw=NUCLEAR_PLANS.get(c, 0.0), source=NUCLEAR_SRC.get(c, "no national plan -> 0")) for c in sorted(ASEAN)]
    write_csv(nuc, OUT / "NUCLEAR_NATIONAL_PLAN_CAPS_S4B2.csv", ["country", "cap_mw", "source"])
    # ---- registry -------------------------------------------------------------------------------------------------------
    reg = Registry(SCRIPT); main_ = cdf[(cdf["mode"] == "national_potential") & (cdf.variant == "announced_preconstruction")]
    for r in main_.itertuples():
        st_ = "SOURCE_ZERO" if (r.cap_mw <= 0 and np.isnan(r.raw)) else "REGISTERED"   # zero pipeline / no resource; a potential below the stock stays REGISTERED at 0 (reported)
        tier = r.grade if r.grade in ("A", "B", "C") else "B"
        lo = hi = None
        if tier == "C":
            if r.country == "LA" and r.tech == "hydro_all":
                lo, hi = max(0.0, LA_MEM - (stock("LA", "hydro existing") + stock("LA", "ror existing"))), r.cap_mw
            else:
                lo, hi = 0.0, r.cap_mw
        reg.add(f"candidate_cap_{r.tech}_{r.country}", f"Decision 78 main cap ({r.tech}, {r.country}): {r.basis} -> {r.cap_mw:,.1f} MW (node allocation CANDIDATE_CAPS_S4B2_BY_NODE.csv)", float(r.cap_mw), "MW", tier,
                "S4A-3 section 3.2 sources / GEM GIPT 2026-09 pipeline", "CANDIDATE_CAPS_S4B2_BY_COUNTRY.csv", src, country=r.country, sensitivity_low=lo, sensitivity_high=hi, decision_ref="78", status=st_)
    reg.add("candidate_cap_switch_s4b2", "research.candidates.hydro_geothermal_cap = national_potential (main) | national_potential_la_mem_18gw | gem_pipeline_only | zero (former state); "
            "research.candidates.pipeline_cap_statuses = announced_preconstruction (main: construction units are 2050 stock after decision 77) | announced_preconstruction_construction (literal reading, double counts)",
            "national_potential", "flag", "B", "S4B instruction S4B-2 items 1-4", "configs/research/baseline.yaml research.candidates", src, decision_ref="78")
    reg.add("candidate_new_hydro_proxies_s4b2", "New reservoir hydro: inflow per MW and max_hours = capacity-weighted same-node (else same-country, else ASEAN) existing reservoirs, inflow tied to the built capacity by a spill constraint "
            "(research_new_hydro_inflow hook), no pumping (p_min_pu 0); new run-of-river: availability = same-node (else country, else ASEAN) existing ROR; new geothermal availability 0.7194 (decision 52 AEO8 CF); "
            "new PHS 6 h, round trip 0.75 (sqrt per leg; the S1 candidate applied 0.75 on both legs)", None, "flag", "C", "S4B instruction S4B-2 item 3", "scripts_project/s4b_candidates.py", src, decision_ref="78", status="REFERENCE_ONLY")
    reg.add("nuclear_cap_switch_s4b2", "Decision 79: research.candidates.nuclear_cap = none (main, decision 38) | national_plans (per-country cap on nuclear + nuclear SMR: PH 4,800, VN 14,400, ID 10,000, TH 600 MW, others 0); implemented only, not run",
            "none", "flag", "B", "S4B instruction S4B-2 item 5; S4A-3 section 3.2", "NUCLEAR_NATIONAL_PLAN_CAPS_S4B2.csv", src, decision_ref="79", status="SENSITIVITY")
    for c, v in NUCLEAR_PLANS.items():
        reg.add(f"nuclear_plan_cap_{c}", f"Nuclear national plan cap {c} (sensitivity national_plans): {NUCLEAR_SRC[c]}", v, "MW", "B" if c in ("PH", "VN") else "C", "S4A-3 section 3.2", "NUCLEAR_NATIONAL_PLAN_CAPS_S4B2.csv", src, country=c,
                sensitivity_low=(0.0 if c not in ("PH", "VN") else None), sensitivity_high=(v if c not in ("PH", "VN") else None), decision_ref="79", status="SENSITIVITY")
    reg.write(REG_DIR / "fragments" / "s4b_2.csv")
    ev = dict(script=SCRIPT, stock_after_s4b1=stk.round(1).reset_index().to_dict("records"), negative_caps=neg[["country", "tech", "raw"]].to_dict("records"), unallocated=unalloc.round(3).reset_index().to_dict("records"),
              ph_geothermal_rebuild_mw=float(rebuild.sum()), ph_geothermal_rebuild_nodes=rebuild.round(1).to_dict(),
              main_caps=main_[["country", "tech", "cap_mw", "basis", "grade"]].to_dict("records"),
              totals=cdf.groupby(["mode", "variant", "tech"]).cap_mw.sum().round(1).reset_index().to_dict("records"))
    write_json(ev, OUT / "CANDIDATE_CAPS_S4B2_EVIDENCE.json")
    pd.set_option("display.width", 250)
    print(main_[["country", "tech", "cap_mw", "grade", "basis"]].round(1).to_string(index=False))
    print("negative:", neg[["country", "tech", "raw"]].round(1).to_dict("records")); print("unallocated:", unalloc.round(2).to_dict()); print("PH rebuild", round(float(rebuild.sum()), 1), rebuild.round(1).to_dict())
    print(cdf.groupby(["mode", "variant", "tech"]).cap_mw.sum().round(0).unstack().to_string())


if __name__ == "__main__":
    main()
