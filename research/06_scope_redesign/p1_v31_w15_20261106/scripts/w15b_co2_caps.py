import sys, json, numpy as np, xarray as xr, pandas as pd, csv
from pathlib import Path
out = Path(sys.argv[1]); res = {}
for lab, d in [a.split("=", 1) for a in sys.argv[2:]]:
    d = Path(d); ds = xr.open_dataset(d / "DUALS_BY_CONSTRAINT.nc")
    da = ds["Store-ext-e_nom-upper"]; s = pd.Series(np.nan_to_num(da.values.astype(float)), index=[str(x) for x in da[da.dims[0]].values])
    R = json.loads((d / "SOLVE_RECEIPT.json").read_text(encoding="utf-8")); seq = R["co2_flows"]["sequestered_by_country"]
    rhs = {}
    p = d / "m12_owen" / "RHS_BY_FAMILY_OWNER.csv"
    if p.exists():
        for r in csv.DictReader(p.open(encoding="utf-8")):
            if r["family"] in ("Store-ext-e_nom-upper", "research_co2_storage_cap"):
                rhs.setdefault(r["owner"], {})[r["family"]] = float(r["rhs_sum"])
    res[lab] = {}
    for cc, v in seq.items():
        g = float(np.nan_to_num(ds[f"research_co2_storage_cap-{cc}"].values)) if f"research_co2_storage_cap-{cc}" in ds else None
        b = float(s.get(f"co2 sequestered {cc}", 0.0))
        res[lab][cc] = dict(used_t=v["final_level_t"], cap_t=v["e_nom_max"], used_share=v["final_level_t"] / v["e_nom_max"], slack_t=v["e_nom_max"] - v["final_level_t"],
                            dual_global_row=g, dual_store_e_nom_upper=b, scarcity_value_eur=abs(b) * v["e_nom_max"] + abs(g or 0.0) * v["e_nom_max"],
                            rhs_owner=rhs.get(cc))
    ds.close()
(out / "evidence" / "KH_CO2_CAP.json").write_text(json.dumps(dict(
    finding=("the national CO2 storage limit appears twice in the LP with the same right-hand side: the global row research_co2_storage_cap-<CC> and the "
             "capacity bound of the Store 'co2 sequestered <CC>' (e_nom <= e_nom_max). The barrier solution puts the whole dual on the Store bound, so the global "
             "row shows 0 while the limit is used to within 1e-7 (degenerate duplicate, not a zero value). Both rows are owned by the same country in the Owen RHS "
             "audit with the same RHS, so y'b does not depend on how the dual is split (EXACT)."),
    runs=res), indent=1) + "\n", encoding="utf-8", newline="\n")
for lab, v in res.items():
    print(lab, {cc: (round(x["used_share"], 8), round(x["dual_store_e_nom_upper"], 3), x["dual_global_row"], round(x["scarcity_value_eur"] / 1e6, 1)) for cc, x in v.items() if x["used_share"] > 0.999})
