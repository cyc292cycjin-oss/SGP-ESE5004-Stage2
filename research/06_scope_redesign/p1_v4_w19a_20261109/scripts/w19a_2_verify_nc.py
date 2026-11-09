"""W19a section 2.1 cross-check: read the v3.1 solved networks and their DUALS_BY_CONSTRAINT.nc directly (xarray, whole variables
once, one network at a time, MemAvailable >= 8 GiB checked before each) and recompute the KH CO2 account independently of the
W10 / D2a extraction caches.

Port flows: CO2 into the bus of port j = -sum_t w_t p_j,t (PyPSA sign: p_j > 0 withdraws from bus j), w = snapshots_objective.
This does not depend on whether a link efficiency is time-varying.

    python w19a_2_verify_nc.py <export dir> <out json>
"""
import gc
import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr

EXP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/hpc_results_v31/unpacked/export")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109/evidence/KH_NC_CROSSCHECK.json")
RUNS = {"F1": ("integrated_BATCH4_2920X3H_solved.nc", "F1"), "F2": ("no_new_xb_BATCH4_2920X3H_solved.nc", "F2")}
TRANSPORT = ("CO2 pipeline", "CO2 ship", "CO2 transit ship", "CO2 transit rail", "CO2 export extra-ASEAN")


def mem_avail_gib():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable"):
            return int(line.split()[1]) / 1024 ** 2
    return float("nan")


def strs(ds, name):
    return ds[name].values.astype(str)


def main():
    res = {}
    for lab, (ncname, sub) in RUNS.items():
        m = mem_avail_gib()
        if m < 8.0:
            raise SystemExit(f"MemAvailable {m:.2f} GiB < 8 GiB: stop before reading {lab}")
        nc = EXP / sub / ncname
        ds = xr.open_dataset(nc)
        r = dict(nc=str(nc), mem_avail_gib_before=round(m, 2), objective=float(ds.attrs["network_objective"]),
                 objective_constant=float(ds.attrs["network_objective_constant"]))
        w = ds["snapshots_objective"].values.astype(float)
        r["weights_sum"] = float(w.sum()); r["snapshots"] = int(len(w))
        bus_i = strs(ds, "buses_i"); carr = dict(zip(bus_i, strs(ds, "buses_carrier"))); ctry = dict(zip(bus_i, strs(ds, "buses_country")))
        st_i = strs(ds, "stores_i")
        def stat(var):
            return dict(zip(st_i, ds[var].values))
        emax, eopt, cc, ext = stat("stores_e_nom_max"), stat("stores_e_nom_opt"), stat("stores_capital_cost"), stat("stores_e_nom_extendable")
        e_last = dict(zip(strs(ds, "stores_t_e_i"), ds["stores_t_e"].values[-1, :]))
        r["stores"] = {c: dict(e_nom_max=float(emax.get(f"co2 sequestered {c}", np.nan)), e_nom_opt=float(eopt.get(f"co2 sequestered {c}", np.nan)),
                               e_last=float(e_last.get(f"co2 sequestered {c}", np.nan)), capital_cost=float(cc.get(f"co2 sequestered {c}", np.nan)),
                               extendable=bool(ext.get(f"co2 sequestered {c}", False)))
                       for c in ("KH", "TH", "VN", "PH")}
        li = strs(ds, "links_i"); lc = strs(ds, "links_carrier")
        acc, xb = {}, {}
        for j in range(5):
            bn, pn = f"links_bus{j}", f"links_t_p{j}"
            if bn not in ds or pn not in ds:
                continue
            buses = strs(ds, bn)
            pcols = {n: k for k, n in enumerate(strs(ds, f"{pn}_i"))}
            P = ds[pn].values  # whole variable once
            other = strs(ds, "links_bus1" if j == 0 else "links_bus0")
            for a, (name, bus) in enumerate(zip(li, buses)):
                if carr.get(bus) != "co2 stored" or ctry.get(bus) != "KH" or name not in pcols:
                    continue
                co2 = -float((P[:, pcols[name]] * w).sum())
                acc[lc[a]] = acc.get(lc[a], 0.0) + co2
                oc = ctry.get(other[a], "")
                if lc[a] in TRANSPORT and oc != "KH":
                    key = f"{lc[a]} {'out to' if co2 < 0 else 'in from'} {oc}"
                    xb[key] = xb.get(key, 0.0) + co2
            del P; gc.collect()
        r["kh_co2_stored_buses_by_carrier_t"] = {k: v for k, v in sorted(acc.items(), key=lambda x: x[1]) if abs(v) > 1e-3}
        r["kh_co2_stored_balance_t"] = float(sum(acc.values()))
        r["kh_cross_border_t"] = {k: v for k, v in xb.items() if abs(v) > 1e-3}
        ds.close(); del ds; gc.collect()
        # duals
        dd = xr.open_dataset(EXP / sub / "DUALS_BY_CONSTRAINT.nc")
        eu = dd["Store-ext-e_nom-upper"]
        coord = eu.dims[0]
        names = dd[coord].values.astype(str)
        eud = dict(zip(names, eu.values.astype(float)))
        r["duals"] = {c: dict(store_e_nom_upper=float(eud.get(f"co2 sequestered {c}", np.nan)),
                              global_row=float(np.nan_to_num(dd[f"research_co2_storage_cap-{c}"].values)) if f"research_co2_storage_cap-{c}" in dd else None,
                              country_co2_limit=float(np.nan_to_num(dd[f"research_country_co2_limit-{c}"].values)) if f"research_country_co2_limit-{c}" in dd else None)
                      for c in ("KH", "PH", "VN", "TH")}
        dd.close()
        res[lab] = r
        print(lab, json.dumps(r, indent=1, default=str))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
