"""S4R: S4R_EVIDENCE.json - SHA256 of inputs (downloads, S4P files used) and outputs, key numbers."""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import OUT, S4P, STEP, WORK, dump_json  # noqa: E402


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def main():
    dl = WORK / "p1_s4r_downloads_20261020"
    inputs = {}
    for p in sorted(dl.rglob("*")):
        if p.is_file() and p.stat().st_size < 200e6:
            inputs[str(p.relative_to(WORK))] = dict(bytes=p.stat().st_size, sha256=sha(p))
        elif p.is_file():
            inputs[str(p.relative_to(WORK))] = dict(bytes=p.stat().st_size, sha256="not hashed (> 200 MB; raster zip not used)")
    for name in ["ASPECTS_SUMMARY.json", "ASPECT6_BIOMASS.csv", "PROPOSED_FIXES.md", "evidence/EXT_DEMAND_BENCHMARKS.json", "evidence/EXT_TECH_POLICY_BENCHMARKS.json", "evidence/EXT_COST_BENCHMARKS.json", "evidence/net/NET_integrated_unsolved_loads.csv"]:
        p = S4P / name
        if p.exists():
            inputs[f"p1_step4p_20261020/{name}"] = dict(bytes=p.stat().st_size, sha256=sha(p))
    outputs = {}
    for name in ["S4R_PLAN.md", "GATES_V6.md", "GATES_V6_SHA256.txt", "GATES_V6_NOTES.md", "S4R_SUPPLEMENT_01.md", "GATES_RETRO_COMPARISON.csv", "GATES_RETRO_COMPARISON.md", "IMPLEMENTATION_PLAN.md", "UNIFICATION_CHECKLIST.csv", "UNIFICATION_CHECKLIST.md",
                 "DEMAND_ANCHOR_COMPARISON.csv", "POTENTIAL_COMPARISON.csv", "LNG_CAPACITY_COMPARISON.csv", "CO2_STORAGE_UNIFIED.csv", "COST_CURRENCY_FIXES.csv", "COUNTRY_WACC_SENSITIVITY_TABLE.csv",
                 "REGISTRY_ROWS_PROPOSED.csv", "USER_DOWNLOAD_LIST.md", "EXTERNAL_SOURCES_S4R.md", "S4R_PROGRESS.md"]:
        p = OUT / name
        if p.exists():
            outputs[name] = dict(bytes=p.stat().st_size, sha256=sha(p))
    key = {}
    try:
        d = pd.read_csv(OUT / "DEMAND_ANCHOR_COMPARISON.csv").set_index("country")
        key["demand_ratio_tfec_model_over_aeo8_ats"] = d.ratio_tfec_model_over_aeo8_ats.round(3).to_dict()
        key["demand_ratio_fixed_elec_over_aeo8_ats"] = d.ratio_fixed_elec_over_aeo8_ats.round(3).to_dict()
        key["cement_2050_proposed_mt"] = d.cement_2050_proposed_mt.round(1).to_dict(); key["steel_2050_proposed_mt"] = d.steel_2050_proposed_mt.round(1).to_dict()
        p = pd.read_csv(OUT / "POTENTIAL_COMPARISON.csv").set_index("country")
        key["solar_ratio_model_over_esmap_l1_x5_1"] = p.ratio_model_solar_over_esmap_l1_x5_1.round(3).to_dict()
        g = pd.read_csv(OUT / "GATES_RETRO_COMPARISON.csv")
        key["gates_retro_labels"] = dict(zip(g.run, g.v6_label))
        c = pd.read_csv(OUT / "CO2_STORAGE_UNIFIED.csv").set_index("country"); key["co2_unified_gt"] = c.unified_potential_gt.round(3).to_dict()
        w = pd.read_csv(OUT / "COUNTRY_WACC_SENSITIVITY_TABLE.csv").set_index("country"); key["real_wacc_mid"] = w.real_wacc_mid.round(4).to_dict()
    except Exception as e:  # noqa: BLE001
        key["error"] = str(e)
    dump_json(dict(step="S4R (decisions 126, 128): unification plan and gates redesign; read-only, no solve, no cloud, no production code change",
                   instruction_sha256=(STEP / "S4R_INSTRUCTION_SHA256.txt").read_text(encoding="utf-8").split()[0], generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   gates_v6_sha256=(OUT / "GATES_V6_SHA256.txt").read_text(encoding="utf-8").split()[0] if (OUT / "GATES_V6_SHA256.txt").exists() else None,
                   inputs_sha256=inputs, outputs_sha256=outputs, key_numbers=key), OUT / "S4R_EVIDENCE.json")
    print("inputs", len(inputs), "outputs", len(outputs))


if __name__ == "__main__":
    main()
