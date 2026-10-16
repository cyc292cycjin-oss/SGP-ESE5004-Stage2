"""S4A-1 step 6: compare the rebuilt profiles with the original network profiles and across variants / classes.
Writes results_project/s4a/analysis/S4A_PROFILE_COMPARISON.json and CSV tables (by node, by country, by class).

    python scripts_project/s4a_1_compare.py --network results_project/s3b/smoke/builds/integrated/integrated_2920_3h_unsolved.nc
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
RV = ROOT / "research_inputs/renewable_v5"
TECHS = ["onwind", "offwind-ac", "offwind-dc", "solar"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--output", type=Path, default=ROOT / "results_project/s4a/analysis")
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    n = pypsa.Network(str(a.network)); w = n.snapshot_weightings.generators; g = n.generators
    pm = n.generators_t.p_max_pu
    ds = {v: xr.open_dataset(RV / f"profiles_{v}_c1_3h.nc") for v in ["fork", "pypsa_eur"]}
    cls3 = pd.read_csv(RV / "S4A_PROFILE_CLASSES_c3.csv") if (RV / "S4A_PROFILE_CLASSES_c3.csv").exists() else None
    rows = []
    for tech in TECHS:
        gens = g[g.carrier == tech]
        for name, z in gens.iterrows():
            node = str(z.bus); key = f"{node}|0"
            orig = pm[name].values if name in pm.columns else None
            r = dict(tech=tech, node=node, country=str(n.buses.at[node, "country"]), p_nom_max_mw=float(z.p_nom_max),
                     cf_original=float((orig * w.values).sum() / w.sum()) if orig is not None else np.nan)
            for v, d in ds.items():
                var = tech.replace("-", "_")
                if key in d[var].bus.values:
                    s = d[var].sel(bus=key).values.astype(float)
                    r[f"cf_{v}"] = float((s * w.values).sum() / w.sum())
                    if orig is not None and orig.std() > 0 and s.std() > 0:
                        r[f"corr_{v}_vs_original"] = float(np.corrcoef(orig, s)[0, 1]); r[f"mae_{v}_vs_original"] = float(np.abs(orig - s).mean())
            rows.append(r)
    df = pd.DataFrame(rows); df.to_csv(a.output / "S4A_PROFILE_COMPARISON_BY_NODE.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    out = {}
    for tech in TECHS:
        d = df[df.tech == tech]
        pw = lambda col: (d[col] * d.p_nom_max_mw.replace(np.inf, np.nan)).groupby(d.country).sum() / d.p_nom_max_mw.replace(np.inf, np.nan).groupby(d.country).sum()
        t = pd.DataFrame(dict(n=d.groupby("country").size(), cf_original_mean=d.groupby("country").cf_original.mean(), cf_original_max=d.groupby("country").cf_original.max(),
                              cf_fork_mean=d.groupby("country").cf_fork.mean(), cf_fork_max=d.groupby("country").cf_fork.max(), corr_fork_median=d.groupby("country")["corr_fork_vs_original"].median(),
                              cf_pypsa_eur_mean=d.groupby("country").cf_pypsa_eur.mean(), cf_pypsa_eur_max=d.groupby("country").cf_pypsa_eur.max(),
                              cf_original_capw=pw("cf_original"), cf_pypsa_eur_capw=pw("cf_pypsa_eur")))
        t["fork_minus_original"] = t.cf_fork_mean - t.cf_original_mean; t["pypsa_eur_over_original"] = t.cf_pypsa_eur_mean / t.cf_original_mean
        print("==", tech); print(t.round(3).to_string())
        out[tech] = dict(by_country=t.round(5).to_dict("index"),
                         overall=dict(cf_original=float(d.cf_original.mean()), cf_fork=float(d.cf_fork.mean()), cf_pypsa_eur=float(d.cf_pypsa_eur.mean()),
                                      corr_fork_median=float(d["corr_fork_vs_original"].median()), corr_fork_p10=float(d["corr_fork_vs_original"].quantile(0.1)),
                                      mae_fork_median=float(d["mae_fork_vs_original"].median()), quantiles_pypsa_eur={q: float(d.cf_pypsa_eur.quantile(q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)},
                                      quantiles_original={q: float(d.cf_original.quantile(q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}))
    if cls3 is not None:
        c = cls3.copy()
        tab = c.groupby(["tech", "variant", "country", "cls"]).apply(lambda x: pd.Series(dict(potential_gw=x.potential_mw.sum() / 1e3, cf=(x.cf_annual_weighted * x.potential_mw).sum() / x.potential_mw.sum(), nodes=x.node.nunique())), include_groups=False)
        tab.to_csv(a.output / "S4A_PROFILE_CLASSES_c3_BY_COUNTRY.csv")
        pe = tab.xs("pypsa_eur", level="variant")
        print("== classes (pypsa_eur) potential GW / cf by country and class"); print(pe.round(3).to_string())
        out["classes_c3"] = {f"{k[0]}|{k[1]}|{k[2]}|{k[3]}": dict(potential_gw=float(v.potential_gw), cf=float(v.cf), nodes=int(v.nodes)) for k, v in tab.iterrows()}
    (a.output / "S4A_PROFILE_COMPARISON.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
