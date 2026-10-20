"""S4P: compile S4P_EVIDENCE.json (read-only): SHA256 of every input file used, key numbers from the analyses A / aspects / rules,
labelled VERIFIED (read from exports / networks) or INFERENCE (derived estimates written in the report)."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4p_paths import NETS, OUT, RUNS, SOLVED_NC, STEP, dump_json, load_json  # noqa: E402


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    inputs = {}
    for run, d in RUNS.items():
        for name in ["COUNTRY_COST_LEDGER.csv", "COUNTRY_COST_LEDGER_DETAIL.csv", "LEDGER_IDENTITY.json", "cross_border_flows.csv", "CO2_FLOWS.json",
                     "CAPACITY_BY_TECH_COUNTRY.json", "NODAL_PRICES.csv", "SOLVE_RECEIPT.json", "EXPORTS.json"]:
            p = d / name
            if p.exists():
                inputs[f"{run}/{name}"] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    for run, p in SOLVED_NC.items():
        if p.exists():
            inputs[f"{run}/{p.name}"] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    for name in ["integrated_365_24h_unsolved.nc", "disconnected_365_24h_unsolved.nc"]:
        p = NETS / name
        if p.exists():
            inputs[f"package/{name}"] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    outputs = {}
    for name in ["A_CHANNEL_DECOMPOSITION.md", "A_SUMMARY.json", "A_CHANNEL_LONG.csv", "A_CHANNEL_BY_COUNTRY.csv", "ASPECTS_TABLES.md", "ASPECTS_SUMMARY.json",
                 "ASPECT1_EXTRA_ASEAN_USE.csv", "ASPECT5_CO2.csv", "ASPECT6_BIOMASS.csv", "ASPECT8_B6_BY_RULE.csv", "POOL_SETTLEMENT_BY_ENTITY.md",
                 "COUNTRY_AUDIT_MATRIX.csv", "COUNTRY_AUDIT_MATRIX.md", "PROPOSED_FIXES.md", "EXTERNAL_SOURCES.md"]:
        p = OUT / name
        if p.exists():
            outputs[name] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    ext = {}
    for name in ["EXT_DEMAND_BENCHMARKS.json", "EXT_TECH_POLICY_BENCHMARKS.json", "EXT_COST_BENCHMARKS.json", "EXT_DEMAND_BENCHMARKS.md", "EXT_TECH_POLICY_BENCHMARKS.md", "EXT_COST_BENCHMARKS.md"]:
        p = OUT / "evidence" / name
        if p.exists():
            ext[name] = {"bytes": p.stat().st_size, "sha256": sha(p)}
    A = load_json(OUT / "A_SUMMARY.json"); S = load_json(OUT / "ASPECTS_SUMMARY.json")
    ev = {
        "step": "S4P (decision 122 point 2): full-model, 11-country audit; read-only, no solve, no cloud",
        "instruction_sha256": (STEP / "S4P_INSTRUCTION_SHA256.txt").read_text(encoding="utf-8").split()[0],
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runs": {"integrated": "S4N pilot 20261019T072454Z_5125 (optimal; light export only)", "disconnected": "S4O-6 20261019T162951Z_6896 (SUBOPTIMAL, C1 passed)",
                 "integrated_nze": "S4O-6 20261019T162951Z_6896 (SUBOPTIMAL, C1 passed)"},
        "inputs_sha256": inputs, "external_benchmark_files": ext, "outputs_sha256": outputs,
        "VERIFIED": {
            "objective_bn": A["objective_bn"], "B6_bn": A["b6_detail_bn"], "nze_minus_integrated_bn": A["nze_minus_int_detail_bn"],
            "ledger_identity_max_absdiff_eur": A["identity_max_absdiff_eur"],
            "country_dis_minus_int_bn": {e: v["dis_minus_int_bn"] for e, v in A["entities"].items()},
            "country_nze_minus_int_bn": {e: v["nze_minus_int_bn"] for e, v in A["entities"].items()},
            "class_dis_minus_int_bn": A["class_dis_minus_int_bn"],
            "VN_top_items_dis_minus_int_bn": A["entities"]["VN"]["top_items_dis_minus_int_bn"][:12],
            "B6_by_settlement_rule_bn": S["aspect8_b6_by_rule"],
            "extra_asean_use_twh": S["aspect1"]["use_twh"],
            "terminals": S["aspect1"]["terminals"],
            "candidate_caps_gw": S["aspect3_candidate_caps_gw"],
            "pnom_opt_gw": S["aspect3_pnom_opt_gw"],
            "co2": S["aspect5"], "biomass": S["aspect6"],
            "net_imports_integrated": S["aspect2_net_imports_integrated"],
            "corridors_integrated": S["aspect8_integrated"]["corridors"],
            "disconnected_definition": "integrated vs disconnected build networks differ only in the cross-border network components (lines 62, links 292: gas pipeline 117 incl. existing ID-SG 8,795 / MM-TH 13,845 / MY-TH 11,244 MW, H2 pipeline 110, CO2 pipeline 55, DC 10); maritime_trade links (CO2 ship 504, transit ship 42, transit rail 6), regional liquid pools and every extra-ASEAN generator (same set, p_nom_max and marginal_cost) are identical",
        },
        "INFERENCE": "see S4P_REPORT.md section 6 and PROPOSED_FIXES.md (magnitude estimates are arithmetic on the VERIFIED numbers, not re-solves)",
    }
    dump_json(ev, OUT / "S4P_EVIDENCE.json")
    print("inputs", len(inputs), "outputs", len(outputs), "ext", len(ext))


if __name__ == "__main__":
    main()
