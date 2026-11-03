"""V3 supplement 07 (review EVDIAG section 2.1 item 3): rebuild check, read-only, no solver.
  * 2920x3h integrated / no_new_xb and the bridges 160-162 / 160-164 (365x24h): SHA256 = registered (RUN_PLAN_V3.md section 21.1) and byte-identical to builds_op;
  * V1 integrated / V2 no_new_xb / V3 disconnected (365x24h): every netCDF variable (data and coordinates) compared bit by bit, every global attribute compared, meta parsed and compared key by key.
    Allowed: the variable stores_t_e_min_pu, only in the columns of the 96 EV batteries; for V2 also meta research_variant.base.sha256, which must equal the new V1 SHA256 (V3_RULES.md section 11).
  * The new daily floor: 0.8 for every day and battery, equal to the daily max of the 2920x3h floor of the same battery; old 0.1; no stores_t.e_max_pu anywhere.
usage: python chk_dmax.py <builds_op> <builds_dmax> <evidence dir>"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

OLD, NEW, EV = map(Path, sys.argv[1:4]); EV.mkdir(parents=True, exist_ok=True)
REG = {"integrated/integrated_2920_3h_unsolved.nc": "1bddacb7c5d6b70df11a6f038001f291ff92a926b60610b30a27d2fe975853f8", "no_new_xb/no_new_xb_2920_3h_unsolved.nc": "b262f6aa76356e1bda20893ae324d5e3e351154b12b9fb2b951877dd469723c8",
       "bridge_160_162/integrated_365_24h_unsolved.nc": "910c037fc23dba7b5b06c1adb86beec81bcbb518c79d387e8eaef1d9388c9bbf", "bridge_160_164/integrated_365_24h_unsolved.nc": "20821ba9da5e304e710dad4464b6a0573710baeca11d212bf247772dfc08ee86",
       "integrated/integrated_365_24h_unsolved.nc": "330e1d3140f8953cc792719b087589f14bde179d833fbeb75ffa7ed1a12ec2b8", "no_new_xb/no_new_xb_365_24h_unsolved.nc": "7f4e87599ae859de4aba4384259d072dd96d4b73b4ad69508d279b9f8236a14f",
       "disconnected/disconnected_365_24h_unsolved.nc": "7ac161088371c8c0347cc018f0af8ba2e09e7575ace74f51a95e2b5101adfcbd"}
SAME = list(REG)[:4]; CHANGED = {"V1": "integrated/integrated_365_24h_unsolved.nc", "V2": "no_new_xb/no_new_xb_365_24h_unsolved.nc", "V3": "disconnected/disconnected_365_24h_unsolved.nc"}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
res = dict(byte_identical={}, changed={}, problems=[]); rows = []


def equal(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or a.dtype != b.dtype:
        return False
    if a.dtype.kind in "fc":
        return bool(np.array_equal(a.view(f"u{a.dtype.itemsize}"), b.view(f"u{b.dtype.itemsize}")))
    return bool(np.array_equal(a, b)) if a.dtype.kind in "iubM" else a.tolist() == b.tolist()


def meta_diff(a, b, path=()):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            out += [path + (k,)] if (k in a) != (k in b) else meta_diff(a[k], b[k], path + (k,))
        return out
    return [] if json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True) else [path]


for f in SAME:
    o, n = OLD / f, NEW / f; s = sha(n); same = n.read_bytes() == o.read_bytes()
    res["byte_identical"][f] = dict(sha256=s, bytes=n.stat().st_size, registered=s == REG[f], identical_to_builds_op=same)
    if not (same and s == REG[f]):
        res["problems"].append(f"{f}: not byte-identical / not the registered SHA256")
new_sha = {k: sha(NEW / f) for k, f in CHANGED.items()}
f3 = xr.open_dataset(NEW / "integrated/integrated_2920_3h_unsolved.nc", engine="netcdf4")
for rid, f in CHANGED.items():
    o = xr.open_dataset(OLD / f, engine="netcdf4", decode_cf=False, mask_and_scale=False); n = xr.open_dataset(NEW / f, engine="netcdf4", decode_cf=False, mask_and_scale=False)
    assert sha(OLD / f) == REG[f], f"{f}: builds_op is not the registered file"
    diff_vars = []
    for v in sorted(set(o.variables) | set(n.variables)):
        ok = v in o.variables and v in n.variables and o[v].dims == n[v].dims and equal(o[v].values, n[v].values) and repr(sorted(o[v].attrs.items())) == repr(sorted(n[v].attrs.items()))   # repr: a _FillValue NaN is never == itself
        rows.append(dict(run=rid, kind="variable", name=v, identical=bool(ok)))
        if not ok:
            diff_vars.append(v)
    attrs = sorted(set(o.attrs) | set(n.attrs)); diff_attrs = [k for k in attrs if k != "meta" and o.attrs.get(k) != n.attrs.get(k)]
    mo, mn = json.loads(o.attrs["meta"]), json.loads(n.attrs["meta"]); md = [".".join(map(str, p)) for p in meta_diff(mo, mn)]
    rows += [dict(run=rid, kind="attribute", name=k, identical=k not in diff_attrs) for k in attrs if k != "meta"] + [dict(run=rid, kind="meta key", name=k, identical=False) for k in md]
    # the store floor: columns, values, old / new, against the daily max of the 2920x3h floor
    cols = [str(x) for x in n["stores_t_e_min_pu_i"].values]; oc = [str(x) for x in o["stores_t_e_min_pu_i"].values]
    lo_n, lo_o = n["stores_t_e_min_pu"].values, o["stores_t_e_min_pu"].values
    st_idx = [str(x) for x in n["stores_i"].values]; carrier = dict(zip(st_idx, [str(x) for x in n["stores_carrier"].values])); e_nom = dict(zip(st_idx, n["stores_e_nom"].values.astype(float)))
    c3 = [str(x) for x in f3["stores_t_e_min_pu_i"].values]; lo3 = f3["stores_t_e_min_pu"].values
    daily_max = {c: lo3[:, c3.index(c)].reshape(365, 8).max(axis=1) for c in cols if c in c3}
    other_store_series = [v for v in n.variables if v.startswith("stores_t_") and not v.startswith("stores_t_e_min_pu")]
    chk = dict(columns=len(cols), columns_same_as_before=cols == oc, carriers=sorted(set(carrier[c] for c in cols)), all_ev_battery_names=all("EV battery" in c for c in cols),
               old_values=sorted(set(np.round(lo_o.ravel(), 12).tolist())), new_values=sorted(set(np.round(lo_n.ravel(), 12).tolist())), new_all_08=bool((lo_n == 0.8).all()), shape=list(lo_n.shape),
               new_equals_daily_max_of_2920x3h=(rid != "V3" and len(daily_max) == len(cols) and all(np.array_equal(lo_n[:, i], daily_max[c]) for i, c in enumerate(cols))) if rid != "V3" else None,
               e_max_pu_series=any(v.startswith("stores_t_e_max_pu") for v in n.variables), other_store_series=other_store_series,
               e_nom_twh=sum(e_nom[c] for c in cols) / 1e6, cross_day_band_twh_new=0.2 * sum(e_nom[c] for c in cols) / 1e6, cross_day_band_twh_old=0.9 * sum(e_nom[c] for c in cols) / 1e6)
    allowed_vars = {"stores_t_e_min_pu"}; allowed_meta = {"research_variant.base.sha256"} if rid == "V2" else set()
    ok = set(diff_vars) <= allowed_vars and not diff_attrs and set(md) <= allowed_meta and chk["columns"] == 96 and chk["columns_same_as_before"] and chk["all_ev_battery_names"] and chk["new_all_08"] and chk["old_values"] == [0.1] and not chk["e_max_pu_series"]
    if rid == "V1":
        ok = ok and chk["new_equals_daily_max_of_2920x3h"]
    if rid == "V2":
        ok = ok and md == ["research_variant.base.sha256"] and mn["research_variant"]["base"]["sha256"] == new_sha["V1"] and mo["research_variant"]["base"]["sha256"] == REG[CHANGED["V1"]]
    res["changed"][rid] = dict(file=f, sha256_old=REG[f], sha256_new=new_sha[rid], bytes_new=(NEW / f).stat().st_size, differing_variables=diff_vars, differing_attributes=diff_attrs, differing_meta_keys=md,
                               variables_compared=len(set(o.variables) | set(n.variables)), floor=chk, passed=bool(ok),
                               meta_base_sha256=dict(old=mo.get("research_variant", {}).get("base", {}).get("sha256"), new=mn.get("research_variant", {}).get("base", {}).get("sha256")) if rid == "V2" else None)
    if not ok:
        res["problems"].append(f"{rid}: differences beyond the 96 EV floors (variables {diff_vars}, attributes {diff_attrs}, meta {md}) or floor check failed")
    o.close(); n.close()
f3.close()
res["passed"] = not res["problems"]
(EV / "REBUILD_CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n"); pd.DataFrame(rows).to_csv(EV / "REBUILD_DIFF_V1_V2_V3.csv", index=False)
print(json.dumps(dict(passed=res["passed"], problems=res["problems"], same={k[:30]: v["identical_to_builds_op"] and v["registered"] for k, v in res["byte_identical"].items()},
                      changed={k: (v["sha256_new"][:8], v["differing_variables"], v["differing_meta_keys"], v["floor"]["columns"], v["floor"]["new_values"], v["floor"]["new_equals_daily_max_of_2920x3h"]) for k, v in res["changed"].items()}), default=str))
