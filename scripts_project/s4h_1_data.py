"""S4H-1 data (decision 100): LA-VN grid-to-grid stock 0 (AIMS basis), the four clustered LA-VN lines as zero-capacity candidates, and the order of
magnitude of the dedicated IPP export lines (grade C limitation, not modelled, not downloaded).

  * LA_VN_STOCK_S4H1.csv: lines 59 / 60 / 63 / 64 with the S4G-state values checked at build time (s_nom = s_nom_min = the author's AIMS 1 MW
    split by length, length, type).
  * IPP estimate: the annualised value of 572 MW (GEM: Xekaman 1 322 MW + Xekaman 3 250 MW, operating, Vietnamese-owned; S4G
    LA_VN_STOCK_CHECK_S4G1.json) carried over the range of LA-VN candidate lengths, at the model's AC unit cost (capital_cost / length of the
    LA-VN lines of the built network = the decision-50 cost layer: annualised HVAC overhead line incl. FOM).

    python scripts_project/s4h_1_data.py --network <S4G integrated build>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv

SCRIPT = "scripts_project/s4h_1_data.py"
INSTRUCTION_SHA = "a029bd64cef2ae1b84aec4ebc186ede21630283d17153df9aed4ae32d1fd33bd"
LOC = "work/p1_step4h_20261017/S4H_CLAUDE_CODE_INSTRUCTION.md"
C = ROOT / "research_inputs/corridors"
AUTHOR = Path("/mnt/d/ResearchWorkspaces/ASEAN/research/00_source_provenance/official/author_run/scripts/final_asean_adjustment.py")
LINES = ["59", "60", "63", "64"]
IPP = {"Xekaman 1 hydroelectric plant": 322.0, "Xekaman 3 hydroelectric plant": 250.0}


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    author_line = AUTHOR.read_text().splitlines()[311].strip() if AUTHOR.exists() else ""
    if author_line and '("LA", "VN", 1),  # no grid-to-grid connections in 2024.' not in author_line:
        raise ValueError("author AIMS_exist_data line 312 changed: " + author_line)
    n = pypsa.Network(str(a.network)); c = n.buses.country
    rows = []
    for k in LINES:
        z = n.lines.loc[k]
        if {str(c[z.bus0]), str(c[z.bus1])} != {"LA", "VN"}:
            raise ValueError(f"line {k} is not LA-VN")
        rows.append(dict(component=k, bus0=z.bus0, bus1=z.bus1, type=z.type, length_km=float(z.length), s_nom_author_mw=float(z.s_nom), capital_cost_eur_per_mw_a=float(z.capital_cost),
                         unit_cost_eur_per_mw_km_a=float(z.capital_cost) / float(z.length), action="zero-capacity candidate (decision 100)"))
    T = pd.DataFrame(rows); write_csv(T.to_dict("records"), C / "LA_VN_STOCK_S4H1.csv", list(T.columns))
    lavn = n.lines[[{str(c[b0]), str(c[b1])} == {"LA", "VN"} for b0, b1 in zip(n.lines.bus0, n.lines.bus1)]]
    unit = sorted({round(float(v), 6) for v in lavn.capital_cost / lavn.length})
    if len(unit) != 1:
        raise ValueError(f"LA-VN unit costs differ: {unit}")
    u = unit[0]; Lmin, Lmax = float(lavn.length.min()), float(lavn.length.max())
    chk = json.loads((C / "LA_VN_STOCK_CHECK_S4G1.json").read_text())
    gem = {p["Plant / Project name"]: float(p["Capacity (MW)"]) for p in chk["found"]["gem_lao_plants_vietnamese_party"] if p["Status"] == "operating"}
    for k, v in IPP.items():
        if abs(gem.get(k, -1) - v) > 1e-6:
            raise ValueError(f"GEM capacity of {k} differs: {gem.get(k)}")
    mw = sum(IPP.values()); lo, hi = mw * Lmin * u, mw * Lmax * u
    est = dict(capacity_mw=mw, plants=IPP, length_km=[Lmin, Lmax], length_basis="LA-VN line lengths of the model (the four clustered lines and the S4E-1 LA-VN candidates)",
               unit_cost_eur_per_mw_km_a=u, unit_cost_basis="capital_cost / length of the LA-VN AC lines in the built network (decision-50 cost layer)",
               annualised_value_eur_per_a=[lo, hi], note="order of magnitude of the stock not modelled (grade C): what the model would otherwise pay to build 572 MW of LA-VN AC capacity")
    (C / "LA_VN_STOCK_S4H1.json").write_text(json.dumps(dict(lines=rows, ipp_estimate=est, author_line_312=author_line, network=str(a.network)), indent=1))
    reg = Registry(SCRIPT)
    reg.add("la_vn_grid_stock_2025", "Decision 100: LA-VN grid-to-grid interconnection stock 2025 = 0 MW - AIMS tables list only Nam Ou - Dien Bien (220 kV, in_planning, "
            "2030), APG #10 has no existing value; the author's AIMS_exist_data gives 1 MW with the comment 'no grid-to-grid connections in 2024' "
            "(final_asean_adjustment.py line 312). The four clustered LA-VN lines 59 / 60 / 63 / 64 become zero-capacity candidates", 0.0, "MW", "B",
            "AIMS transmission projects (data/transmission_projects/AIMS); APG AIMS III Table 1 #10; author final_asean_adjustment.py line 312",
            "research_inputs/corridors/LA_VN_STOCK_S4H1.csv", sha256(C / "LA_VN_STOCK_S4H1.csv"), sensitivity_low=0.0, sensitivity_high=1.0, decision_ref="100")
    reg.add("s4h1_la_vn_stock_switch", "Decision 100: research.network.la_vn_stock = aims_zero (main: lines 59 / 60 / 63 / 64 with s_nom = s_nom_min = 0, extendable, "
            "individual limit 0 + 20,000 MW, length / unit cost / subsea share unchanged, cross-border network class, candidate num_parallel convention) | author "
            "(the S4G state, comparison)", "aims_zero|author", "flag", "B", "S4H instruction S4H-1", LOC, INSTRUCTION_SHA, decision_ref="100", status="REFERENCE_ONLY")
    reg.add("s4h1_ipp_export_lines_estimate", f"Decision 100 limitation (grade C, not modelled, not downloaded): dedicated IPP export lines Laos -> Viet Nam. Order of "
            f"magnitude: {mw:.0f} MW (GEM Xekaman 1 322 MW + Xekaman 3 250 MW, operating, Vietnamese-owned) x {Lmin:.0f}-{Lmax:.0f} km (model LA-VN line lengths) x "
            f"{u:.3f} EUR/MW/km/a (model AC cost layer) = {lo / 1e6:.1f}-{hi / 1e6:.1f} M EUR/a of LA-VN capacity the model has to build instead", hi,
            "EUR/a", "C", "derived (scripts_project/s4h_1_data.py)", "research_inputs/corridors/LA_VN_STOCK_S4H1.json", sha256(C / "LA_VN_STOCK_S4H1.json"),
            sensitivity_low=lo, sensitivity_high=hi, decision_ref="100", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4h_1.csv")
    print(T.to_string()); print(json.dumps(est, indent=1))


if __name__ == "__main__":
    main()
