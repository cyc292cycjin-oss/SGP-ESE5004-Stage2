"""W19a 2.2: static p_nom_max / extendable of the links used by the feasible re-route bound (KH sequestration links, KH export pipelines / ships), F1 and F2."""
import json, sys
import numpy as np, xarray as xr
EXP = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_results_v31/unpacked/export/"
out = {}
for lab, f in (("F1", "F1/integrated_BATCH4_2920X3H_solved.nc"), ("F2", "F2/no_new_xb_BATCH4_2920X3H_solved.nc")):
    ds = xr.open_dataset(EXP + f)
    li = ds["links_i"].values.astype(str)
    sel = [i for i, n in enumerate(li) if (n.startswith("KH2") and ("co2 sequestration" in n or "co2 ship to" in n)) or (n.startswith("CO2 pipeline KH2") and ("TH2" in n or "KH2 2" in n)) or n.startswith("VN2 0 co2 ship to") or n.startswith("TH2 3 co2 sequestration")]
    d = {}
    for i in sel:
        d[li[i]] = dict(p_nom=float(ds["links_p_nom"].values[i]), p_nom_max=float(ds["links_p_nom_max"].values[i]) if "links_p_nom_max" in ds else None,
                        p_nom_extendable=bool(ds["links_p_nom_extendable"].values[i]), p_nom_opt=float(ds["links_p_nom_opt"].values[i]),
                        capital_cost=float(ds["links_capital_cost"].values[i]), marginal_cost=float(ds["links_marginal_cost"].values[i]),
                        p_min_pu=float(ds["links_p_min_pu"].values[i]) if "links_p_min_pu" in ds else None)
    out[lab] = d
    ds.close()
json.dump(out, open("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109/evidence/KH_LINK_LIMITS.json", "w"), indent=1)
for lab, d in out.items():
    print("==", lab)
    for k, v in d.items():
        print(f"  {k:40s} ext={v['p_nom_extendable']} p_nom={v['p_nom']:.4g} p_nom_max={v['p_nom_max']} opt={v['p_nom_opt']:.4g} cc={v['capital_cost']:.6g} mc={v['marginal_cost']:.6g} pmin={v['p_min_pu']}")
