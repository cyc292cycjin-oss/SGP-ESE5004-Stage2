"""M08a A7 evidence (no solve): derive the variants from the S4M-3 built base networks with scripts_project/m08a_variants.py
(--allow-stale-base: the bases were built with an earlier config; evidence of the mechanics only, not production inputs).
The variant networks are written to a scratch folder and deleted after the checks; receipts and checks are kept.

    PYTHONHASHSEED=0 python m08a_a7_evidence.py --repo /home/jin/wt_m08a_20261021 \
        --builds /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds \
        --scratch /home/jin/m08a_scratch --out <work dir>
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def ports(n):
    out = set()
    for c in n.iterate_components(["Generator", "Load", "Store", "StorageUnit", "Link", "Line"]):
        for col in [k for k in c.df.columns if k == "bus" or (k.startswith("bus") and k[3:].isdigit())]:
            out |= set(c.df[col])
    return out - {""}


def demand(n):
    return float(n.get_switchable_as_dense("Load", "p_set").mul(n.snapshot_weightings.generators, axis=0).sum().sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--builds", type=Path, required=True)
    ap.add_argument("--scratch", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import pypsa
    from m08a_variants import derive
    base = {s: a.builds / s / f"{s}_2920_3h_unsolved.nc" for s in ("integrated", "disconnected")}
    jobs = [("keep_stock_from_integrated", "integrated", {"cross_border.stock_mode": "keep_stock_no_new"}),
            ("no_intra_co2_shipping_from_disconnected", "disconnected", {"disconnected.co2_shipping_intra_asean": "forbid"}),
            ("minus_VN_from_integrated", "integrated", {"coalition.remove_countries": ["VN"]}),
            ("minus_VN_from_disconnected", "disconnected", {"coalition.remove_countries": ["VN"]}),
            ("country_wacc_from_integrated", "integrated", {"finance.wacc_mode": "country_specific"})]
    ev = dict(schema="m08a-a7-variants-evidence-v1", solver_runs=0, stale_bases_allowed=True, note="bases = S4M-3 builds (earlier config); mechanics only", runs={})
    a.scratch.mkdir(parents=True, exist_ok=True)
    for tag, sc, sets in jobs:
        out = a.scratch / tag
        r = derive(a.repo, base[sc], out, sets, None, True)
        r2 = derive(a.repo, base[sc], a.scratch / (tag + "_repeat"), sets, None, True)
        chk = dict(deterministic=r["output"]["sha256"] == r2["output"]["sha256"])
        if "coalition.remove_countries" in sets:
            b = pypsa.Network(str(base[sc])); v = pypsa.Network(r["output"]["path"])
            vn_loads = [x for x in b.loads.index if str(b.loads.at[x, "country"]) == "VN" or str(b.buses.at[b.loads.at[x, "bus"], "country"]) == "VN"]
            dvn = float(b.get_switchable_as_dense("Load", "p_set")[vn_loads].mul(b.snapshot_weightings.generators, axis=0).sum().sum())
            vn_buses = set(b.buses.index[b.buses.country == "VN"])
            chk.update(demand_base_twh=demand(b) / 1e6, demand_variant_twh=demand(v) / 1e6, demand_vn_twh=dvn / 1e6,
                       remaining_equals_base_minus_vn=abs(demand(v) - (demand(b) - dvn)) <= 1e-6 * demand(b),
                       references_to_vn_buses=len(ports(v) & vn_buses), vn_buses_left=int((v.buses.country == "VN").sum()),
                       bunker_loads_kept=int(v.loads.index.str.contains("international").sum()), research_countries=v.meta.get("research_countries"))
        ev["runs"][tag] = dict(receipt=r, checks=chk)
        for p in (out, a.scratch / (tag + "_repeat")):
            for f in p.glob("*.nc"):
                f.unlink()
        print(tag, json.dumps(chk, default=str))
    (a.out / "evidence").mkdir(parents=True, exist_ok=True)
    (a.out / "evidence" / "M08A_A7_VARIANTS.json").write_text(json.dumps(ev, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    shutil.rmtree(a.scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
