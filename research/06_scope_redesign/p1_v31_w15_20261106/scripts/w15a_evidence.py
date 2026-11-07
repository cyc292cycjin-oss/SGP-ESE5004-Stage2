"""V31 W15 stage A: EVIDENCE.json - SHA256 and bytes of every input file read and every deliverable written (read only).

  python -I w15a_evidence.py --work <work dir> --out <work/p1_v31_w15_20261106> --registry-s07 <file> --registry-f <file> --smoke-v31 <dir> --smoke-sb <dir> --smoke-sa <dir>
"""
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def entry(p: Path, label: str) -> dict:
    return dict(path=label, bytes=p.stat().st_size, sha256=sha(p))


def main():
    ap = argparse.ArgumentParser()
    for k in ("work", "out", "registry_s07", "registry_f", "smoke_v31", "smoke_sb", "smoke_sa"):
        ap.add_argument("--" + k.replace("_", "-"), required=True)
    a = ap.parse_args()
    W, OUT = Path(a.work), Path(a.out)
    V3 = W / "p1_v3_20261102"; RES = V3 / "hpc_results_v31"; PKG = V3 / "hpc_package_v3_1"; SPKG = V3 / "screen_package_v3_dmax"
    S07 = V3 / "cloud_results" / "final_20261103T160537Z" / "full_unpacked" / "export"
    rel = lambda p: str(p.relative_to(W)) if str(p).startswith(str(W)) else str(p)
    inputs = {}
    inputs["instruction"] = [entry(OUT / f, rel(OUT / f)) for f in ("V31_W15_INSTRUCTION.md", "V31_W15_SHA256.txt", "V31_W15_SUPP01.md", "V31_W15_SUPP01_SHA256.txt")
                             if (OUT / f).exists()]
    inputs["archives"] = [entry(p, rel(p)) for p in sorted(RES.glob("interim_F*.tar.gz*"))]
    inputs["interim_unpacked"] = [entry(p, rel(p)) for p in sorted((RES / "interim_unpacked").rglob("*")) if p.is_file()]
    inputs["hpc_package_v3_1"] = [entry(PKG / f, rel(PKG / f)) for f in ("BATCH_DEF.json", "REFERENCE_VALUES.json", "COMMIT", "RUN_PLAN_HPC_V3.md", "RUN_PLAN_V3.md",
                                                                          "HPC_OPERATOR_GUIDE_V3.md", "pack_results.sh", "run_batch4.sh", "SHA256SUMS")] + \
                                 [entry(p, rel(p)) for p in sorted((PKG / "networks").iterdir()) if p.is_file()]
    inputs["supplement07_export"] = [entry(S07 / r / f, rel(S07 / r / f)) for r in ("V1", "V2") for f in (
        "RUN.json", "SOLVE_RECEIPT.json", "COUNTRY_COST_LEDGER_DETAIL.csv", "CAPACITY_BY_TECH_COUNTRY.json", "cross_border_flows.csv", "costs_active_research.csv",
        "V5_GATES.json", "GUROBI_LOG_SCRUBBED.txt", "COMPONENT_COST_BREAKDOWN.csv")]
    inputs["screen_package_v3_dmax"] = [entry(SPKG / "COMMIT", rel(SPKG / "COMMIT"))] + [entry(p, rel(p)) for p in sorted((SPKG / "networks").iterdir()) if p.suffix in (".json", ".csv")]
    inputs["registry"] = [dict(entry(Path(a.registry_s07), "git show 7aec953e:research_inputs/registry_v5/DATA_REGISTRY.csv")),
                          dict(entry(Path(a.registry_f), "git show a1ef782b:research_inputs/registry_v5/DATA_REGISTRY.csv (= HEAD 1899c837)"))]
    sm = []
    for base, label in ((Path(a.smoke_v31), "v3.1 smoke56 (drill package 13ebce95, S-A)"), (Path(a.smoke_sb), "supplement 05 smoke56 (S-B)"), (Path(a.smoke_sa), "V3 HPC smoke56 (S-A)")):
        for r in ("F1", "F2", "integrated", "no_new_xb"):
            for f in ("CAPACITY_BY_TECH_COUNTRY.json", "COUNTRY_COST_LEDGER_DETAIL.csv", "SOLVE_RECEIPT.json", "cross_border_flows.csv", "RUN.json", "GUROBI_LOG_SCRUBBED.txt"):
                p = base / r / f
                if p.exists():
                    sm.append(dict(entry(p, str(p)), set=label))
    inputs["smoke56_reference"] = sm
    w10 = W / "p1_v4_w10_20261106"
    inputs["w10"] = [entry(w10 / f, rel(w10 / f)) for f in ("REPORT.md", "EVIDENCE.json", "C_GRADE_INVENTORY.csv", "rerank_with_results.py")]
    # stage B (batch result packs), present once the user downloaded them
    packs = sorted(RES.glob("results_*_final_*.tar.gz*")) + [RES / f for f in ("BATCH4_SUMMARY.json", "BATCH4_SUMMARY.md", "STATUS.txt", "PBS_JOBS.txt", "SUBMITTED.txt") if (RES / f).exists()]
    if packs:
        inputs["stage_b_downloads"] = [entry(p, rel(p)) for p in packs]
        inputs["stage_b_unpacked"] = [entry(p, rel(p)) for p in sorted((RES / "unpacked").rglob("*")) if p.is_file() and not p.name.startswith(".unpack")]
        inputs["supplement07_solved"] = [entry(S07 / r / f, rel(S07 / r / f)) for r, f in (("V1", "integrated_DFX_365X24H_solved.nc"), ("V2", "no_new_xb_DFX_365X24H_solved.nc"),
                                                                                         ("V1", "DUALS_BY_CONSTRAINT.nc"), ("V2", "DUALS_BY_CONSTRAINT.nc"),
                                                                                         ("V1", "NODAL_PRICES.csv"), ("V2", "NODAL_PRICES.csv"), ("V1", "m12_owen/OWEN.csv"), ("V2", "m12_owen/OWEN.csv"))
                                         if (S07 / r / f).exists()]
        SCR = V3 / "cloud_results" / "final_20261103T063207Z" / "full_unpacked" / "export"
        inputs["screening_export"] = [entry(SCR / r / f, rel(SCR / r / f)) for r in ("V1", "V2") for f in (
            "cross_border_flows.csv", "NODAL_PRICES.csv", "COUNTRY_COST_LEDGER.csv", "V5_GATES.json", "m12_owen/OWEN.csv") if (SCR / r / f).exists()] + \
            [entry(p, rel(p)) for p in sorted((SCR / "batch").rglob("BENEFIT.csv"))] + \
            [entry(p, rel(p)) for p in sorted((S07 / "batch").rglob("BENEFIT.csv"))]
    outputs = [entry(p, str(p.relative_to(OUT))) for p in sorted(OUT.rglob("*"))
               if p.is_file() and p.name not in ("EVIDENCE.json", "PROGRESS.md") and not p.name.startswith("REVIEW_")
               and not ({"__pycache__", "cache", "logs"} & set(p.relative_to(OUT).parts))]
    ev = dict(
        schema="v31-w15-evidence-v1", step="V31 W15 stage A (ledger W15; decisions 212, 213)", written_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        instruction=dict(file="V31_W15_INSTRUCTION.md", sha256=sha(OUT / "V31_W15_INSTRUCTION.md"), expected=(OUT / "V31_W15_SHA256.txt").read_text().split()[0]),
        branch="codex/v31-w15-20261106", base_commit="1899c837efd78a5f454396b98bf49724c5f85758", worktree="/home/jin/wt_v31_w15",
        scope=("stage A (F1, F2, F4 interim exports) and stage B (batch result packs, F1-F4)" if packs else
               "stage A only: F1, F2, F4 interim exports; F3 interim and batch result packs not yet downloaded"),
        budget=(dict(solver_calls=0, hpc_connections=0, downloads_by_session=0, local_compute_minutes_both_stages=40, disk_added_gb_both_stages=7.5,
                     unsolved_networks_read=3, solved_networks_read="4 x 2920x3h (one at a time, memory guard) + 2 x 365 daily slices",
                     memory="extraction peak RSS 3.5-3.7 GB per 2920x3h network; min MemAvailable 6.75 GiB; no Gurobi process")
                if packs else dict(solver_calls=0, hpc_connections=0, downloads=0, local_compute_minutes=3, disk_added_mb=52, unsolved_networks_read=3, solved_networks_read=0)),
        privacy="HPC user and node names scrubbed to <user> / <node> in every deliverable; checked with a run-time pattern scan (pattern not stored)",
        inputs=inputs, outputs=outputs,
        outputs_note="PROGRESS.md and REVIEW_MANIFEST.csv / REVIEW_*.zip are written after this file (commit SHAs) and are not listed; the review manifest lists every member's SHA256 and CRC32",
    )
    (OUT / "EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("inputs", sum(len(v) for v in inputs.values()), "outputs", len(outputs))


if __name__ == "__main__":
    main()
