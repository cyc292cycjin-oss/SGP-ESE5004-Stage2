"""V4 W14: EVIDENCE.json - the reported numbers with status EXACT / VERIFIED / INFERENCE / PROPOSED, read from the W14 files (no recomputation; drill entries are
read from the drill reports copied into logs/).

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w14_evidence.py <package commit>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[1]
PKG = W / "hpc_package_v4"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jl(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def lines(p: Path, rx: str) -> list:
    return [l.strip() for l in p.read_text(encoding="utf-8", errors="replace").splitlines() if re.search(rx, l)] if p.exists() else []


def main():
    commit = sys.argv[1]
    rows = []
    add = lambda k, v, unit, st, src, note="": rows.append(dict(id=k, value=v, unit=unit, status=st, source=src, note=note))   # noqa: E731
    add("instruction.sha256", sha(W / "V4_W14_INSTRUCTION.md"), "sha256", "VERIFIED", "V4_W14_INSTRUCTION.md", "= V4_W14_SHA256.txt (checked before starting)")
    add("session.model", "claude-opus-5-5 (Opus 5.5)", "-", "VERIFIED", "session system information", "effort setting of the session not visible to the session (instruction asks Xhigh)")
    add("branch", dict(branch="codex/v4-w14-20261109", base="4e83d71ed20010b87867d7889693d879fe11a4ab", d2c_review_commit="612d8f6b23f1e01f93d2f2270cbdce5b8e4a50c4",
                       d2c_review_commit_is_ancestor=True, files_changed_between_outside_d2c_folder=0), "-", "VERIFIED", "PROGRESS.md", "git merge-base --is-ancestor; git diff --name-only")
    st = jl(W / "STATIC_CHECKS.json") or {}
    for rid, r in st.items():
        add(f"network.{rid}", dict(sha256=r["network_sha256"], bytes=r["network_bytes"], switch_sha256=r["network_meta_v4"]["switch_sha256"], tables_dir=r["network_meta_v4"]["tables_dir"],
                                   d2c_sha256=r["d2c_network_sha256"], identical_data_to_d2c_2920=r["C8_identical_data_2920"], identical_data_to_d2c_365=r["C8_identical_data_365"]),
            "-", "VERIFIED", "STATIC_CHECKS.json", "build commit 59b128ea (W14-1)")
        add(f"static.{rid}", {k: r[k] for k in ("C1_industry_loads_vs_summary_max_abs_mwh", "C2_ev_vs_land_x_ev_factor_max_rel", "C3_max_ratio", "C3_no_new_zero_margin_pool", "C4_gas_caps_vs_table_max_rel",
                                                 "C6_switch_sha_equals_tables", "C9_trunk_at_proxy", "C10_overflow_ledger_vs_table_max_abs_mwh", "C11_band_shares_ledger_vs_table_max_abs",
                                                 "C12_lng_mc_change_max_dev_vs_D2c")} | dict(C6b_passed=r["C6b_meta"]["passed"], B12_identity=r["C6b_meta"]["b12_identity"]),
            "-", "VERIFIED", "STATIC_CHECKS.json")
    z = jl(W / "evidence/ZERO_SLACK_CHECK_W14.json") or {}
    add("zero_slack_gate", dict(passed=z.get("passed"), networks={x["label"]: dict(passed=x["passed"], verdicts=x["verdicts"]) for x in z.get("networks", [])}), "-", "VERIFIED", "evidence/ZERO_SLACK_CHECK_W14.json")
    t = jl(W / "evidence/W14_TRUNC56.json") or {}
    for rid, v in t.items():
        add(f"trunc56.{rid}", dict(w14_sha256=v["w14"]["sha256"], d2c_sha256=v["d2c"]["sha256"], identical_data=v["identical_data"], meta_keys_differing=v["meta_keys_differing"],
                                   weights_8760_over_56=v["weights_all_8760_over_56"]), "-", "VERIFIED", "evidence/W14_TRUNC56.json", "s2_solve.py --truncate 56 rule")
    d = jl(W / "batch_def/BATCH_DEF_2920x3h_v4hpc.json")
    add("smoke_expected", d["smoke_expected"]["objective"], "EUR", "VERIFIED", "batch_def/BATCH_DEF_2920x3h_v4hpc.json", "D2c local 56-snapshot smoke R1 / R2 (networks component-identical)")
    add("registered_limits", dict(status=d["limits_status"], **d["limits"], walltime={k: j["walltime"] for k, j in d["hpc_jobs"].items()}, iterations_reference={k: r["iterations_reference"] for k, r in d["runs"].items()}),
        "-", "VERIFIED", "batch_def/BATCH_DEF_2920x3h_v4hpc.json", "decision 222")
    b = jl(W / "evidence/W14_BOUNDS_PRE.json") or {}
    for rid in ("F1", "F2"):
        if rid in b:
            r = b[rid]
            add(f"alarm_line.{rid}", {k: r[k] for k in ("v31_objective_eur", "constant_change_eur", "rhs_lower_bound_eur", "structure_lower_bound_eur", "cost_class_lower_bound_eur",
                                                     "cost_class_upper_bound_eur", "coefficient_first_order_eur", "tolerance_eur", "alarm_line_eur", "alarm_objective_eur", "first_order_estimate_eur", "n_unclassified")},
                "EUR", "EXACT", "evidence/W14_BOUNDS_PRE.json", "rule EXACT, numbers from the v3.1 2920x3h HPC duals; registered in RUN_PLAN_HPC_V4.md section 8 before any v4 HPC solve")
    man = jl(PKG / "HPC_PACKAGE_MANIFEST.json")
    if man:
        add("package", dict(commit=man["commit"], sha256sums_sha256=man["sha256sums_sha256"], files_listed=len(man["files"]), files_total=sum(1 for p in PKG.rglob("*") if p.is_file()),
                            bytes_excluding_manifest=man["upload_total_bytes_excluding_this_manifest"], consistency=man["consistency"], zero_slack=man["zero_slack_check"]["passed"], run_dirs=man["run"]["run_dirs"],
                            jobs=[j["name"] for j in man["run"]["jobs"].values()]), "-", "VERIFIED", "hpc_package_v4/HPC_PACKAGE_MANIFEST.json", "package commit = " + commit)
    for name in ("dry_bash", "dry_bash42", "smoke_drill"):
        p = W / f"logs/{name}.txt"
        if p.exists():
            add(f"drill.{name}", lines(p, r"^(UNPACKED|PREFLIGHT:|LOGIN_PREFLIGHT|BUILD_ONLY_ALL|JOB_BODY|SUBMIT_DRY|DRY-RUN|STATUS_|SMOKE|F[12]:termination|POSTPROC|BATCH_DONE|HALTED|PACKS|WLS|REBUILD)")[:60],
                "-", "VERIFIED", f"logs/{name}.txt")
    p = W / "logs/rebuild_and_dry.txt"
    if p.exists():
        add("rebuild_at_package_commit", lines(p, r"REBUILD_CMP|RECEIPT_KEYS"), "-", "VERIFIED", "logs/rebuild_and_dry.txt", "same worktree path; 2920x3h files must be byte-identical")
    for name in ("leak_scan",):
        p = W / f"logs/{name}.txt"
        if p.exists():
            add("leak_scan", lines(p, r"pattern_file|pack_results_regex"), "-", "VERIFIED", f"logs/{name}.txt", "counts only; patterns never printed")
    add("predictions", dict(F1_objective_bn="336-339 (range 325-350)", F2_objective_bn="348-351 (range 337-362)", B6_bn="positive; 11.8-13.0 (range 10.5-14.5)",
                            owen_positive=["BN", "ID", "KH", "LA", "MM", "MY", "SG", "TL", "VN"], owen_probably_positive=["BUNKER"], owen_uncertain=["TH", "PH"],
                            iterations="F1 210-260, F2 140-200", peak_rss_gib="F1 105-130, F2 95-120", process2_h="F1 8-20, F2 4-12"), "-", "INFERENCE", "RUN_PLAN_HPC_V4.md section 9",
        "registered before any v4 HPC solve")
    out = dict(step="V4 W14", package_commit=commit, rows=rows)
    (W / "EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n")
    print("EVIDENCE.json rows", len(rows))


if __name__ == "__main__":
    main()
