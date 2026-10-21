"""M08a A3 evidence (read-only): apply the existing-stock vintage rule IN MEMORY to the S4M-3 built networks (integrated, disconnected).

The networks on disk are not changed and nothing is solved. Output: <out>/evidence/M08A_A3_EXISTING_VINTAGE.json and
M08A_A3_EXISTING_VINTAGE_<scenario>.csv (per component before / after).

    PYTHONHASHSEED=0 python m08a_a3_evidence.py --repo /home/jin/wt_m08a_20261021 \
        --builds /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/s4m/s4m3/builds --out <work dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--builds", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import pypsa
    from phase4_static import config
    from m08a_layers import apply_existing_vintage_costs
    out = dict(schema="m08a-a3-existing-vintage-v1", solver_runs=0, network_files_changed=0, rule="scripts_project/m08a_layers.apply_existing_vintage_costs", by_scenario={})
    (a.out / "evidence").mkdir(parents=True, exist_ok=True)
    for sc in ("integrated", "disconnected"):
        p = a.builds / sc / f"{sc}_2920_3h_unsolved.nc"
        before_sha = sha(p)
        n = pypsa.Network(str(p))
        cfg = config(a.repo, sc)
        led = apply_existing_vintage_costs(n, cfg, a.repo)
        assert sha(p) == before_sha
        t = pd.DataFrame(led["table"])
        t.assign(years=t.years.map(lambda v: ";".join(map(str, v)))).to_csv(a.out / "evidence" / f"M08A_A3_EXISTING_VINTAGE_{sc}.csv", index=False, float_format="%.10g")
        out["by_scenario"][sc] = dict(network=str(p), network_sha256=before_sha, **{k: v for k, v in led.items() if k not in ("table",)})
    i, d = out["by_scenario"]["integrated"], out["by_scenario"]["disconnected"]
    out["fom_identical_between_scenarios"] = bool(abs(i["fom_after_eur"] - d["fom_after_eur"]) <= 1e-6 * max(1.0, i["fom_after_eur"]))
    out["fom_change_bn"] = (i["fom_after_eur"] - i["fom_before_eur"]) / 1e9
    (a.out / "evidence" / "M08A_A3_EXISTING_VINTAGE.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(dict(fom_before_bn=i["fom_before_eur"] / 1e9, fom_after_bn=i["fom_after_eur"] / 1e9, identical=out["fom_identical_between_scenarios"],
                          ccgt=i["by_carrier"]["CCGT existing"]), indent=1, default=str))
    for c, v in i["by_carrier"].items():
        print(f"{c:18s} mw {v['mw']:9.1f} eff {v['efficiency_before_mw_weighted']:.4f} -> {v['efficiency_after_mw_weighted']:.4f} "
              f"FOM {v['fom_before_eur'] / 1e9:.4f} -> {v['fom_after_eur'] / 1e9:.4f} bn years {v['table_years']}")


if __name__ == "__main__":
    main()
