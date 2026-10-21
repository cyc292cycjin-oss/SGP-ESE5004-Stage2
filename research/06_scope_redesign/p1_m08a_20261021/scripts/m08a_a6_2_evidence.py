"""M08a A6.2 evidence (no solve): offshore wind potentials under the PyPSA-Eur v2025.07.0 area rules vs the author (as-built) potentials,
the author-rule re-computation (method validation) and the size of the shipping-lane exclusion.

Inputs: research_inputs/renewable_v5/offshore_m08a (scripts_project/m08a_offshore_profiles.py, rules pypsa_eur_v2025_07), the work folder of
the same script with --rules author and --rules pypsa_eur_v2025_07_no_ship_lanes (--no-profiles), and the S4M-3 integrated build (as-built
offwind-ac / -dc p_nom_max of the screening networks).

    python m08a_a6_2_evidence.py --repo /home/jin/wt_m08a_20261021 --work /home/jin/m08a_offshore_work \
        --built /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds/integrated/integrated_2920_3h_unsolved.nc --out <work dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--built", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    import pypsa
    d = a.repo / "research_inputs/renewable_v5/offshore_m08a"
    log = json.loads((d / "OFFSHORE_PROFILES_LOG_pypsa_eur_v2025_07.json").read_text())
    cls = pd.read_csv(d / "OFFSHORE_CLASSES_pypsa_eur_v2025_07.csv")
    aut = json.loads((a.work / "author_validation/OFFSHORE_PROFILES_LOG_author.json").read_text())
    autv = json.loads((a.work / "author_validation/AUTHOR_VALIDATION_SUMMARY.json").read_text())
    nos = json.loads((a.work / "no_ship_lanes/OFFSHORE_PROFILES_LOG_pypsa_eur_v2025_07_no_ship_lanes.json").read_text())
    n = pypsa.Network(str(a.built))
    g = n.generators[n.generators.carrier.isin(["offwind-ac", "offwind-dc"]) & n.generators.p_nom_extendable]
    built = g.groupby([g.carrier, g.bus.map(n.buses.country)]).p_nom_max.sum().div(1e3)
    rows = []
    countries = sorted(set(cls.country))
    for c in countries:
        r = dict(country=c)
        for t in ("offwind-ac", "offwind-dc"):
            r[f"{t}_as_built_gw"] = round(float(built.get((t, c), 0.0)), 3)
            r[f"{t}_author_recalc_gw"] = round(aut["potential_mw_by_country"][t].get(c, 0.0) / 1e3, 3)
        for t in ("offwind-ac", "offwind-dc", "offwind-float"):
            r[f"{t}_new_gw"] = round(log["potential_mw_by_country"][t].get(c, 0.0) / 1e3, 3)
            r[f"{t}_ship_lane_excluded_mw"] = round(nos["potential_mw_by_country"][t].get(c, 0.0) - log["potential_mw_by_country"][t].get(c, 0.0), 1)
        rows.append(r)
    T = pd.DataFrame(rows)
    tot = T.drop(columns="country").sum().round(3).to_dict()
    c3 = cls[cls.classes == 3]
    w = c3.assign(pw=c3.potential_mw * c3.cf_annual_weighted, dw=c3.potential_mw * c3.average_distance_km).groupby("tech")[["pw", "dw", "potential_mw"]].sum()
    ev = dict(schema="m08a-a6-2-offshore-v1", solver_runs=0, rules=log["rule_values"], sources_pypsa_eur=log["sources_pypsa_eur"], area_crs=log["area_crs"],
              inputs=log["inputs"], ship_raster=log["ship_raster"], timings_s=log["timings"], outputs=log["outputs"],
              totals_gw=tot, by_country=rows,
              classes=dict(rows=int(len(c3)), generators_with_potential=c3[c3.potential_mw > 0].groupby("tech").size().to_dict(), nodes=c3.groupby("tech").node.nunique().to_dict(),
                           cf_potential_weighted=(w.pw / w.potential_mw).round(4).to_dict(), distance_potential_weighted_km=(w.dw / w.potential_mw).round(2).to_dict(),
                           distance_km_range={t: [round(float(x.average_distance_km.min()), 2), round(float(x.average_distance_km.max()), 2)] for t, x in c3.groupby("tech")},
                           partition_c1_vs_c3_max_rel=float((cls[cls.classes == 1].groupby(["tech", "node"]).potential_mw.sum() /
                                                             c3.groupby(["tech", "node"]).potential_mw.sum() - 1).abs().max())),
              author_rule_validation=dict(summary=autv, method="--rules author (Copernicus [80, 200], natura, depth <= 50 m, shore 30 km, 2 / 3 MW/km2, no ship lanes) vs the author potential "
                                                       "(s4a_profiles.author_potential, as split by S4A coverage weights) and the as-built p_nom_max",
                                          as_built_total_gw={t: round(float(built.xs(t).sum()), 3) for t in ("offwind-ac", "offwind-dc")}),
              ship_lanes=dict(threshold_ais_positions_per_cell=400 * 8760 * 6, rule="determine_availability_matrix.py 126-133: exclude density > ship_threshold x 8760 x 6",
                              excluded_mw={t: round(sum(nos["potential_mw_by_country"][t].values()) - sum(log["potential_mw_by_country"][t].values()), 1) for t in log["potential_mw_by_country"]},
                              samples_ais_positions=dict(singapore_strait=16688911, malacca_strait=1361049, south_china_sea_lane_max_10px=10736776),
                              note="the PyPSA-Eur threshold (21.0 M positions per 0.005 deg cell, ~400 per hour over 6 years) is above the densest ASEAN lanes; cells above it lie "
                                   "mostly in the East China Sea (13.1-29.4 N); effect in the ASEAN EEZ 57 MW"),
              built_network=dict(path=str(a.built), sha256=sha(a.built)))
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "evidence/M08A_A6_2_OFFSHORE.json").write_text(json.dumps(ev, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    T.to_csv(a.out / "evidence/M08A_A6_2_OFFSHORE_BY_COUNTRY.csv", index=False)
    print(json.dumps(dict(totals_gw=tot, ship=ev["ship_lanes"]["excluded_mw"], cf=ev["classes"]["cf_potential_weighted"]), indent=1))


if __name__ == "__main__":
    main()
