"""Assemble S4B_EVIDENCE.json from the S4B receipts and tables (read-only; run inside WSL from the repo root).

    PYTHONHASHSEED=0 python research/06_scope_redesign/p1_step4b_20261016/s4b_collect_evidence.py [--dist /mnt/d/.../cloud_package_dist]
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RES = REPO / "results_project/s4b"
RI = REPO / "research_inputs"
EV = HERE / "evidence"
BASE = "a58ca3fa"   # S4A final commit (PR #25 head) the S4B branch starts from


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def opt(p):
    return read(p) if Path(p).exists() else None


def git(cmd):
    return subprocess.run(["git"] + cmd, cwd=REPO, capture_output=True, text=True).stdout.strip()


def files(d, pattern="*"):
    d = Path(d)
    return {str(p.relative_to(REPO)): dict(sha256=sha(p), bytes=p.stat().st_size) for p in sorted(d.glob(pattern)) if p.is_file()} if d.exists() else {}


def lines(p):
    return Path(p).read_text().splitlines() if Path(p).exists() else None


def solve_dir(d):
    if not (d / "SOLVE_RECEIPT.json").exists():
        return None
    r = read(d / "SOLVE_RECEIPT.json"); g = opt(d / "V5_GATES.json")
    rec = {k: v for k, v in r.items() if k not in ("solver_parameters", "emissions_by_country", "co2_flows", "gap_table", "scaling", "gates")}
    if "lp" in rec and isinstance(rec["lp"], dict):
        rec["lp"] = {k: v for k, v in rec["lp"].items() if k != "research_constraints"}
    drop = ("rows", "stores", "countries", "details", "terminals", "generators", "by_country", "checks", "metrics", "lp", "reconciliation", "known_constants", "budgets", "largest_ratio_checks")
    gates = {k: ({kk: vv for kk, vv in v.items() if kk not in drop} if isinstance(v, dict) else v) for k, v in g.items()} if g else None
    return dict(receipt=rec, gates=gates, gap_table=opt(d / "GAP_TABLE.json"), files={p.name: sha(p) for p in sorted(d.glob("*.json")) + sorted(d.glob("*.csv"))})


def builds(d):
    out = {}
    for b in sorted(Path(d).glob("*/*_BUILD_RECEIPT.json")):
        r = read(b)
        out[b.parent.name] = {k: r.get(k) for k in ["status", "scenario", "gap_diagnostic", "research_config_sha256", "code_sha", "build_seconds", "network", "daily_network"]}
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dist", type=Path, default=None); a = ap.parse_args()
    t0 = time.time()
    instr = HERE / "S4B_CLAUDE_CODE_INSTRUCTION.md"
    ev = dict(stage="S4B", instruction=dict(file="work/p1_step4b_20261016/S4B_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(instr) if instr.exists() else None,
                                            expected=(HERE / "S4B_INSTRUCTION_SHA256.txt").read_text().split()[0] if (HERE / "S4B_INSTRUCTION_SHA256.txt").exists() else None),
              decisions="70-81", branch=git(["branch", "--show-current"]), head=git(["rev-parse", "HEAD"]), base=BASE,
              commits=git(["log", "--oneline", f"{BASE}..HEAD"]).splitlines(),
              label="SMOKE_TEST_ONLY results have no scientific meaning before the cloud run (decision 47)")
    # S4B-0 (decisions 70-73)
    s0 = RES / "s4b0"
    ev["s4b_0"] = dict(sector_switches=dict(file="research_inputs/sector_v5/SECTOR_SWITCHES_VS_PYPSA_EUR.csv", sha256=sha(RI / "sector_v5/SECTOR_SWITCHES_VS_PYPSA_EUR.csv")),
                       status=lines(s0 / "STATUS.txt"), builds=builds(s0 / "builds"),
                       solves={sc: solve_dir(s0 / f"solves/{sc}") for sc in ["integrated", "disconnected", "disconnected_gap"]},
                       structural_gap=opt(s0 / "analysis/S4B0_STRUCTURAL_GAP_ANNUAL.json"),
                       reevaluation={p.name: sha(p) for p in sorted((EV / "s4b_0/reeval").glob("*.json"))}, files=files(EV / "s4b_0/analysis/integrated_s4b0"))
    # S4B-1 (decision 77)
    ev["s4b_1"] = dict(evidence=opt(EV / "s4b_1/FLEET_S4B1_EVIDENCE.json"), build_resources=lines(EV / "s4b_1/build_resources.txt"), files=files(EV / "s4b_1"))
    # S4B-2 (decisions 78, 79)
    ev["s4b_2"] = dict(evidence=opt(EV / "s4b_2/CANDIDATE_CAPS_S4B2_EVIDENCE.json"), build_resources=lines(EV / "s4b_2/build_resources.txt"), files=files(EV / "s4b_2"))
    # S4B-3 (decisions 74, 75)
    ev["s4b_3"] = dict(calibration=opt(EV / "s4b_3/WIND_CALIBRATION_S4B3.json"), manifest=opt(RI / "renewable_v5/MANIFEST.json"),
                       build_resources=lines(EV / "s4b_3/build_resources.txt"), profile_rebuild_resources=lines(EV / "s4b_3/profile_rebuild_resources.txt"), files=files(EV / "s4b_3"))
    # S4B-4 (decision 76)
    ev["s4b_4"] = dict(exposure=opt(EV / "s4b_4/TYPHOON_EXPOSURE_S4B4.json"), build_check=lines(EV / "s4b_4/build_check.txt"), run_resources=lines(EV / "s4b_4/typhoon_run_resources.txt"), files=files(EV / "s4b_4"))
    # S4B-5
    s5 = RES / "s4b5"
    summ = opt(s5 / "analysis/S4B5_SMOKE_SUMMARY.json") or {}
    ev["s4b_5"] = dict(status=lines(s5 / "STATUS.txt"), builds=builds(s5 / "builds"),
                       solves={sc: solve_dir(s5 / f"solves/{sc}") for sc in ["integrated", "disconnected", "disconnected_gap", "integrated_gap"]},
                       run_table=summ.get("runs"), gates=summ.get("gates"), B5_trial={k: v for k, v in (summ.get("B5_trial") or {}).items()}, B6_trial=summ.get("B6_trial"),
                       slack_cost_disconnected_gap=summ.get("slack_cost_disconnected_gap"), integrated_gap_vs_main=summ.get("integrated_gap_vs_main"),
                       asean_integrated=summ.get("asean_integrated"), net_exports_twh_integrated=summ.get("net_exports_twh_integrated"),
                       structural_gap=opt(s5 / "analysis/S4B5_STRUCTURAL_GAP_ANNUAL.json"), files=files(EV / "s4b_5/analysis"))
    # S4B-6
    dist = a.dist
    ev["s4b_6"] = dict(estimate=dict(file="CLOUD_RESOURCE_ESTIMATE.md", sha256=sha(HERE / "CLOUD_RESOURCE_ESTIMATE.md") if (HERE / "CLOUD_RESOURCE_ESTIMATE.md").exists() else None),
                       deploy_steps=dict(file="CLOUD_DEPLOY_STEPS.md", sha256=sha(HERE / "CLOUD_DEPLOY_STEPS.md") if (HERE / "CLOUD_DEPLOY_STEPS.md").exists() else None),
                       package_scripts=files(HERE / "cloud_package"),
                       package_manifest=(opt(dist / "PACKAGE_MANIFEST.json") if dist else None), package_sha256sums=(lines(dist / "SHA256SUMS") if dist else None))
    # downloads, registry, tests
    ev["downloads"] = lines(HERE / "sources_s4b/SOURCES_S4B.csv")
    ev["registry"] = dict(fragments={f: sha(RI / "registry_v5/fragments" / f) for f in [f"s4b_{i}.csv" for i in range(5)] if (RI / "registry_v5/fragments" / f).exists()},
                          data_registry_sha256=sha(RI / "registry_v5/DATA_REGISTRY.csv"), data_pending_list_sha256=sha(RI / "registry_v5/DATA_PENDING_LIST.csv"),
                          d1_evidence_counts=(opt(RI / "registry_v5/D1_EVIDENCE.json") or {}).get("counts"))
    ev["tests"] = lines(EV / "s4b_5/pytest_summary.txt")
    ev["deliverables"] = files(HERE, "*.md") | files(HERE, "*.csv") | files(HERE, "*.py")
    ev["collector_seconds"] = round(time.time() - t0, 1)
    (HERE / "S4B_EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=str))
    print("S4B_EVIDENCE.json", (HERE / "S4B_EVIDENCE.json").stat().st_size, "bytes")


if __name__ == "__main__":
    main()
