"""Assemble S4A_EVIDENCE.json from the S4A receipts and tables (read-only; run inside WSL from the repo root).

    PYTHONHASHSEED=0 python research/06_scope_redesign/p1_step4_20261016/s4a_collect_evidence.py
"""
from pathlib import Path
import hashlib, json, subprocess, time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RES = REPO / "results_project/s4a"
RI = REPO / "research_inputs"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def opt(p):
    return read(p) if Path(p).exists() else None


def git(cmd):
    return subprocess.run(["git"] + cmd, cwd=REPO, capture_output=True, text=True).stdout.strip()


def files(d, pattern="*"):
    d = Path(d)
    return {str(p.relative_to(REPO)): dict(sha256=sha(p), bytes=p.stat().st_size) for p in sorted(d.glob(pattern)) if p.is_file()} if d.exists() else {}


def solve_dir(d):
    if not (d / "SOLVE_RECEIPT.json").exists():
        return None
    r = read(d / "SOLVE_RECEIPT.json"); g = opt(d / "V5_GATES.json")
    rec = {k: v for k, v in r.items() if k not in ("solver_parameters", "emissions_by_country", "co2_flows", "gap_table", "scaling")}
    if "lp" in rec and isinstance(rec["lp"], dict):
        rec["lp"] = {k: v for k, v in rec["lp"].items() if k != "research_constraints"}
    gates = {k: ({kk: vv for kk, vv in v.items() if kk not in ("rows", "stores", "countries", "details", "terminals", "generators", "by_country", "checks", "metrics", "lp", "reconciliation", "known_constants")} if isinstance(v, dict) else v) for k, v in g.items()} if g else None
    return dict(receipt=rec, gates=gates, gate_b1_countries=(g or {}).get("B1", {}).get("countries"), files={p.name: sha(p) for p in sorted(d.glob("*.json")) + sorted(d.glob("*.csv"))})


def main():
    t0 = time.time()
    ev = dict(stage="S4A", instruction="work/p1_step4_20261016/S4A_CLAUDE_CODE_INSTRUCTION.md + S4A_RESUME_01.md", decisions="70-73", ledger=["L14", "L15", "L16"],
              branch=git(["branch", "--show-current"]), head=git(["rev-parse", "HEAD"]), commits=git(["log", "--oneline", "05be057c..HEAD"]).splitlines(),
              label="SMOKE_TEST_ONLY results have no scientific meaning before the cloud run (decision 47)")
    # S4A-0 / resume 01: cutout
    ev["cutout"] = opt(HERE / "evidence/s4a_1/S4A_CUTOUT_CHECK.json")
    # S4A-1
    ev["s4a_1"] = dict(manifest=opt(RI / "renewable_v5/MANIFEST.json"), evidence=opt(RI / "renewable_v5/RENEWABLE_S4A_EVIDENCE.json"),
                       comparison_overall={k: v.get("overall") for k, v in (opt(HERE / "evidence/s4a_1/S4A_PROFILE_COMPARISON.json") or {}).items() if isinstance(v, dict) and "overall" in v},
                       method_validation=opt(HERE / "evidence/s4a_1/S4A_PROFILE_METHOD_VALIDATION_TUTORIAL_WEEK_v2.json"),
                       rebuild_resources=(HERE / "evidence/s4a_1/profile_rebuild_resources.txt").read_text().splitlines() if (HERE / "evidence/s4a_1/profile_rebuild_resources.txt").exists() else None,
                       files=files(RI / "renewable_v5") | files(HERE / "evidence/s4a_1"))
    # S4A-2
    ev["s4a_2"] = dict(evidence=opt(RI / "fleet_v5/FLEET_S4A_EVIDENCE.json"), gas_allocation_old_vs_new=opt(HERE / "evidence/s4a_2/GAS_PRODUCTION_ALLOCATION_OLD_VS_NEW.json"), files=files(RI / "fleet_v5"))
    # S4A-3
    p3 = opt(RI / "potentials_v5/POTENTIALS_S4A_EVIDENCE.json") or {}
    ev["s4a_3"] = dict(rows=p3.get("rows"), status_counts=p3.get("status_counts"), documents=p3.get("documents"), comparison=p3.get("comparison"), cost_consistency=p3.get("cost_consistency"), files=files(RI / "potentials_v5"))
    # S4A-4
    sm = RES / "smoke"
    st = (sm / "STATUS.txt").read_text().splitlines() if (sm / "STATUS.txt").exists() else None
    builds = {}
    for sc in ["integrated", "disconnected"]:
        b = opt(sm / f"builds/{sc}/{sc}_BUILD_RECEIPT.json")
        if b:
            builds[sc] = {k: b.get(k) for k in ["status", "scenario", "research_config_sha256", "code_sha", "build_seconds", "network"]}
    ev["s4a_4"] = dict(status=st, builds=builds, solves={sc: solve_dir(sm / f"solves/{sc}") for sc in ["integrated", "disconnected"]},
                       compare=opt(sm / "analysis/integrated/S4A_SMOKE_COMPARE.json"), files=files(sm / "analysis/integrated", "*.csv"))
    # registry
    ev["registry"] = dict(fragments={f: sha(RI / "registry_v5/fragments" / f) for f in ["renewable_s4a.csv", "fleet_s4a.csv", "potentials_s4a.csv"] if (RI / "registry_v5/fragments" / f).exists()},
                          data_registry_sha256=sha(RI / "registry_v5/DATA_REGISTRY.csv"), data_pending_list_sha256=sha(RI / "registry_v5/DATA_PENDING_LIST.csv"),
                          d1_evidence_counts=(opt(RI / "registry_v5/D1_EVIDENCE.json") or {}).get("counts"))
    ev["deliverables"] = files(HERE, "*.md") | files(HERE, "*.csv") | files(HERE, "*.py")
    ev["collector_seconds"] = round(time.time() - t0, 1)
    (HERE / "S4A_EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=str))
    print("S4A_EVIDENCE.json", (HERE / "S4A_EVIDENCE.json").stat().st_size, "bytes")


if __name__ == "__main__":
    main()
