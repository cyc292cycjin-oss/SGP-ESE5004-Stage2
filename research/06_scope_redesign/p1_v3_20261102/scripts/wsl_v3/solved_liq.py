"""V3 phase 1: liquids in the solved v2 runs V1 / V2 (365x24h), existing bunker node shares of the assembly allocation. Read only on the packs; extraction under results_project/v3/intake/."""
import json, tarfile, logging
from pathlib import Path
import numpy as np, pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 150)
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); INT = MAIN / "results_project/v3/intake/dfx_solved"; INT.mkdir(parents=True, exist_ok=True); OUT = MAIN / "results_project/v3/phase1"
T = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_results/final_20261026T223024Z/results_full_final_20261026T223024Z.tar.gz"
want = {"export/V1/integrated_DFX_365X24H_solved.nc": "V1.nc", "export/V2/disconnected_DFX_365X24H_solved.nc": "V2.nc"}
if not all((INT / v).exists() for v in want.values()):
    with tarfile.open(T, "r:gz") as x:
        for m in x:
            if m.name in want:
                f = x.extractfile(m); (INT / want[m.name]).write_bytes(f.read()); print("extracted", m.name, m.size)
res = {}
for lab in ("V1", "V2"):
    n = pypsa.Network(str(INT / f"{lab}.nc")); w = n.snapshot_weightings.objective; L = n.links; p0 = n.links_t.p0; p1 = n.links_t.p1
    bc = lambda s: n.buses.country.reindex(s).astype(str).values
    def flow(sel, port="p1", sign=-1.0):
        d = n.links_t[port].reindex(columns=sel, fill_value=0.0) * sign
        return d.mul(w, axis=0).sum()
    r = {}
    for car, bus in [("methanol", "ASEAN methanol"), ("ammonia", "ASEAN ammonia"), ("oil_nf", "ASEAN oil non-fossil"), ("oil", "ASEAN oil")]:
        rows = {}
        for col, pn in (("bus0", "p0"), ("bus1", "p1")):
            s = L.index[L[col] == bus]
            e = n.links_t[pn].reindex(columns=s, fill_value=0.0).mul(w, axis=0).sum() / 1e6   # + = withdrawn from the pool bus (TWh)
            for k, v in e.items():
                key = (str(L.at[k, "country"]), str(L.at[k, "carrier"]))
                rows[key] = rows.get(key, 0.0) + float(v)
        t = pd.Series(rows).unstack(0).fillna(0.0)
        g = n.generators[n.generators.bus == bus]; imp = float((n.generators_t.p[g.index] .mul(w, axis=0)).sum().sum() / 1e6)
        ld = n.loads[n.loads.bus == bus]; loads = n.get_switchable_as_dense("Load", "p_set")[ld.index].mul(w, axis=0).sum().groupby(ld.country).sum() / 1e6 if len(ld) else pd.Series(dtype=float)
        pr = n.buses_t.marginal_price[bus]
        st = n.stores[n.stores.bus == bus]
        r[car] = dict(import_twh=imp, price_mean=float(pr.mean()), price_min=float(pr.min()), price_max=float(pr.max()), store_e_nom_opt_twh=float(st.e_nom_opt.sum() / 1e6) if len(st) else 0.0)
        print(lab, car, r[car]); print((t.round(1)).to_string()); print("loads", loads.round(1).to_dict())
        t.to_csv(OUT / f"V2SOL_{lab}_{car}_BY_COUNTRY.csv")
    res[lab] = r
    print(lab, "objective", n.objective)
Path(OUT / "V2_SOLVED_LIQUIDS.json").write_text(json.dumps(res, indent=1))
# bunker node shares in the Assembly allocation
am = json.load(open(MAIN / "results_project/assembly_v1/final_allocation/allocation_manifest.json"))
z = np.load(MAIN / "results_project/assembly_v1/final_allocation" / am["arrays_file"], allow_pickle=False)
print({k: (am[k] if not isinstance(am[k], (list, dict)) else type(am[k]).__name__) for k in am if k not in ("records",)})
for ar in am["records"]:
    c, y, s, acc, car = ar["InputID"].split(":")
    if acc in ("InternationalShippingBunker", "InternationalAviationBunker", "DomesticShippingFuel") and c in ("ID", "MY", "TH", "VN", "PH"):
        a = np.asarray(z[ar["ArrayKey"]], dtype=float); a = a.reshape(-1, 1) if a.ndim == 1 else a
        sh = a.sum(axis=0) / a.sum()
        print(ar["InputID"], ar["Method"], {nd: round(float(v), 3) for nd, v in sorted(zip(ar["Nodes"], sh), key=lambda t: -t[1])[:6]})
