"""M10R evidence collector (read only; run inside WSL with the project python from the worktree root):
    PYTHONHASHSEED=0 python /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10r_20261024/scripts/m10r_evidence.py --out /mnt/d/.../M10R_EVIDENCE.json
Gathers: instruction SHA256, git commits of the branch since efef93bf, the local Gurobi solve records (results_project/m10r/STATUS.txt), the
56x3h reproduction and its post-fix results, the pre / post regression comparison, the 365x24h structural check, the drill record, the test
summaries, package v6 vs v5, the dry runs, the fuel-bunker WACC numbers (light pack of the third batch), the full-pack download state."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work")
M10R = W / "p1_m10r_20261024"
RES = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m10r")
WT = Path("/home/jin/wt_m10p_20261022")
LIGHT = W / "p1_m10_20261022/cloud_results/20261023T174135Z_halted/light_unpacked/export"
FULL = W / "p1_m10_20261022/cloud_results/20261023T174135Z_halted/full"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jl(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def git(*a):
    return subprocess.run(["git", *a], cwd=WT, capture_output=True, text=True).stdout.strip()


def status_lines(p):
    return Path(p).read_text().splitlines() if Path(p).exists() else []


def solves():
    rows = []; lines = status_lines(RES / "STATUS.txt")
    for i, l in enumerate(lines):
        m = re.match(r"^SOLVE_(\d+):(\S+?):(.*)$", l)
        if m:
            k = m.group(1); start = m.group(2)
            end = next((x for x in lines[i:] if x.startswith(f"END_{k}:")), "")
            parts = end.split(":")
            rows.append(dict(solve=int(k), start_utc=start, end_utc=(parts[1] if len(parts) > 1 else None), detail=":".join(parts[2:]) if len(parts) > 2 else None, line=l))
    return rows


def ledger_asean(rid):
    out = {}
    with open(LIGHT / rid / "COUNTRY_COST_LEDGER.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["entity"].startswith("ASEAN"):
                out[r["entity"]] = {k: float(v) for k, v in r.items() if k != "entity" and v not in ("", None)}
    return out


def prices_asean(rid):
    out = {}
    with open(LIGHT / rid / "NODAL_PRICES.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["country"] == "ASEAN":
                out[r["bus"]] = dict(carrier=r["carrier"], mean=float(r["mean"]), min=float(r["min"]), max=float(r["max"]))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--tests", type=Path, default=None); ap.add_argument("--dist", type=Path, default=None)
    ap.add_argument("--dist-v5", type=Path, default=W / "p1_m10p_20261022/cloud_package_dist_v5_e0a89f8e"); ap.add_argument("--dryrun", type=Path, default=None)
    a = ap.parse_args()
    ins = M10R / "M10R_CLAUDE_CODE_INSTRUCTION.md"
    ev = dict(instruction=dict(file=ins.name, sha256=sha(ins), registered=(M10R / "M10R_INSTRUCTION_SHA256.txt").read_text().split()[0]),
              worktree=dict(path=str(WT), branch=git("branch", "--show-current"), head=git("rev-parse", "HEAD"), start="efef93bf9eab307cd1cfb432506787ee66a38667",
                            commits=[dict(sha=l.split()[0], subject=" ".join(l.split()[1:])) for l in git("log", "--format=%H %s", "efef93bf..HEAD").splitlines()]),
              gurobi_local=dict(authorised=3, used=int((RES / ".solves_used").read_text().strip()) if (RES / ".solves_used").exists() else 0, solves=solves(),
                                status_file=str(RES / "STATUS.txt")),
              reproduction_v5=dict(dir=str(RES / "keepstock_v5"), receipt={k: (jl(RES / "keepstock_v5/SOLVE_RECEIPT.json") or {}).get(k) for k in ("objective", "termination_condition", "solve_seconds", "solver_profile")},
                                   input_network=(jl(RES / "keepstock_v5/SOLVE_RECEIPT.json") or {}).get("input_network"),
                                   b16=(jl(RES / "keepstock_v5/V5_GATES.json") or {}).get("B16_LEDGER", {}).get("error"),
                                   c1=(jl(RES / "keepstock_v5/PRECISION.json") or {}).get("grade"), m12_err=(RES / "keepstock_v5/m12.err").read_text().splitlines()[-1] if (RES / "keepstock_v5/m12.err").exists() else None,
                                   v6=(jl(RES / "keepstock_v5/V6_ACCEPTANCE.json") or {}).get("label"), g2_3=((jl(RES / "keepstock_v5/V6_ACCEPTANCE.json") or {}).get("G2") or {}).get("G2_3", {}).get("checks")),
              keepstock_after_fix=dict(dir=str(RES / "regress_post/keepstock"), ledger_redo=jl(RES / "regress_post/keepstock/LEDGER_REDO.json"),
                                       identity=(jl(RES / "regress_post/keepstock/LEDGER_IDENTITY.json") or {}).get("identity"),
                                       fom_meta=((jl(RES / "regress_post/keepstock/LEDGER_IDENTITY.json") or {}).get("diagnostics") or {}).get("existing_cross_border_fom_ledger"),
                                       c1=(jl(RES / "regress_post/keepstock/PRECISION.json") or {}).get("grade"), c1_b16=((jl(RES / "regress_post/keepstock/PRECISION.json") or {}).get("c_prices") or {}).get("b16"),
                                       m12=dict(identity=(jl(RES / "regress_post/keepstock/ALLOCATION.json") or {}).get("identity"), checks=(jl(RES / "regress_post/keepstock/ALLOCATION.json") or {}).get("checks")),
                                       owen_usable=(jl(RES / "regress_post/keepstock/m12_owen/OWEN.json") or {}).get("usable_for_allocation"),
                                       v6=dict(label=(jl(RES / "regress_post/keepstock/V6_ACCEPTANCE.json") or {}).get("label"), G1=(jl(RES / "regress_post/keepstock/V6_ACCEPTANCE.json") or {}).get("G1"),
                                               G2={k: v.get("passed") for k, v in ((jl(RES / "regress_post/keepstock/V6_ACCEPTANCE.json") or {}).get("G2") or {}).items()}),
                                       ledger_totals_eur=({r["entity"]: float(r["total"]) for r in csv.DictReader(open(RES / "regress_post/keepstock/COUNTRY_COST_LEDGER.csv"))} if (RES / "regress_post/keepstock/COUNTRY_COST_LEDGER.csv").exists() else None)),
              regression_56x3h={p.stem: {k: v for k, v in (jl(p) or {}).items() if k in ("all_equal", "A", "B")} | dict(files={f: v["status"] for f, v in (jl(p) or {}).get("files", {}).items()}) for p in sorted((RES / "regress_compare").glob("*.json"))},
              regression_status={t: status_lines(RES / f"regress_{t}/ALL_STATUS.txt") for t in ("pre", "post")},
              structural_check_365=jl(RES / "variants365/XB_LEDGER_CHECK_365.json"), variants_365_check=[l for l in status_lines(RES / "variants365/STATUS.txt") if l.startswith("CHECK_")],
              drill=jl(RES / "drill/DRILL_POSTPROC.json"), drill_status=status_lines(RES / "drill/DRILL_STATUS.txt"),
              wacc_fuel_bunker=dict(ledger_asean=dict(R1=ledger_asean("R1"), R10=ledger_asean("R10")), pool_prices=dict(R1=prices_asean("R1"), R10=prices_asean("R10")),
                                    variant_receipt_finance={k: v for k, v in ((jl(LIGHT / "variants/R10/integrated_wacccountry_365_24h_VARIANT_RECEIPT.json") or {}).get("ledgers", {}).get("finance") or {}).items() if k != "by_country"}),
              full_pack=dict(dir=str(FULL), tar_bytes=((FULL / "results_full_halted_20261023T174135Z.tar.gz").stat().st_size if (FULL / "results_full_halted_20261023T174135Z.tar.gz").exists() else None),
                             expected_bytes=1744049251, expected_sha256="46f1afbc87bea7e070d9ab8e950c22349ed3a30ae98e028ad7f29f437e2aa438",
                             sha256_file=((FULL / "results_full_halted_20261023T174135Z.tar.gz.sha256").read_text().split()[0] if (FULL / "results_full_halted_20261023T174135Z.tar.gz.sha256").exists() else None),
                             verify={k: v for k, v in (jl(FULL / "FULL_VERIFY.json") or {}).items() if k in ("full", "files", "bytes", "export_problems", "runs_with_exports")},
                             files=[p.name for p in FULL.iterdir()]),
              regression_365x24h=dict(dir="/home/jin/m10r_365", status=status_lines(Path("/home/jin/m10r_365/STATUS.txt")), nodal_prices_aligned=jl(Path("/home/jin/m10r_365/NODAL_PRICES_ALIGNED_CHECK.json")),
                                      runs={rid: dict(compare={k: v for k, v in (jl(Path(f"/home/jin/m10r_365/{rid}/COMPARE_VS_LIGHT.json")) or {}).items() if k in ("all_equal",)}
                                                     | dict(files={f: v["status"] for f, v in (jl(Path(f"/home/jin/m10r_365/{rid}/COMPARE_VS_LIGHT.json")) or {}).get("files", {}).items()}),
                                            ledger_redo={k: v for k, v in (jl(Path(f"/home/jin/m10r_365/{rid}/LEDGER_REDO.json")) or {}).items() if k in ("b16_before", "b16_after", "objective", "seconds")},
                                            fom_meta=((jl(Path(f"/home/jin/m10r_365/{rid}/LEDGER_IDENTITY.json")) or {}).get("diagnostics") or {}).get("existing_cross_border_fom_ledger"),
                                            m12_identity=(jl(Path(f"/home/jin/m10r_365/{rid}/ALLOCATION.json")) or {}).get("identity"))
                                            for rid in ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R10") if Path(f"/home/jin/m10r_365/{rid}").exists()}),
              written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), solver_runs_by_this_script=0)
    if a.tests and a.tests.exists():
        t = a.tests.read_text(errors="replace"); m = re.search(r"(\d+) passed(?:, (\d+) skipped)?", t)
        ev["tests"] = dict(log=str(a.tests), summary=(t.strip().splitlines()[-1] if t.strip() else None), passed=int(m.group(1)) if m else None, skipped=int(m.group(2) or 0) if m else None,
                           failed=(int(re.search(r"(\d+) failed", t).group(1)) if re.search(r"(\d+) failed", t) else 0))
    if a.dist and a.dist.exists():
        man = jl(a.dist / "PACKAGE_MANIFEST.json") or {}; v5 = jl(a.dist_v5 / "PACKAGE_MANIFEST.json") or {}
        same = {}
        for rel in ("networks/integrated_365_24h_unsolved.nc", "networks/disconnected_365_24h_unsolved.nc", "networks/integrated_BUILD_RECEIPT.json", "networks/disconnected_BUILD_RECEIPT.json",
                    "networks/integrated_costs_active_research.csv", "networks/disconnected_costs_active_research.csv", "EXPECTED_VARIANTS.json"):
            p6, p5 = a.dist / rel, a.dist_v5 / rel
            same[rel] = dict(v6=sha(p6) if p6.exists() else None, v5=sha(p5) if p5.exists() else None, equal=(p6.exists() and p5.exists() and sha(p6) == sha(p5)))
        ev["package_v6"] = dict(dist=str(a.dist), commit=man.get("commit"), files=len(man.get("files", [])), bytes=man.get("upload_total_bytes_excluding_this_manifest"),
                                manifest_sha256=sha(a.dist / "PACKAGE_MANIFEST.json"), sha256sums_sha256=man.get("sha256sums_sha256"), drill=man.get("drill"),
                                v5=dict(dist=str(a.dist_v5), commit=v5.get("commit"), files=len(v5.get("files", [])), bytes=v5.get("upload_total_bytes_excluding_this_manifest")),
                                same_as_v5=same, all_registered_inputs_equal=all(v["equal"] for v in same.values()))
    if a.dryrun and a.dryrun.exists():
        ev["dry_run_v6"] = {p.name: (p.read_text(errors="replace").splitlines()[-40:] if p.suffix in (".txt", ".out") else jl(p)) for p in sorted(a.dryrun.iterdir()) if p.is_file() and p.stat().st_size < 400000}
    a.out.write_text(json.dumps(ev, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(head=ev["worktree"]["head"][:8], commits=len(ev["worktree"]["commits"]), solves=ev["gurobi_local"]["used"], drill=(ev["drill"] or {}).get("all_types_ran"), tests=ev.get("tests", {}).get("summary"),
                          package=(ev.get("package_v6") or {}).get("all_registered_inputs_equal")), ensure_ascii=False))


if __name__ == "__main__":
    main()
