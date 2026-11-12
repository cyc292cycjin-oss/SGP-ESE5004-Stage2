"""V5 X20, X21 sensitivity switch (decision 253): factors of research.demand.v5.onwind_reference_level = gwa_reference.

    python scripts_project/v5_onwind_reference_data.py --network <v5 main integrated_2920_3h_unsolved.nc> --cells <X03 cache/onwind_cells/onwind_node_cells.csv>

Per country (X20 ONWIND_SANITY rule, scripts x20_bridge.onwind_sanity):
  v5 = p_nom_max-weighted annual mean p_max_pu (snapshot weights) of the extendable onshore candidates ('onwind') of the network;
  reference = GWA IEC3 gross capacity factor (potential-weighted over the candidate cells, X03 onwind_node_cells.csv) / r,
  r = GWA gross / observed at the farm points: TH 1.07, VN 1.44, PH 1.52 (EXACT X03); the other 8 countries = farm-capacity-weighted r of the three
  (weights farm_capacity_onshore_mw of WIND_CALIBRATION_ALPHA_V5.csv, as the alpha of those countries);
  factor = 1 / (v5 / reference) = reference / v5. Also listed: candidate potential (MW) and whether the decision-252 threshold (>= 1 GW) applies.
Writes research_inputs/renewable_v5/ONWIND_REFERENCE_LEVEL_FACTORS_V5.csv. The main set does not read it (switch disabled).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/renewable_v5/ONWIND_REFERENCE_LEVEL_FACTORS_V5.csv"
ALPHA = ROOT / "research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA_V5.csv"
R_FARM = dict(TH=1.07, VN=1.44, PH=1.52)
COUNTRIES = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def factors(n, cells: pd.DataFrame, alpha: pd.DataFrame) -> pd.DataFrame:
    wcap = alpha.loc[list(R_FARM), "farm_capacity_onshore_mw"].astype(float)
    r_other = float(sum(R_FARM[c] * wcap[c] for c in R_FARM) / wcap.sum())
    gwa = {c: float((d.gwa_cf_iec3 * d.w_mw).sum() / d.w_mw.sum()) for c, d in cells.groupby("country")}
    g = n.generators; cty = g.bus.map(n.buses.country)
    w = n.snapshot_weightings.generators; P = n.generators_t.p_max_pu
    rows = []
    for c in COUNTRIES:
        idx = [x for x in g.index[(g.carrier == "onwind") & g.p_nom_extendable & (cty == c)] if x in P.columns]
        cap = g.loc[idx, "p_nom_max"].replace(np.inf, np.nan).fillna(0.0)
        cf = (P[idx].mul(w, axis=0).sum() / w.sum()) if idx else pd.Series(dtype=float)
        v5 = float((cf * cap).sum() / cap.sum()) if cap.sum() > 0 else np.nan
        r = R_FARM.get(c, r_other); ref = gwa.get(c, np.nan) / r
        rows.append(dict(country=c, candidates=len(idx), potential_mw=float(cap.sum()), threshold_applies=bool(cap.sum() >= 1000.0), cf_v5=v5,
                         gwa_iec3_gross=gwa.get(c, np.nan), r=r, r_basis=("farm points" if c in R_FARM else "capacity-weighted TH/VN/PH"), reference=ref,
                         v5_over_reference=v5 / ref if ref else np.nan, factor=ref / v5 if v5 else np.nan))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--cells", type=Path, required=True); a = ap.parse_args()
    import pypsa
    n = pypsa.Network(str(a.network))
    variant = (n.meta.get("research_renewable") or {}).get("profile_variant")
    t = factors(n, pd.read_csv(a.cells), pd.read_csv(ALPHA).set_index("country"))
    t.insert(1, "profile_variant", variant)
    t["source_network_sha256"] = sha256(a.network); t["cells_sha256"] = sha256(a.cells); t["alpha_table_sha256"] = sha256(ALPHA)
    t.to_csv(OUT, index=False, lineterminator="\n")
    print(json.dumps(dict(variant=variant, out=str(OUT)), default=str)); print(t[["country", "potential_mw", "cf_v5", "reference", "v5_over_reference", "factor", "threshold_applies"]].to_string())


if __name__ == "__main__":
    main()
