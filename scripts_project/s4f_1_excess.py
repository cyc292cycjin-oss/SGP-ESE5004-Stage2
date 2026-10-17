"""S4F-1 (decision 96) report table: lines / DC links of the S4E-3 smoke solutions (56 x 3h, read only) whose extension exceeds the PyPSA-Eur individual
limit (registry pypsa_eur_lines_max_extension, increment over the existing capacity s_nom / p_nom).

    python scripts_project/s4f_1_excess.py --solves results_project/s4e/s4e3/solves --out results_project/s4f/s4f1
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR

RUNS = {"integrated": "integrated", "disconnected": "disconnected", "integrated_nze": "integrated"}


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--solves", type=Path, required=True); ap.add_argument("--out", type=Path, required=True); a = ap.parse_args()
    cap = float(pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id").at["pypsa_eur_lines_max_extension", "value"])
    a.out.mkdir(parents=True, exist_ok=True); rows, summ = [], {}
    for tag, sc in RUNS.items():
        n = pypsa.Network(str(a.solves / tag / f"{sc}_SMOKE_TEST_ONLY_solved.nc"))
        L = n.lines.assign(component_type="Line", existing=n.lines.s_nom, opt=n.lines.s_nom_opt)
        dc = n.links[n.links.carrier == "DC"]
        D = dc.assign(component_type="Link", existing=dc.p_nom, opt=dc.p_nom_opt)
        A = pd.concat([L[["component_type", "bus0", "bus1", "border_class", "existing", "opt"]], D[["component_type", "bus0", "bus1", "border_class", "existing", "opt"]]])
        A["added"] = A.opt - A.existing; A["country0"] = A.bus0.map(n.buses.country); A["country1"] = A.bus1.map(n.buses.country)
        A["cap_s4f1"] = A.existing + cap; A["excess"] = (A.added - cap).clip(lower=0.0)
        over = A[A.excess > 0].sort_values("excess", ascending=False)
        for k, z in over.iterrows():
            rows.append(dict(run=tag, component_type=z.component_type, component=k, bus0=z.bus0, bus1=z.bus1, country0=z.country0, country1=z.country1, border_class=z.border_class,
                             existing_mw=round(float(z.existing), 3), optimal_mw=round(float(z.opt), 3), added_mw=round(float(z.added), 3), cap_mw=round(float(z.cap_s4f1), 3),
                             excess_mw=round(float(z.excess), 3)))
        summ[tag] = dict(components=int(len(A)), added_total_gw=float(A.added.sum() / 1e3), over_cap=int(len(over)), excess_total_gw=float(over.excess.sum() / 1e3),
                         over_cap_cross_border=int((over.border_class == "cross_border").sum()), over_cap_domestic=int((over.border_class == "domestic").sum()),
                         max_added_gw=float(A.added.max() / 1e3))
    pd.DataFrame(rows).to_csv(a.out / "MAX_EXTENSION_EXCESS_S4E3.csv", index=False)
    (a.out / "MAX_EXTENSION_EXCESS_S4E3.json").write_text(json.dumps(dict(cap_mw=cap, basis="added = s_nom_opt - s_nom (lines), p_nom_opt - p_nom (DC links); S4E-3 smoke, 56 x 3h", runs=summ), indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
