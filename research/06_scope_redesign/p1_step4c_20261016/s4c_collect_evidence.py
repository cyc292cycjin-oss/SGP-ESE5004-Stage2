"""Assemble S4C_EVIDENCE.json from the S4C receipts and tables (read-only; run inside WSL from the repo root after copying this folder to
research/06_scope_redesign/p1_step4c_20261016/).

    PYTHONHASHSEED=0 python research/06_scope_redesign/p1_step4c_20261016/s4c_collect_evidence.py [--dist /mnt/d/.../cloud_package_dist]
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RES = REPO / "results_project/s4c"
RI = REPO / "research_inputs"
EV = HERE / "evidence"
BASE = "819ade64"   # S4B final commit (PR #26 head) the S4C branch starts from


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
    return {str(p.relative_to(REPO)): dict(sha256=sha(p), bytes=p.stat().st_size) for p in sorted(d.rglob(pattern)) if p.is_file()} if d.exists() else {}


def lines(p):
    return Path(p).read_text().splitlines() if Path(p).exists() else None


def solve_dir(d):
    if not (d / "SOLVE_RECEIPT.json").exists():
        return None
    r = read(d / "SOLVE_RECEIPT.json"); g = opt(d / "V5_GATES.json")
    rec = {k: v for k, v in r.items() if k not in ("solver_parameters", "emissions_by_country", "co2_flows", "gap_table", "gates")}
    if "lp" in rec and isinstance(rec["lp"], dict):
        rec["lp"] = {k: v for k, v in rec["lp"].items() if k != "research_constraints"}
    drop = ("rows", "stores", "countries", "details", "terminals", "generators", "by_country", "checks", "metrics", "lp", "reconciliation", "known_constants", "budgets", "largest_ratio_checks",
            "worst_rows", "worst_columns", "worst_stationarity", "worst_dual_sign_rows", "worst_dual_sign_columns", "port_tonnes", "supply_mwh")
    gates = {k: ({kk: vv for kk, vv in v.items() if kk not in drop} if isinstance(v, dict) else v) for k, v in g.items()} if g else None
    return dict(receipt=rec, gates=gates, gap_table=opt(d / "GAP_TABLE.json"), bunker_account=opt(d / "BUNKER_ACCOUNT.json"),
                extra_asean=(opt(d / "CO2_FLOWS.json") or {}).get("extra_asean_by_country"), files={p.name: sha(p) for p in sorted(d.glob("*.json")) + sorted(d.glob("*.csv"))})


def builds(d):
    out = {}
    for b in sorted(Path(d).glob("*/*_BUILD_RECEIPT.json")):
        r = read(b)
        out[b.parent.name] = {k: r.get(k) for k in ["status", "scenario", "gap_diagnostic", "research_config_sha256", "code_sha", "build_seconds", "network", "daily_network"]}
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dist", type=Path, default=None); a = ap.parse_args()
    t0 = time.time()
    instr = HERE / "S4C_CLAUDE_CODE_INSTRUCTION.md"; sup = HERE / "S4C_SUPPLEMENT_01.md"
    ev = dict(stage="S4C", instruction=dict(file="S4C_CLAUDE_CODE_INSTRUCTION.md", sha256=sha(instr) if instr.exists() else None,
                                            expected=(HERE / "S4C_INSTRUCTION_SHA256.txt").read_text().split()[0] if (HERE / "S4C_INSTRUCTION_SHA256.txt").exists() else None),
              supplement_01=dict(file="S4C_SUPPLEMENT_01.md", sha256=sha(sup) if sup.exists() else None,
                                 expected=(HERE / "S4C_SUPPLEMENT_01_SHA256.txt").read_text().split()[0] if (HERE / "S4C_SUPPLEMENT_01_SHA256.txt").exists() else None),
              decisions="82-90 (+ supplement 01: decision 16)", branch=git(["branch", "--show-current"]), head=git(["rev-parse", "HEAD"]), base=BASE,
              commits=git(["log", "--oneline", f"{BASE}..HEAD"]).splitlines(),
              label="SMOKE_TEST_ONLY results have no scientific meaning before the cloud run (decision 47)")
    for k in ["s4c_0", "s4c_1", "s4c_2", "s4c_3", "s4c_4"]:
        ev[k] = dict(builds=opt(EV / k / f"{k.upper().replace('_', '')}_BUILDS.json"), files=files(EV / k))
    ev["s4c_1"]["audit_summary"] = opt(EV / "s4c_1/audit_integrated/COST_AUDIT_S4C1_SUMMARY.json")
    ev["s4c_3"]["bunker_summary"] = opt(EV / "s4c_3/BUNKER_ATTRIBUTION_S4C3_SUMMARY.json")
    ev["s4c_3"]["config_key_check"] = {p.name: {kk: vv for kk, vv in read(p).items() if kk in ("label", "unaffected", "static", "series", "costs_active_research", "research_config", "key_values")}
                                       for p in sorted((EV / "s4c_3/config_key_check").glob("*.json"))}
    s5 = RES / "s4c5"
    ev["s4c_5"] = dict(status=lines(s5 / "STATUS.txt"), builds=builds(s5 / "builds"), solves={t: solve_dir(s5 / f"solves/{t}") for t in ["A_kvl_off", "A", "B", "C"]},
                       comparison=opt(s5 / "analysis/S4C5_COMPARISON.json"), files=files(EV / "s4c_5"))
    s6 = RES / "s4c6"
    summ = opt(s6 / "analysis/S4C6_SMOKE_SUMMARY.json") or {}
    ev["s4c_6"] = dict(status=lines(s6 / "STATUS.txt"), builds=builds(s6 / "builds"),
                       solves={f"{s}/{t}": solve_dir(s6 / f"solves_{s}/{t}") for s in ["main", "control"] for t in ["integrated", "disconnected", "integrated_nze", "disconnected_gap"] if (s6 / f"solves_{s}/{t}").exists()},
                       summary={s: {k: v for k, v in R.items() if k.startswith(("runs", "gates", "B5", "B6", "asean_", "lng_", "bunker_account", "co2_flows", "net_exports"))} for s, R in (summ.get("sets") or {}).items()},
                       files=files(EV / "s4c_6"))
    dist = a.dist
    ev["cloud_package"] = dict(estimate=dict(file="CLOUD_RESOURCE_ESTIMATE.md", sha256=sha(HERE / "CLOUD_RESOURCE_ESTIMATE.md") if (HERE / "CLOUD_RESOURCE_ESTIMATE.md").exists() else None),
                               deploy_steps=dict(file="CLOUD_DEPLOY_STEPS.md", sha256=sha(HERE / "CLOUD_DEPLOY_STEPS.md") if (HERE / "CLOUD_DEPLOY_STEPS.md").exists() else None),
                               package_scripts=files(HERE / "cloud_package"),
                               package_manifest=(opt(dist / "PACKAGE_MANIFEST.json") if dist else None), package_sha256sums=(lines(dist / "SHA256SUMS") if dist else None))
    ev["downloads"] = dict(co2_category_1=lines(EV / "s4c_4/DOWNLOAD_LOG_S4C4.tsv"), finance_category_2="see S4C_PROGRESS.md download table (0.58 MB)")
    ev["registry"] = dict(fragments={f: sha(RI / "registry_v5/fragments" / f) for f in [f"s4c_{i}.csv" for i in range(5)] if (RI / "registry_v5/fragments" / f).exists()},
                          data_registry_sha256=sha(RI / "registry_v5/DATA_REGISTRY.csv"), d1_evidence_counts=(opt(RI / "registry_v5/D1_EVIDENCE.json") or {}).get("counts"))
    ev["tests"] = lines(EV / "TESTS_FULL_SUITE_FINAL.txt")
    ev["deliverables"] = files(HERE, "*.md") | files(HERE, "*.csv") | files(HERE, "*.py")
    ev["collector_seconds"] = round(time.time() - t0, 1)
    (HERE / "S4C_EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=str))
    print("S4C_EVIDENCE.json", (HERE / "S4C_EVIDENCE.json").stat().st_size, "bytes")


if __name__ == "__main__":
    main()
