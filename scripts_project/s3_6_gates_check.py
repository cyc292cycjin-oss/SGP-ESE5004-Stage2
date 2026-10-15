"""S3-6: run the static (solver-free) V5 group-B gates on built networks: B11 (supply routes incl. the S3 pools), B12 (switches/hashes incl.
overrides), B13 (imports one-way), B14 (terminal caps), B15 (production caps registered), B16 (import prices identical across scenarios),
plus the B1 scope part (import carriers zero CO2, S3 fuel ports). Writes a JSON next to --output.

    python scripts_project/s3_6_gates_check.py --integrated <nc> --disconnected <nc> [--sensitivity <nc>] --output <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pypsa

from phase4_static import config
from v5.v5_gates import (gate_b11_supply_routes, gate_b12_hash, gate_b13_imports_one_way, gate_b14_terminal_caps, gate_b15_domestic_production_caps, gate_b16_import_prices_identical, IMPORT_CARRIERS)


def b1_scope(n):
    imp = [c for c in IMPORT_CARRIERS if c in n.carriers.index]
    L = n.links
    cols = [c for c in L if c.startswith("bus") and c[3:].isdigit() and c != "bus0"]
    port_carriers = sorted(set(L.carrier[L[cols].apply(lambda col: col.astype(str).str.startswith("co2 atmosphere")).any(axis=1)]))
    return dict(import_carriers_zero_co2=bool((n.carriers.loc[imp, "co2_emissions"].fillna(0.0) == 0).all()) if imp else True, import_carriers=imp, atmosphere_port_carriers=port_carriers,
                fuel_carbon_mode=n.meta.get("research_fuel_carbon", {}).get("mode"))


def main():
    p = argparse.ArgumentParser(); p.add_argument("--repo", type=Path, default=HERE.parent); p.add_argument("--integrated", type=Path, required=True); p.add_argument("--disconnected", type=Path, required=True)
    p.add_argument("--sensitivity", type=Path, default=None); p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    nets = {"integrated": pypsa.Network(str(a.integrated)), "disconnected": pypsa.Network(str(a.disconnected))}
    if a.sensitivity:
        nets["sensitivity"] = pypsa.Network(str(a.sensitivity))
    out = {}
    for label, n in nets.items():
        sc = n.meta.get("scenario", "integrated"); cfg = config(a.repo, sc)
        g = dict(B1_scope=b1_scope(n), B11=gate_b11_supply_routes(n, cfg), B12=gate_b12_hash(n, cfg), B13=gate_b13_imports_one_way(n), B14=gate_b14_terminal_caps(n), B15=gate_b15_domestic_production_caps(n))
        g["all_passed"] = all(v["passed"] for k, v in g.items() if isinstance(v, dict) and "passed" in v)
        out[label] = g
    out["B16"] = gate_b16_import_prices_identical(nets["integrated"], nets["disconnected"])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=1, default=str))
    for label, g in out.items():
        if label == "B16":
            print("B16", g["passed"], {k: v["identical"] for k, v in g["carriers"].items()}, "s3 config identical", g["s3_config_identical"])
        else:
            print(label, {k: (v["passed"] if isinstance(v, dict) and "passed" in v else v) for k, v in g.items() if k != "B1_scope"}, "| B1 scope:", g["B1_scope"]["import_carriers_zero_co2"], g["B1_scope"]["fuel_carbon_mode"])
            for r in g["B11"]["rows"]:
                if r["count_short"]:
                    print("   B11 short:", r["carrier"], r["buses_with_fewer_than_min_routes"][:5])
            print("   B12 checks:", g["B12"]["checks"], "| B13:", g["B13"]["checks"], "| B14 terminals:", len(g["B14"]["terminals"]), "| B15 gens:", g["B15"]["generators"])


if __name__ == "__main__":
    main()
