"""S4G-1 data (decision 98): electrical parameters of the 19 cross-border AC lines whose s_nom the author's readjust_existing_interconnections set
to the AIMS 2024 totals (S4F AUTHOR_READJUST_LINES_S4F2.csv) made consistent with their capacity through the line-type relation.

Source relation (checked line by line below):
  * PyPSA-Earth scripts/base_network.py _set_lines_s_nom_from_linetypes (lines 680-701): s_nom = sqrt3 x i_nom(type) x v_nom x num_parallel (AC);
    scripts/simplify_network.py lines 179-181 (conversion to the 380 kV type): num_parallel = s_nom / (sqrt3 x v_nom x i_nom) - the inverse used here.
    The same file is in pypsa-asean (identical SHA256).
  * PyPSA 0.30.3 pypsa/pf.py apply_line_types (lines 862-901), called by calculate_dependent_values (line 1007) at every optimisation
    (pypsa/optimization/abstract.py line 315, constraints.py line 624): for lines with a type x = x_per_length x length / num_parallel,
    r = r_per_length x length / num_parallel, b = 2 pi 1e-9 f_nom c_per_length x length x num_parallel; then x_pu = x / v_nom^2, x_pu_eff = x_pu,
    and the Kirchhoff voltage law rows use 1e5 x x_pu_eff (constraints.py lines 651-652).
Rule (decision 98): num_parallel = s_nom / (sqrt3 x v_nom(bus0) x i_nom(type)); x, r, b by the PyPSA line-type formulas; s_nom, s_nom_min, length,
cost unchanged; line 91 uses the S4F-corrected 80 MW (TH_MY_STOCK_S4F2.csv). Applied at build time (s4g_layers.apply_readjust_impedance).

    python scripts_project/s4g_1_data.py
"""
from __future__ import annotations

import logging
import math
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv

SCRIPT = "scripts_project/s4g_1_data.py"
INSTRUCTION_SHA = "2fd959e9134804a51aecc68b252b2ebe966813e65ed7dabd945ad3953a0d915c"
LOC = "work/p1_step4g_20261017/S4G_CLAUDE_CODE_INSTRUCTION.md"
C = ROOT / "research_inputs/corridors"
BASE = ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
PYPSA = Path("/home/jin/miniforge3/envs/pypsa-earth/lib/python3.11/site-packages/pypsa")
OUT = C / "READJUST_IMPEDANCE_S4G1.csv"


def check_line(path: Path, lineno: int, text: str) -> str:
    line = path.read_text().splitlines()[lineno - 1]
    if text not in line:
        raise ValueError(f"{path} line {lineno} does not hold {text!r}: {line!r}")
    return line.strip()


def source_checks() -> dict:
    bn, sn = ROOT / "scripts/base_network.py", ROOT / "scripts/simplify_network.py"
    out = dict(base_network=dict(file="scripts/base_network.py", sha256=sha256(bn), function=check_line(bn, 680, "def _set_lines_s_nom_from_linetypes"),
                                 lines={"694": check_line(bn, 694, "np.sqrt(3)"), "695": check_line(bn, 695, 'n.lines["type"].map(n.line_types.i_nom)'),
                                        "696": check_line(bn, 696, 'n.lines.eval("v_nom * num_parallel")')}),
               simplify_network=dict(file="scripts/simplify_network.py", sha256=sha256(sn),
                                     lines={"181": check_line(sn, 181, 'n.lines["num_parallel"] = n.lines.eval("s_nom / (sqrt(3) * v_nom * i_nom)")')}))
    pf, ab, co = PYPSA / "pf.py", PYPSA / "optimization/abstract.py", PYPSA / "optimization/constraints.py"
    import pypsa
    out["pypsa"] = dict(version=pypsa.__version__, pf_sha256=sha256(pf),
                        apply_line_types=check_line(pf, 862, "def apply_line_types"),
                        x_r={"887": check_line(pf, 887, 'lines[attr + "_per_length"] * lines["length"] / lines["num_parallel"]')},
                        b={"894": check_line(pf, 894, 'lines["c_per_length"]'), "896": check_line(pf, 896, 'lines["num_parallel"]')},
                        calculate_dependent_values={"1002": check_line(pf, 1002, "def calculate_dependent_values"), "1007": check_line(pf, 1007, "apply_line_types(network)"),
                                                    "1015": check_line(pf, 1015, 'network.lines["x_pu"] = network.lines.x / (network.lines.v_nom**2)'),
                                                    "1019": check_line(pf, 1019, 'network.lines["x_pu_eff"] = network.lines["x_pu"]')},
                        optimisation={"abstract.py:315": check_line(ab, 315, "n.calculate_dependent_values()"), "constraints.py:624": check_line(co, 624, "n.calculate_dependent_values()"),
                                      "constraints.py:651": check_line(co, 651, "weightings = branches.x_pu_eff if carrier == \"AC\""),
                                      "constraints.py:652": check_line(co, 652, "C = 1e5 * sparse.diags(weightings.values) * sub.C")})
    if Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/scripts/base_network.py").exists():
        out["pypsa_asean_base_network_sha256"] = sha256(Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/scripts/base_network.py"))
    return out


def table() -> pd.DataFrame:
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(BASE)); lt = n.line_types
    audit = pd.read_csv(C / "AUTHOR_READJUST_LINES_S4F2.csv", dtype={"line": str})
    thmy = pd.read_csv(C / "TH_MY_STOCK_S4F2.csv", dtype={"component": str}).set_index("component")
    rows = []
    for _, a in audit.iterrows():
        k = a.line; z = n.lines.loc[k]; t = lt.loc[z.type]
        v = float(n.buses.at[z.bus0, "v_nom"]); s_used = float(thmy.at[k, "corrected_mw"]) if k in thmy.index else float(z.s_nom)
        npar = s_used / (math.sqrt(3) * v * float(t.i_nom))
        f = lambda np_: dict(x=float(t.x_per_length) * float(z.length) / np_, r=float(t.r_per_length) * float(z.length) / np_,
                             b=2 * math.pi * 1e-9 * float(t.f_nom) * float(t.c_per_length) * float(z.length) * np_)
        old, new = f(float(z.num_parallel)), f(npar)
        rows.append(dict(line=k, country_pair=a.country_pair, bus0=z.bus0, bus1=z.bus1, type=z.type, length_km=float(z.length), v_nom_kv=v, i_nom_ka=float(t.i_nom),
                         s_nom_frozen_mw=float(z.s_nom), s_nom_min_frozen_mw=float(z.s_nom_min), s_nom_used_mw=s_used, num_parallel_frozen=float(z.num_parallel),
                         num_parallel_s4g=npar, x_stored_frozen=float(z.x), r_stored_frozen=float(z.r), b_stored_frozen=float(z.b),
                         x_type_frozen=old["x"], r_type_frozen=old["r"], b_type_frozen=old["b"], x_s4g=new["x"], r_s4g=new["r"], b_s4g=new["b"],
                         x_factor=new["x"] / old["x"], rating_check_mw=math.sqrt(3) * v * float(t.i_nom) * npar))
    return pd.DataFrame(rows)


def main():
    src = source_checks(); T = table()
    if not (abs(T.rating_check_mw - T.s_nom_used_mw) < 1e-6).all():
        raise ValueError("line-type relation does not reproduce s_nom")
    write_csv(T.to_dict("records"), OUT, list(T.columns))
    import json
    (C / "READJUST_IMPEDANCE_S4G1.json").write_text(json.dumps(dict(sources=src, lines=len(T), base_sha256=sha256(BASE), audit_sha256=sha256(C / "AUTHOR_READJUST_LINES_S4F2.csv"),
                                                                   stored_x_equals_type_x_frozen=bool((abs(T.x_stored_frozen - T.x_type_frozen) / T.x_type_frozen < 1e-6).all()),
                                                                   stored_x_vs_type_x_max_rel=float((abs(T.x_stored_frozen - T.x_type_frozen) / T.x_type_frozen).max())), indent=1))
    reg = Registry(SCRIPT)
    reg.add("s4g1_line_type_relation", "Decision 98 source: PyPSA-Earth scripts/base_network.py _set_lines_s_nom_from_linetypes (lines 680-701) s_nom = sqrt3 x i_nom x v_nom x "
            "num_parallel; simplify_network.py line 181 num_parallel = s_nom / (sqrt3 x v_nom x i_nom); PyPSA 0.30.3 pf.apply_line_types (862-901): x = x_per_length x length / "
            "num_parallel, r likewise, b = 2 pi 1e-9 f_nom c_per_length length num_parallel, called by calculate_dependent_values at every optimisation (abstract.py 315); "
            "KVL rows use 1e5 x x_pu_eff (constraints.py 651-652)", "relation", "flag", "B", "PyPSA-Earth scripts/base_network.py, simplify_network.py; PyPSA 0.30.3 pf.py",
            "base_network.py 680-701; simplify_network.py 181; pf.py 862-901, 1002-1019", src["base_network"]["sha256"], decision_ref="98", status="REFERENCE_ONLY")
    reg.add("s4g1_readjust_impedance_table", f"Decision 98: {len(T)} author-readjusted cross-border AC lines - num_parallel = s_nom / (sqrt3 x v_nom x i_nom) (line 91 with the "
            "S4F 80 MW), x / r / b by the PyPSA line-type formulas; s_nom, s_nom_min, length, cost unchanged; applied at build time with the frozen values checked",
            "table", "flag", "B", "derived (scripts_project/s4g_1_data.py)", "research_inputs/corridors/READJUST_IMPEDANCE_S4G1.csv", sha256(OUT), decision_ref="98", status="REFERENCE_ONLY")
    reg.add("s4g1_readjust_impedance_switch", "Decision 98: research.network.readjust_impedance = pypsa_eur (main: READJUST_IMPEDANCE_S4G1.csv applied) | author (the "
            "author's parameters, comparison; default when absent). The cluster-member issue (members of a clustered cross-border line are not the physical "
            "interconnection, e.g. line 91) is not re-clustered: registered limitation, grade C", "pypsa_eur|author", "flag", "C", "S4G instruction S4G-1", LOC, INSTRUCTION_SHA,
            decision_ref="98", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4g_1.csv")
    pd.set_option("display.width", 250)
    print(T[["line", "country_pair", "s_nom_used_mw", "num_parallel_frozen", "num_parallel_s4g", "x_stored_frozen", "x_type_frozen", "x_s4g", "x_factor"]].round(4).to_string())


if __name__ == "__main__":
    main()
