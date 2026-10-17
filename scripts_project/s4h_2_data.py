"""S4H-2 data (decision 101): reference reactance of the AC candidates.

  a. research.corridors.candidate_num_parallel = one_circuit (main) | template43: registry entries with the source notes (PyPSA-Eur v2025.07.0 has no
     zero-capacity AC candidate lines in its default configuration; PyPSA-Earth augmented_line_connections - the rule is off by default - adds AC lines
     without num_parallel, i.e. the PyPSA default 1, or HVDC links; checked against the in-repo copies).
  b. READJUST_IMPEDANCE_S4H2.csv = READJUST_IMPEDANCE_S4G1.csv (19 rows, unchanged) + APG17_LA_MM: num_parallel = 30 / (sqrt3 x v_nom x i_nom), x / r / b
     by the line type; the 'frozen' values are those of the line as added by s2_layers.add_apg_corridor_lines (template line 43), read from the S4H-1 build.
  c. CANDIDATE_COMPLETENESS_S4H2.csv: every country pair with a cross-border line / DC link or land-adjacent by decision 94 (ADJACENCY_S4E1.csv): stock
     and candidate lines / DC links. A country pair with AC stock and no zero-capacity AC candidate gets one candidate at every adjacent node pair of
     ADJACENCY_S4E1.csv (decision 94 / S4E-1 rule 1 applied to the pairs it skipped as 'existing corridor'; type, length, subsea share and cost as
     S4E-1 rule 5: same landmass -> AC line, else DC link). CORRIDORS_S4H2.csv = CORRIDORS_S4F2.csv + these rows; SUBSEA_SHARE_S4H2.csv =
     SUBSEA_SHARE_S4F2.csv with the new components listed at their node pairs (the shares are recomputed and must equal the table).
     A country pair with AC stock and no adjacent node pair stops the script (S4H stop condition).

    python scripts_project/s4h_2_data.py --network <S4H-1 integrated build>
    python scripts_project/s4h_2_data.py --length-shares <S4H-2 integrated build with corridors.optional_sg_vn_kh=on>
    python scripts_project/s4h_2_data.py --registry
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import numpy as np
import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s4f_2_corridors import corridor_row, geometry_tools

SCRIPT = "scripts_project/s4h_2_data.py"
INSTRUCTION_SHA = "a029bd64cef2ae1b84aec4ebc186ede21630283d17153df9aed4ae32d1fd33bd"
LOC = "work/p1_step4h_20261017/S4H_CLAUDE_CODE_INSTRUCTION.md"
C = ROOT / "research_inputs/corridors"
APG17 = "APG17_LA_MM"
EUR_CONF = REG_DIR / "sources" / "pypsa_eur_v2025.07.0_config.default.yaml"
EARTH_AUG = ROOT / "scripts/augmented_line_connections.py"
EARTH_CONF = ROOT / "config.default.yaml"
STATUS = ("S4H2_REFERENCE_CANDIDATE (decision 101 c): country pair with AC stock and no zero-capacity AC candidate; decision-94 adjacency rule at the "
          "adjacent node pair; capacity 0, extendable")
SOURCE = "S4H-2 (scripts_project/s4h_2_data.py): great-circle x 1.25; subsea share S4C supplement 01 rule; type by landmass (S4E-1 rule 5)"


def _line(path: Path, no: int, text: str) -> dict:
    got = path.read_text().splitlines()[no - 1]
    if text not in got:
        raise ValueError(f"{path.name} line {no} changed: {got.strip()}")
    return dict(file=str(path.relative_to(ROOT)), line=no, text=got.strip(), sha256=sha256(path))


def source_checks() -> dict:
    import pypsa
    attrs = pd.read_csv(Path(pypsa.__file__).parent / "component_attrs" / "lines.csv", index_col=0)
    return dict(pypsa_eur_under_construction=_line(EUR_CONF, 327, "under_construction: keep # 'zero': set capacity to zero"),
                pypsa_earth_rule_off=_line(EARTH_CONF, 174, "add_to_snakefile: false"),
                pypsa_earth_new_line_type=_line(EARTH_CONF, 177, 'new_line_type: ["HVAC"]'),
                pypsa_earth_min_expansion=_line(EARTH_CONF, 178, "min_expansion: 1"),
                pypsa_earth_script_fallback=_line(EARTH_AUG, 93, 'line_type_option = options.get("new_line_type", ["HVDC"])'),
                pypsa_earth_hvdc_links=_line(EARTH_AUG, 187, '"Link"'), pypsa_earth_hvac_lines=_line(EARTH_AUG, 206, '"Line"'),
                pypsa_earth_hvac_no_num_parallel=dict(num_parallel_in_script="num_parallel" in EARTH_AUG.read_text()),
                pypsa_default_num_parallel=dict(version=pypsa.__version__, default=str(attrs.at["num_parallel", "default"])))


def _xb(n):
    c = n.buses.country
    L = n.lines.assign(c0=c.reindex(n.lines.bus0).to_numpy(), c1=c.reindex(n.lines.bus1).to_numpy())
    K = n.links[n.links.carrier == "DC"]; K = K.assign(c0=c.reindex(K.bus0).to_numpy(), c1=c.reindex(K.bus1).to_numpy())
    return L[L.c0 != L.c1], K[K.c0 != K.c1]


def completeness(n, adj: pd.DataFrame, added: dict | None = None) -> pd.DataFrame:
    L, K = _xb(n); key = lambda a, b: "-".join(sorted((str(a), str(b))))
    pairs = sorted(set(key(a, b) for a, b in zip(L.c0, L.c1)) | set(key(a, b) for a, b in zip(K.c0, K.c1)) |
                   set(key(a, b) for a, b in zip(adj[adj.adjacent].country_a, adj[adj.adjacent].country_b)))
    rows = []
    for p in pairs:
        l = L[[key(a, b) == p for a, b in zip(L.c0, L.c1)]]; k = K[[key(a, b) == p for a, b in zip(K.c0, K.c1)]]
        a_ = adj[adj.adjacent & np.array([key(a, b) == p for a, b in zip(adj.country_a, adj.country_b)], dtype=bool)]
        ac_stock = l[l.s_nom_min > 0]; ac_cand = l[(l.s_nom == 0) & (l.s_nom_min == 0) & l.s_nom_extendable]
        dc_stock = k[k.p_nom_min > 0]; dc_cand = k[(k.p_nom == 0) & (k.p_nom_min == 0) & k.p_nom_extendable]
        rows.append(dict(country_pair=p, land_adjacent_node_pairs=len(a_), adjacent_node_pairs=";".join(f"{x} | {y}" for x, y in zip(a_.node_a, a_.node_b)),
                         ac_stock_lines=";".join(map(str, ac_stock.index)), ac_stock_mw=float(ac_stock.s_nom.sum()), ac_candidates=len(ac_cand),
                         ac_candidate_lines=";".join(map(str, ac_cand.index)), dc_stock_links=";".join(map(str, dc_stock.index)), dc_stock_mw=float(dc_stock.p_nom.sum()),
                         dc_candidates=len(dc_cand), dc_candidate_links=";".join(map(str, dc_cand.index)),
                         needs_reference_candidate=bool(len(ac_stock) and not len(ac_cand)), added=";".join((added or {}).get(p, []))))
    return pd.DataFrame(rows)


def readjust_row(n) -> dict:
    z = n.lines.loc[APG17]; t = n.line_types.loc[z.type]; v = float(n.buses.at[z.bus0, "v_nom"]); s = float(z.s_nom)
    if abs(s - 30.0) > 1e-9 or abs(float(z.s_nom_min) - 30.0) > 1e-9:
        raise ValueError(f"{APG17}: s_nom {s} is not the APG #17 stock 30 MW")
    npar = s / (math.sqrt(3) * v * float(t.i_nom))
    f = lambda np_: dict(x=float(t.x_per_length) * float(z.length) / np_, r=float(t.r_per_length) * float(z.length) / np_,
                         b=2 * math.pi * 1e-9 * float(t.f_nom) * float(t.c_per_length) * float(z.length) * np_)
    old, new = f(float(z.num_parallel)), f(npar)
    return dict(line=APG17, country_pair="LA-MM", bus0=z.bus0, bus1=z.bus1, type=z.type, length_km=float(z.length), v_nom_kv=v, i_nom_ka=float(t.i_nom),
                s_nom_frozen_mw=s, s_nom_min_frozen_mw=float(z.s_nom_min), s_nom_used_mw=s, num_parallel_frozen=float(z.num_parallel), num_parallel_s4g=npar,
                x_stored_frozen=float(z.x), r_stored_frozen=float(z.r), b_stored_frozen=float(z.b), x_type_frozen=old["x"], r_type_frozen=old["r"], b_type_frozen=old["b"],
                x_s4g=new["x"], r_s4g=new["r"], b_s4g=new["b"], x_factor=new["x"] / old["x"], rating_check_mw=math.sqrt(3) * v * float(t.i_nom) * npar)


def main_tables(network: Path):
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(network)); b = n.buses; tools = geometry_tools()
    adj = pd.read_csv(C / "ADJACENCY_S4E1.csv")
    cor = pd.read_csv(C / "CORRIDORS_S4F2.csv", float_precision="round_trip"); sub = pd.read_csv(C / "SUBSEA_SHARE_S4F2.csv", float_precision="round_trip")
    T0 = completeness(n, adj)
    new_rows, added, checks = [], {}, []
    for _, r in T0[T0.needs_reference_candidate].iterrows():
        a_ = adj[adj.adjacent & np.array(["-".join(sorted((x, y))) == r.country_pair for x, y in zip(adj.country_a, adj.country_b)], dtype=bool)]
        if a_.empty:
            raise SystemExit(f"S4H STOP: country pair {r.country_pair} has AC stock but no adjacent node pair - endpoints cannot be determined")
        for _, e in a_.iterrows():
            p, q = sorted((str(e.node_a), str(e.node_b)))
            row, geo = corridor_row(b, p, q, tools, f"S4H2 {p} - {q}", STATUS, sub.columns)
            row["source"] = SOURCE
            if row["component"] in n.lines.index or row["component"] in n.links.index or (cor.component.astype(str) == row["component"]).any():
                raise ValueError(f"{row['component']} exists already")
            s = sub[(sub.loc0 == p) & (sub.loc1 == q)]
            if len(s) != 1:
                raise SystemExit(f"S4H STOP: node pair {p} - {q} not unique in SUBSEA_SHARE_S4F2.csv ({len(s)} rows)")
            s = s.iloc[0]
            ok = abs(float(s.share_landmass_nonland) - float(row["subsea_share"])) < 1e-12 and bool(s.same_landmass) == bool(geo["same_landmass"])
            checks.append(dict(component=row["component"], country_pair=r.country_pair, type=row["component_type"], length_km=row["length_km"], subsea_share=row["subsea_share"],
                               table_share=float(s.share_landmass_nonland), same_landmass=bool(geo["same_landmass"]), existing_at_pair=str(e.existing_components), consistent=ok))
            if not ok:
                raise ValueError(f"{row['component']}: subsea share / landmass differs from SUBSEA_SHARE_S4F2.csv")
            new_rows.append(row); added.setdefault(r.country_pair, []).append(row["component"])
    C2 = pd.concat([cor, pd.DataFrame(new_rows)[cor.columns]], ignore_index=True)
    S2 = sub.copy()
    for row in new_rows:
        p, q = sorted((row["from"], row["to"])); i = S2.index[(S2.loc0 == p) & (S2.loc1 == q)][0]
        tag = f"{row['component_type']}:{row['carrier']}"
        comps = [x for x in str(S2.at[i, "components"]).split(";") if x and x != "nan"]
        S2.at[i, "components"] = ";".join(sorted(set(comps) | {tag})); S2.at[i, "n_components"] = int(S2.at[i, "n_components"]) + 1
        S2.at[i, "names"] = ";".join(sorted([x for x in str(S2.at[i, "names"]).split(";") if x and x != "nan"] + [row["component"]]))[:400]
    T = completeness(n, adj, added)
    g1 = pd.read_csv(C / "READJUST_IMPEDANCE_S4G1.csv", dtype={"line": str}, float_precision="round_trip")
    if APG17 in set(g1.line) or len(g1) != 19:
        raise ValueError("READJUST_IMPEDANCE_S4G1.csv is not the 19-row S4G table")
    ra = readjust_row(n)
    if abs(ra["rating_check_mw"] - 30.0) > 1e-6:
        raise ValueError("line-type relation does not reproduce 30 MW")
    R = pd.concat([g1, pd.DataFrame([ra])[g1.columns]], ignore_index=True)
    C2.to_csv(C / "CORRIDORS_S4H2.csv", index=False); S2.to_csv(C / "SUBSEA_SHARE_S4H2.csv", index=False)
    write_csv(T.to_dict("records"), C / "CANDIDATE_COMPLETENESS_S4H2.csv", list(T.columns))
    write_csv(R.to_dict("records"), C / "READJUST_IMPEDANCE_S4H2.csv", list(R.columns))
    src = source_checks()
    summ = dict(network=str(network), completeness_rule="country pair with AC stock and no zero-capacity AC candidate -> one candidate at every adjacent node pair of ADJACENCY_S4E1.csv",
                pairs=len(T), pairs_needing=T0[T0.needs_reference_candidate].country_pair.tolist(), added=added, new_components=checks,
                n_ac=sum(1 for x in new_rows if x["component_type"] == "Line"), n_dc=sum(1 for x in new_rows if x["component_type"] == "Link"),
                apg17=ra, sources=src, inputs=dict(corridors_s4f2=sha256(C / "CORRIDORS_S4F2.csv"), subsea_s4f2=sha256(C / "SUBSEA_SHARE_S4F2.csv"),
                                                   adjacency_s4e1=sha256(C / "ADJACENCY_S4E1.csv"), readjust_s4g1=sha256(C / "READJUST_IMPEDANCE_S4G1.csv")))
    (C / "CORRIDORS_S4H2.json").write_text(json.dumps(summ, indent=1, default=str))
    write_registry()
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
    print(T[["country_pair", "land_adjacent_node_pairs", "ac_stock_lines", "ac_stock_mw", "ac_candidates", "dc_stock_links", "dc_candidates", "needs_reference_candidate", "added"]].to_string())
    print(pd.DataFrame(checks).to_string())
    print(json.dumps({k: ra[k] for k in ("num_parallel_frozen", "num_parallel_s4g", "x_stored_frozen", "x_s4g", "x_factor")}, indent=1))


def write_registry():
    js = json.loads((C / "CORRIDORS_S4H2.json").read_text()); src = js["sources"]; ra = js["apg17"]
    reg = Registry(SCRIPT)
    reg.add("s4h2_candidate_num_parallel_switch", "Decision 101 a: research.corridors.candidate_num_parallel = one_circuit (main: every zero-capacity AC candidate line - "
            "S4E-1 adjacency candidates, APG11, the four LA-VN lines of S4H-1, the S4H-2 reference candidates - gets num_parallel = 1 of 'Al/St 240/40 4-bundle 380.0', "
            "x / r / b by the PyPSA line-type formulas, read back after the build) | template43 (the former convention: num_parallel 1.286 of template line 43, "
            "comparison). Model convention: PyPSA-Eur has no zero-capacity AC candidate lines (default lines.under_construction = keep; the only zero-capacity "
            "AC lines are under-construction lines with the option 'zero'); AC rather than DC because 380 kV interconnections on one landmass are subject to "
            "Kirchhoff's voltage law", "one_circuit|template43", "flag", "B", "S4H instruction S4H-2 a", LOC, INSTRUCTION_SHA, decision_ref="101", status="REFERENCE_ONLY")
    e = src["pypsa_eur_under_construction"]; a = src["pypsa_earth_new_line_type"]
    reg.add("s4h2_candidate_convention_sources", "Decision 101 a sources (checked against the in-repo copies): PyPSA-Eur v2025.07.0 config.default.yaml line 327 "
            f"'{e['text'][:80]}'; PyPSA-Earth augmented_line_connections (config.default.yaml line 174 add_to_snakefile: false - off by default; line 177 "
            f"new_line_type ['HVAC'], script fallback ['HVDC'] at line 93) adds k-edge AC lines (line 206, s_nom_min = min_expansion 1 MW, num_parallel not set -> "
            f"PyPSA {src['pypsa_default_num_parallel']['version']} default {src['pypsa_default_num_parallel']['default']}) and/or HVDC links for long intra-country "
            "edges (line 187). The instruction's note 'PyPSA-Earth augmented connection = DC links' holds only for the script fallback; the default "
            "configuration adds AC lines with one circuit, consistent with one_circuit", "reference", "flag", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml; PyPSA-Earth scripts/augmented_line_connections.py, config.default.yaml",
            "config.default.yaml 327 (PyPSA-Eur); augmented_line_connections.py 93, 187, 206; config.default.yaml 174-178 (PyPSA-Earth)",
            src["pypsa_earth_hvac_lines"]["sha256"], decision_ref="101", status="REFERENCE_ONLY")
    reg.add("s4h2_apg17_readjust", f"Decision 101 b: APG17_LA_MM (APG AIMS III #17, 30 MW stock) num_parallel {ra['num_parallel_frozen']:.6f} (template line 43) -> 30 / (sqrt3 x "
            f"{ra['v_nom_kv']:.0f} kV x {ra['i_nom_ka']} kA) = {ra['num_parallel_s4g']:.6f}; x {ra['x_stored_frozen']:.3f} -> {ra['x_s4g']:.1f} ohm (decision-98 relation); "
            "inside research.network.readjust_impedance = pypsa_eur (author restores the template values)", ra["num_parallel_s4g"], "circuits", "B",
            "derived (scripts_project/s4h_2_data.py)", "research_inputs/corridors/READJUST_IMPEDANCE_S4H2.csv", sha256(C / "READJUST_IMPEDANCE_S4H2.csv"), decision_ref="101",
            status="REFERENCE_ONLY")
    reg.add("s4h2_readjust_impedance_table", "Decision 101 b: READJUST_IMPEDANCE_S4H2.csv = READJUST_IMPEDANCE_S4G1.csv (the 19 author-readjusted cross-border AC lines, unchanged) + "
            "APG17_LA_MM; applied at build time with the pre-correction values checked (research.network.readjust_impedance_table)", "table", "flag", "B",
            "derived (scripts_project/s4h_2_data.py)", "research_inputs/corridors/READJUST_IMPEDANCE_S4H2.csv", sha256(C / "READJUST_IMPEDANCE_S4H2.csv"), decision_ref="101",
            status="REFERENCE_ONLY")
    names = [x["component"] for x in js["new_components"]]
    reg.add("s4h2_reference_candidates", f"Decision 101 c: every country pair with AC stock has at least one zero-capacity AC candidate - pairs lacking one "
            f"({', '.join(js['pairs_needing'])}) get a candidate at every adjacent node pair of ADJACENCY_S4E1.csv (decision-94 rule, S4E-1 parameters: great-circle "
            f"x 1.25, subsea share by the S4C supplement 01 rule, AC on one landmass else DC, cost by the decision-50 layer): {js['n_ac']} AC lines + {js['n_dc']} DC link "
            f"({'; '.join(names)})", float(len(names)), "components", "B", "derived (scripts_project/s4h_2_data.py)", "research_inputs/corridors/CORRIDORS_S4H2.csv",
            sha256(C / "CORRIDORS_S4H2.csv"), decision_ref="101", status="REFERENCE_ONLY")
    reg.add("s4h2_candidate_completeness_table", f"Decision 101 c: stock and candidate lines / DC links of the {js['pairs']} cross-border country pairs (with a cross-border "
            "component or land-adjacent by decision 94), before and after the completion", "table", "flag", "B", "derived (scripts_project/s4h_2_data.py)",
            "research_inputs/corridors/CANDIDATE_COMPLETENESS_S4H2.csv", sha256(C / "CANDIDATE_COMPLETENESS_S4H2.csv"), decision_ref="101", status="REFERENCE_ONLY")
    reg.add("s4h2_subsea_table", "Decision 101 c: SUBSEA_SHARE_S4H2.csv = SUBSEA_SHARE_S4F2.csv with the S4H-2 components listed at their node pairs (all pairs present "
            "already; shares recomputed and equal)", "table", "flag", "B", "derived (scripts_project/s4h_2_data.py)", "research_inputs/corridors/SUBSEA_SHARE_S4H2.csv",
            sha256(C / "SUBSEA_SHARE_S4H2.csv"), decision_ref="101", status="REFERENCE_ONLY")
    if (C / "XB_LENGTH_SHARES_S4H2.csv").exists():
        reg.add("s4h2_length_shares_table", "Decision 101 c: in-country length shares of every cross-border line / link of the S4H-2 integrated build with the optional "
                "SG-VN / SG-KH candidates (method of s4d_3_data.length_shares; ledger sensitivity of decision 91a)", "table", "flag", "B", "derived (scripts_project/s4h_2_data.py)",
                "research_inputs/corridors/XB_LENGTH_SHARES_S4H2.csv", sha256(C / "XB_LENGTH_SHARES_S4H2.csv"), decision_ref="101", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4h_2.csv")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, default=None); ap.add_argument("--length-shares", type=Path, default=None)
    ap.add_argument("--registry", action="store_true"); a = ap.parse_args()
    if a.registry:
        write_registry(); print("registry fragment s4h_2 written"); return
    if a.length_shares is not None:
        from s4d_3_data import length_shares
        sh = length_shares(a.length_shares); write_csv(sh.to_dict("records"), C / "XB_LENGTH_SHARES_S4H2.csv", list(sh.columns))
        write_registry(); print(len(sh), "components;", int((sh.samples_other > 50).sum()), "with > 50 of 401 samples outside the two end countries"); return
    main_tables(a.network)


if __name__ == "__main__":
    main()
