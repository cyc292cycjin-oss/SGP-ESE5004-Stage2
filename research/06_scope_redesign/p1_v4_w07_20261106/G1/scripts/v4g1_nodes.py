"""V4 W07 G1 step 8 (Malaysia): spatial allocation of the v4 sub-sectors to the v3 onshore nodes, against the v3 shares.

    PROJ_LIB=... python scripts/v4g1_nodes.py        (WSL pypsa-earth python; after v4g1_products.py)

steel, cement   GEM capacity weights of the v3 input files re-computed with the S1 point-in-region rule (method check; no MY plant output in GEM).
aluminium       v3 (USGS GIS smelters) kept.
ammonia         GEM plants weighted by 2019 output (capacity x USGS national utilisation) against the v3 ammonia load shares (general industry pattern).
methanol, HVC   GEM plants weighted by the 2019 activity of tables/MY_CHEM_ENERGY.csv (central).
pulp and paper  SFI 2025-07 mills: paper by capacity (unknown capacities share the remainder), pulp by pulp capacity; combined by the 2019 energy split.
lime            no facility data: v3 'other' shares.
other           v3: DOSE 2019 manufacturing output by ADM1 x node electricity (one pattern for every carrier). Proposal: carrier-specific regional totals from
                NEB 2019 (table 17 industry electricity, table 7 industry gas by region) minus the explicit sub-sectors of that region (aluminium, chemicals),
                split inside the region by the v3 DOSE shares; option B moves the unexplained Sabah gas to NEU (chain sensitivity) before the split.
Single-node differences above 5 percentage points are explained in the note column. Output tables/MY_NODE_SHARES.csv, tables/_nodes_evidence.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g1_common as cm   # noqa: E402

OUT = cm.G1 / "tables"
REG_NODES = {"Peninsular Malaysia": ["MY_Peninsular2 0", "MY_Peninsular2 1"], "Sabah": ["MY_Sabah4 0", "MY_Sabah4 1"], "Sarawak": ["MY_Sarawak4 0", "MY_Sarawak4 1", "MY_Sarawak4 2"]}


def shares(df, wcol, node="node"):
    s = df.groupby(node)[wcol].sum(); s = s[s > 0]
    return (s / s.sum()).to_dict()


def main():
    import geopandas as gpd
    ev = cm.Ev("nodes")
    regions = gpd.read_file(cm.MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    v3s = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv"); v3s = v3s[v3s.country == cm.CC]
    v3c = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_CARRIER_NODE_SHARES_V3.csv"); v3c = v3c[(v3c.country == cm.CC) & (v3c.case == "main")]
    v3 = {k: g.set_index("node").share.to_dict() for k, g in v3s.groupby("subsector")}
    v3["ammonia"] = v3c[v3c.carrier == "ammonia"].set_index("node").share.to_dict()
    rows = []

    def add(sub, v4, v3_, note_fn, method):
        nodes = sorted(set(v4) | set(v3_))
        for n in nodes:
            a, b = v4.get(n, 0.0), v3_.get(n, 0.0)
            rows.append(dict(country=cm.CC, subsector=sub, node=n, share_v4=a, share_v3=b, diff_pp=(a - b) * 100, method=method, note=note_fn(n, a, b) if abs(a - b) > 0.05 else ""))
    # ---- steel / cement: recompute the v3 capacity weights (method check)
    for sub, f in (("steel", "GEM_STEEL_ASEAN_OPERATING_V3.csv"), ("cement", "GEM_CEMENT_ASEAN_OPERATING_V3.csv")):
        g = pd.read_csv(cm.REPO / "research_inputs/industry_v3" / f); g = g[g.iso == cm.CC].copy()
        g["node"], g["node_method"] = cm.node_of(g, regions)
        sh = shares(g, "weight")
        add(sub, sh, v3[sub], lambda n, a, b: "", f"GEM capacity weights ({len(g)} plants) re-computed, point in region; equals v3 (same GEM version, no MY plant output)")
        ev.put(f"{sub}.max_abs_diff_pp", max(abs(sh.get(n, 0) - v3[sub].get(n, 0)) for n in set(sh) | set(v3[sub])) * 100, "pp", "re-computed vs INDUSTRY_NODE_SHARES_V3.csv", "EXACT", "B")
    add("nonferrous_aluminium_primary", v3["nonferrous_aluminium_primary"], v3["nonferrous_aluminium_primary"], lambda *a: "", "v3 kept (USGS GIS: Press Metal Samalaju 960 kt, Mukah 120 kt)")
    # ---- chemicals
    ce = pd.read_csv(OUT / "MY_CHEM_ENERGY.csv"); ce = ce[(ce.level == "central") & ce.in_2019_base]
    cp = pd.read_csv(OUT / "MY_CHEM_PLANTS.csv")
    nm = lambda n, prods: "; ".join(f"{p} ({m})" for p, m in cp[(cp.node == n) & cp["product"].isin(prods) & cp.in_2019_base][["plant", "node_method"]].drop_duplicates().itertuples(index=False))
    a = ce[ce["product"] == "ammonia"]
    add("ammonia", shares(a, "activity_2019_t"), v3["ammonia"],
        lambda n, x, y: (f"plants: {nm(n, ['ammonia'])}" if x > y else "v3 spreads the ammonia load by the general industry pattern; no ammonia plant at this node"),
        "GEM plants x 2019 output (capacity x USGS 2019 / GEM capacity = 0.691)")
    add("methanol", shares(ce[ce["product"] == "methanol"], "activity_2019_t"), {}, lambda n, x, y: f"plant: {nm(n, ['methanol'])}" if x > 0 else "",
        "GEM plant (2019 base); Sarawak Petchem 2023 (MY_Sarawak4 0) only in the R4 sensitivity")
    h = ce[ce["product"].isin(["olefins", "aromatics"])]
    add("hvc", shares(h, "activity_2019_t"), {}, lambda n, x, y: f"plants: {nm(n, ['olefins', 'aromatics'])}" if x > 0 else "", "GEM plants x 2019 HVC activity (Titan, Kerteh); PIC Pengerang (MY_Peninsular2 1) only in R4")
    # ---- pulp and paper
    sf = pd.read_csv(OUT / "MY_PULP_PAPER_MILLS_SFI.csv")
    P = json.loads((OUT / "_products_evidence.json").read_text()); pv = {x["key"]: x["value"] for x in P["numbers"]}
    e_pulp = pv.get("products.pp.energy.2019 deduction (FAOSTAT 2019 x JRC-IDE", np.nan)
    pp_df = pd.read_csv(OUT / "MY_PULP_PAPER_ENERGY.csv")
    ep, eq = float(pp_df.pulp_twh.iloc[0]), float(pp_df.paper_twh.iloc[0])
    sp_ = shares(sf, "w_pulp") if sf.w_pulp.sum() > 0 else {}
    sq_ = shares(sf, "w_paper")
    comb = {n: (ep * sp_.get(n, 0.0) + eq * sq_.get(n, 0.0)) / (ep * (1 if sp_ else 0) + eq) for n in set(sp_) | set(sq_)}
    add("pulp_paper", comb, v3["other"], lambda n, x, y: ("SFI mills: " + ", ".join(sf[sf.node == n].plant_name.astype(str).head(4))) if x > 0 else "no SFI mill with weight at this node",
        f"SFI 2025-07 ({len(sf)} mills; paper capacity known for {int(sf.cap_paper.notna().sum())}); compared with v3 'other' (where the energy sat in v3)")
    add("lime", v3["other"], v3["other"], lambda *a: "", "no facility data: v3 'other' shares")
    # ---- other: NEB regional proposal
    neb = json.loads((OUT / "_base_evidence.json").read_text())["extra"]["neb_checks"]
    ch = json.loads((OUT / "_chain_evidence.json").read_text()) if (OUT / "_chain_evidence.json").exists() else None
    al = pd.read_csv(OUT / "MY_ALUMINIUM_CHECK.csv").set_index("item").value
    al_el19 = float(al["v3 2019-equivalent aluminium electricity (750 kt)"])
    el_reg = {r: float(neb[f"industry_electricity_share_{r}"]) * float(neb["industry_electricity_twh"]) for r in REG_NODES}
    gas_reg = {r: float(neb[f"industry_gas_twh_{r}"]) for r in REG_NODES}
    chem_g = ce.groupby("region").deduct_gas_2019_mwh.sum() / 1e6; chem_e = ce.groupby("region").deduct_el_2019_mwh.sum() / 1e6
    el_res = {r: max(0.0, el_reg[r] - float(chem_e.get(r, 0.0)) - (al_el19 if r == "Sarawak" else 0.0)) for r in REG_NODES}
    gas_res = {r: max(0.0, gas_reg[r] - float(chem_g.get(r, 0.0))) for r in REG_NODES}
    gas_res_b = dict(gas_res); gas_res_b["Sabah"] = 0.0
    vo = v3["other"]

    def split(reg_tot):
        tot = sum(reg_tot.values()); out = {}
        for r, ns in REG_NODES.items():
            w = {n: vo.get(n, 0.0) for n in ns}; sw = sum(w.values())
            for n in ns:
                out[n] = reg_tot[r] / tot * (w[n] / sw if sw else 1.0 / len(ns))
        return out
    regnote = lambda kind, rt: (lambda n, x, y: f"NEB 2019 {kind}: " + ", ".join(f"{r} {v / sum(rt.values()):.1%}" for r, v in rt.items()) + "; v3 regions: " +
                                ", ".join(f"{r} {sum(vo.get(k, 0) for k in REG_NODES[r]):.1%}" for r in REG_NODES))
    add("other (electricity), proposal", split(el_res), vo, regnote("industry electricity minus aluminium and chemicals", el_res), "NEB table 17 by region minus explicit; DOSE inside the region")
    add("other (heat bands and oil), proposal A", split(gas_res), vo, regnote("industry gas minus chemicals", gas_res), "NEB table 7 by region minus explicit chemicals; DOSE inside the region")
    add("other (heat bands and oil), proposal B (Sabah unexplained gas to NEU)", split(gas_res_b), vo, regnote("industry gas minus chemicals, Sabah residual to NEU", gas_res_b), "as A, Sabah residual moved to NEU")
    for r in REG_NODES:
        ev.put(f"other.region.{r}.electricity_residual_2019", el_res[r], "TWh", "NEB 2019 table 17 x UNSD industry electricity minus aluminium (Sarawak) and chemical electricity (central)", "INFERENCE", "B/C")
        ev.put(f"other.region.{r}.gas_residual_2019", gas_res[r], "TWh", "NEB 2019 table 7 share x UNSD industry gas minus chemical gas (central)", "INFERENCE", "B/C")
        ev.put(f"other.region.{r}.v3_share", sum(vo.get(k, 0) for k in REG_NODES[r]), "-", "INDUSTRY_NODE_SHARES_V3.csv other", "VERIFIED", "C")
    N = pd.DataFrame(rows)
    N.to_csv(OUT / "MY_NODE_SHARES.csv", index=False, float_format="%.6f")
    big = N[N.diff_pp.abs() > 5]
    for r in big.itertuples():
        ev.put(f"diff_gt_5pp.{r.subsector}.{r.node}", r.diff_pp, "pp", r.note[:200], "PROPOSED (quantified)", "C")
    ev.write(OUT / "_nodes_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 110); pd.set_option("display.max_rows", 200)
    print(N[["subsector", "node", "share_v4", "share_v3", "diff_pp", "note"]].round(4).to_string())
    print(json.dumps(dict(el_res=el_res, gas_res=gas_res), indent=1))


if __name__ == "__main__":
    main()
