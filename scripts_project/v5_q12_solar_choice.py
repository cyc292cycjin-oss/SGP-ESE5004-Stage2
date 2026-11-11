"""V5 X20 Q12 (decision 246; X20_SPEC_ADDENDUM_246.md section 3, the rule fixed before this computation): profile of the existing solar components.

Candidates (one rule for all 11 countries): (i) node average = the one-class node solar profile of the variant (the column of '<node> solar rooftop-2025',
s4a_layers: rooftop PV gets the c1 node solar profile), (ii) best class = the highest '<node> solar-2025 c{k}' column (falling back class by class);
class 0 ('<node> solar-2025', v4) is reported only. Model CF of a country = p_nom-weighted, snapshot-weighted annual mean p_max_pu of every existing solar
component (carrier 'solar existing') under a candidate. Observed CF = Ember yearly data, the s4b_3_wind_calibration.observed rule with Solar
(X20 B scripts/25_ember_solar_cf.py: CF = generation / (8,760 x mean of the year and previous-year capacity), 2019-2025, growth > 50 % dropped, median;
usable when max capacity >= 0.2 GW and >= 2 valid years). E = sum_c w_c |CF_c,model - CF_c,Ember| / sum_c w_c, w_c = existing solar p_nom of country c,
countries with an observation only. The smaller E wins for all countries; |E_i - E_ii| < 1e-4 -> node average.
Input: a 2920x3h v5 build (all candidate columns are present whatever existing_solar_profile was used). Output EXISTING_SOLAR_PROFILE_CHOICE.csv / .json.
    python scripts_project/v5_q12_solar_choice.py --network <v5 integrated_2920_3h_unsolved.nc> --ember <EMBER_SOLAR_CF_SUMMARY.csv>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/renewable_v5/EXISTING_SOLAR_PROFILE_CHOICE.csv"
TIE = 1e-4


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--ember", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=OUT); a = ap.parse_args(argv)
    ds = xr.open_dataset(a.network)
    g = pd.DataFrame({k: ds[f"generators_{k}"].values for k in ("carrier", "bus", "p_nom")}, index=ds["generators_i"].values.astype(str))
    g["carrier"] = g.carrier.astype(str); g["bus"] = g.bus.astype(str)
    cty = pd.Series(ds["buses_country"].values.astype(str), index=ds["buses_i"].values.astype(str))
    P = pd.DataFrame(ds["generators_t_p_max_pu"].values, columns=ds["generators_t_p_max_pu_i"].values.astype(str))
    w = ds["snapshots_generators"].values.astype(float) if "snapshots_generators" in ds else np.ones(len(P))
    ds.close()
    cf = lambda col: float((P[col].values * w).sum() / w.sum())   # noqa: E731
    ex = g[g.carrier == "solar existing"].copy(); ex["country"] = ex.bus.map(cty)
    rows = []
    for name, r in ex.iterrows():
        node = name.split("::")[1] if name.startswith("existing_survivor::") else r.bus   # the GEM-addition node (dedicated plant nodes moved the unit behind '<node> dedicated src')
        base = f"{node} solar-2025"; roof = f"{node} solar rooftop-2025"
        best = next((f"{base} c{k}" for k in range(9, 0, -1) if f"{base} c{k}" in P.columns), base)
        rows.append(dict(component=name, country=r.country, node=node, p_nom_mw=float(r.p_nom), own_cf=(cf(name) if name in P.columns else np.nan),
                         cf_class0=cf(base), cf_node_average=(cf(roof) if roof in P.columns else np.nan), cf_best_class=cf(best), best_column=best))
    U = pd.DataFrame(rows)
    em = pd.read_csv(a.ember).set_index("country")
    out = []
    for c, d in U.groupby("country"):
        wmw = float(d.p_nom_mw.sum())
        r = dict(country=c, existing_solar_mw=wmw, components=int(len(d)), **{f"cf_{k}": float((d[f"cf_{k}"] * d.p_nom_mw).sum() / wmw) for k in ("class0", "node_average", "best_class")})
        ok = c in em.index and bool(em.at[c, "usable"])
        r.update(ember_cf=(float(em.at[c, "cf_obs_median_main"]) if c in em.index else np.nan), ember_usable=ok, weight_mw=(wmw if ok else 0.0))
        out.append(r)
    T = pd.DataFrame(out)
    use = T[T.ember_usable]
    E = {k: float((use.weight_mw * (use[f"cf_{k}"] - use.ember_cf).abs()).sum() / use.weight_mw.sum()) for k in ("node_average", "best_class", "class0")}
    choice = "node_average" if (E["node_average"] <= E["best_class"] or abs(E["node_average"] - E["best_class"]) < TIE) else "best_class"
    T["abs_err_node_average"] = (T.cf_node_average - T.ember_cf).abs(); T["abs_err_best_class"] = (T.cf_best_class - T.ember_cf).abs(); T["abs_err_class0"] = (T.cf_class0 - T.ember_cf).abs()
    T.to_csv(a.output, index=False, lineterminator="\n")
    U.to_csv(a.output.with_name(a.output.stem + "_COMPONENTS.csv"), index=False, lineterminator="\n")
    ev = dict(script="scripts_project/v5_q12_solar_choice.py", rule="X20_SPEC_ADDENDUM_246.md section 3", network=str(a.network),
              network_sha256=hashlib.sha256(a.network.read_bytes()).hexdigest(), ember=str(a.ember), ember_sha256=hashlib.sha256(a.ember.read_bytes()).hexdigest(),
              E=E, choice=choice, tie_threshold=TIE, countries_used=sorted(use.country), weight_mw_total=float(use.weight_mw.sum()))
    a.output.with_suffix(".json").write_text(json.dumps(ev, indent=1) + "\n")
    pd.set_option("display.width", 250)
    print(T.round(4).to_string(index=False)); print(json.dumps({k: (round(v, 6) if isinstance(v, float) else v) for k, v in ev.items() if k in ("E", "choice", "countries_used")}, default=str))


if __name__ == "__main__":
    main()
