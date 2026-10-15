"""S3-7 result summary of a solved 56x3h smoke / gap_diagnostic network (SMOKE_TEST_ONLY, representative weights 8760/N):
net-zero by country (B1), import volumes and structure, CO2 destinations, Singapore supply mix, and the B5/B6 trial between the
integrated and disconnected solutions. No scientific meaning before the cloud run (decision 47).

    python scripts_project/s3_7_results_summary.py --integrated <solved nc> [--disconnected <solved nc>] --output <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

IMPORT_CARRIERS = ["LNG import", "oil import", "ammonia import", "methanol import", "FT fuel import", "H2 import", "gas production"]


def annual(n, df_t, w):
    return df_t.mul(w, axis=0).sum()


def summarise(n):
    w = n.snapshot_weightings.generators
    g = n.generators; gp = annual(n, n.generators_t.p, w)
    out = {}
    imp = g[g.carrier.isin(IMPORT_CARRIERS)]
    tab = pd.DataFrame(dict(carrier=imp.carrier, country=imp.country, mwh=gp.reindex(imp.index).fillna(0.0), p_nom_opt=imp.p_nom_opt))
    out["imports_twh_by_carrier"] = (tab.groupby("carrier").mwh.sum() / 1e6).round(3).to_dict()
    out["imports_twh_by_country_carrier"] = {f"{c}|{k}": round(v / 1e6, 3) for (c, k), v in tab.groupby(["country", "carrier"]).mwh.sum().items() if v > 1e-6}
    out["import_capacity_mw_by_carrier"] = tab.groupby("carrier").p_nom_opt.sum().round(1).to_dict()
    # domestic production vs cap
    caps = n.meta.get("external_annual_caps", {})
    prod = tab[tab.carrier == "gas production"]
    out["gas_production_vs_cap_twh"] = {c: dict(production=round(float(d.mwh.sum()) / 1e6, 3), cap=round(sum(caps.get(i, 0.0) for i in d.index) / 1e6, 3)) for c, d in prod.groupby("country")}
    # conversions on the regional buses
    L = n.links; lp0 = annual(n, n.links_t.p0, w); lp1 = -annual(n, n.links_t.p1, w)
    for car in ["Haber-Bosch", "ammonia cracker", "methanolisation", "biomass-to-methanol", "OCGT methanol", "Fischer-Tropsch", "BtL", "shipping methanol", "industry methanol", "industry ammonia"]:
        sel = L[L.carrier == car]
        if len(sel):
            out.setdefault("conversion_twh_output", {})[car] = round(float(lp1.reindex(sel.index).fillna(0.0).sum()) / 1e6, 3)
    sm = L[L.carrier == "shipping methanol"]
    out["shipping_methanol_twh_by_country"] = {c: round(float(lp1.reindex(d.index).fillna(0.0).sum()) / 1e6, 3) for c, d in sm.groupby("country")}
    # CO2 destinations
    st = n.stores
    seq = st[st.index.str.startswith("co2 sequestered")]
    out["co2_sequestered_mt_by_country"] = {s.split()[-1]: round(float(n.stores_t.e[s].iloc[-1]) / 1e6, 3) for s in seq.index}
    cap_links = L[L.carrier.isin(["CCGT CC", "SMR CC", "biomass EOP CC", "process emissions CC", "DAC", "industry biomass CC", "industry biomass boiler CC"])]
    out["co2_captured_mt_by_carrier"] = {}
    for car, d in cap_links.groupby("carrier"):
        col = "p3" if car in ("CCGT CC", "SMR CC", "biomass EOP CC") else ("p2" if car == "DAC" else "p3")
        tot = 0.0
        for name in d.index:
            for c in ["p1", "p2", "p3", "p4"]:
                b = L.at[name, "bus" + c[1:]] if ("bus" + c[1:]) in L else ""
                if isinstance(b, str) and b.endswith(" co2 stored") and c in n.links_t and name in n.links_t[c]:
                    tot += -float((n.links_t[c][name] * w).sum())
        out["co2_captured_mt_by_carrier"][car] = round(tot / 1e6, 3)
    xb = L[(L.carrier == "CO2 pipeline") & (L.border_class == "cross_border")]
    out["co2_cross_border_mt"] = {name: round(float((n.links_t.p0[name] * w).sum()) / 1e6, 3) for name in xb.index if abs(float((n.links_t.p0[name] * w).sum())) > 1e3}
    # net emissions
    from country_carbon import emission_report
    rep = emission_report(n)
    out["net_emissions_t_by_country"] = {k: round(v, 1) for k, v in rep["by_country"].items()}
    out["atmosphere_final_level_t"] = {k: round(v, 1) for k, v in rep["store_final_level"].items()}
    # Singapore supply mix
    sg_nodes = [b for b in n.buses.index if n.buses.at[b, "carrier"] == "AC" and n.buses.at[b, "country"] == "SG"]
    gen_sg = g[g.bus.isin(sg_nodes)]
    out["sg_electricity_generation_twh"] = {c: round(float(gp.reindex(d.index).fillna(0).sum()) / 1e6, 3) for c, d in gen_sg.groupby("carrier") if float(gp.reindex(d.index).fillna(0).sum()) > 1e3}
    lines_sg = n.lines[(n.lines.bus0.isin(sg_nodes)) ^ (n.lines.bus1.isin(sg_nodes))]
    out["sg_electricity_import_twh"] = round(sum(float((n.lines_t.p1[i] * w).sum()) * (-1 if n.lines.at[i, "bus1"] in sg_nodes else 1) for i in lines_sg.index) / 1e6, 3) if len(lines_sg) else 0.0
    sg_links_in = L[(L.bus1.isin(sg_nodes)) & (L.carrier.isin(["CCGT", "OCGT", "CCGT CC", "OCGT methanol", "CCGT existing", "H2 fuel cell", "oil existing"]))]
    out["sg_electricity_links_twh"] = {c: round(float(lp1.reindex(d.index).fillna(0).sum()) / 1e6, 3) for c, d in sg_links_in.groupby("carrier")}
    out["sg_imports_twh"] = {k.split("|")[1]: v for k, v in out["imports_twh_by_country_carrier"].items() if k.startswith("SG|")}
    out["sg_gas_pipeline_in_twh"] = {name: round(float((n.links_t.p0[name] * w).sum()) / 1e6, 3) for name in L.index[(L.carrier == "gas pipeline") & L.bus1.str.startswith("SG2")]}
    out["objective"] = float(n.objective) if hasattr(n, "objective") else None
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument("--integrated", type=Path, required=True); p.add_argument("--disconnected", type=Path, default=None); p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    import pypsa, logging
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    ni = pypsa.Network(str(a.integrated)); out = dict(integrated=summarise(ni))
    if a.disconnected and a.disconnected.exists():
        nd = pypsa.Network(str(a.disconnected)); out["disconnected"] = summarise(nd)
        from v5.v5_gates import gate_b5_single_switch, gate_b6_cost
        from phase4_static import config
        out["B5"] = gate_b5_single_switch(config(HERE.parent, "integrated"), config(HERE.parent, "disconnected"), n_dis_solved=nd, n_int_solved=ni)
        out["B6"] = gate_b6_cost(float(ni.objective), float(nd.objective))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=1, default=str))
    for k, v in out.items():
        if k in ("integrated", "disconnected"):
            print("==", k, "objective", v["objective"]); print("  imports TWh:", v["imports_twh_by_carrier"]); print("  gas production vs cap:", v["gas_production_vs_cap_twh"]); print("  conversions:", v.get("conversion_twh_output"))
            print("  sequestered Mt:", v["co2_sequestered_mt_by_country"]); print("  net emissions:", v["net_emissions_t_by_country"]); print("  SG gen:", v["sg_electricity_generation_twh"], "SG links:", v["sg_electricity_links_twh"], "SG imports:", v["sg_imports_twh"], "SG line import TWh:", v["sg_electricity_import_twh"])
        else:
            print("==", k, v.get("passed"), {kk: vv for kk, vv in v.items() if kk in ("objective", "difference", "relative", "disconnected_cross_border_capacity_mw", "disconnected_cross_border_abs_flow_mw", "config_differences")})


if __name__ == "__main__":
    main()
