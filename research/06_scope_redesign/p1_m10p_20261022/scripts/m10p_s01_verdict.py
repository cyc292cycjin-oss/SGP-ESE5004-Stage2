"""M10P supplement 01 item 5 and section 2 (read only): evidence that the instance never reads the top-level research/ folder, and the second dry
run against the first one (package eac6c3e0, research/ included).

    python m10p_s01_verdict.py builds <first dry run build_only dir> <second dry run build_only dir> <out json>
    python m10p_s01_verdict.py trace <out json> <trace log> [...]
    python m10p_s01_verdict.py verdict <static raw json> <trace json> <builds json> <out json>
"""
import json
import sys
from collections import Counter
from pathlib import Path

RUNS = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11"]
# Hand classification of every hit of m10p_s01_static_research.py (module, line) -> (on the run path?, how the value is used)
CLASSIFIED = {
    ("gate5_resources.py", 15): (False, "opened by gate5_resources.current_evidence(); its callers (gate5_cloud_preflight, gate5_memory_preflight, run_gate5_stable_inventory, "
                                        "test_gate5_resources, test_gate5_cloud_resources) are outside the import closure of the run entries; the closure imports only sha() and budget-type helpers"),
    ("run_gate6_baseline.py", 50): (False, "opened by run_gate6_baseline.make_lock(), called only by the Gate6 runner's own functions (lines 64, 95); the closure reaches the module "
                                           "only for resource_admission() inside gate6_execution_context.claim_execution (Gate6 execution, not used by the third batch)"),
    ("s1_solve.py", 18): (False, "label D5_SOURCE written into s1_solve receipts as parameter_source; never opened"),
    ("s4o_c1_precision.py", 44): (False, "label of the default C1 reference (L23_REFERENCE.source); the values are inline (L23_DIFF_BN); never opened"),
    ("gates_v6.py", 225): (False, "label definition.file of V6_ACCEPTANCE.json next to the constant GATES_V6_SHA256; never opened"),
}
DOCSTRING_LINE = 1


def builds(first: Path, second: Path, out: Path):
    rows, ok = {}, True
    for rid in RUNS:
        a, b = json.loads((first / rid / "BUILD_CHECK.json").read_text()), json.loads((second / rid / "BUILD_CHECK.json").read_text())
        eq = dict(passed=b["passed"], lp_equal=a["lp"]["num_row"] == b["lp"]["num_row"] and a["lp"]["num_col"] == b["lp"]["num_col"] and a["lp"]["nnz"] == b["lp"]["nnz"],
                  parameters_equal=a["parameters"] == b["parameters"], network_sha256_equal=a["network_sha256"] == b["network_sha256"], profile_equal=a["profile"] == b["profile"])
        ok &= all(eq.values())
        rows[rid] = dict(checks=eq, lp=b["lp"], first_lp=a["lp"], peak_rss_gib=round(b["peak_rss_gib"], 2), network_sha256=b["network_sha256"])
    res = dict(note="second dry run (code archive without research/) vs the first (package eac6c3e0 with research/): BUILD_CHECK passed, LP rows / columns / nonzeros, "
                    "solver parameters, input network SHA256 and profile identical per run", all_equal=ok, runs=rows)
    out.write_text(json.dumps(res, indent=1) + "\n"); print(json.dumps(dict(all_equal=ok)))


def trace(out: Path, logs):
    res = {}
    for lg in logs:
        lines = [x.split("\t") for x in Path(lg).read_text().splitlines()] if Path(lg).exists() else []
        research = [x for x in lines if x[0] == "RESEARCH"]; local = [x for x in lines if x[0] == "LOCAL"]
        pref = Counter("/".join(x[2].split("/")[:5]) for x in local)
        res[Path(lg).name] = dict(lines=len(lines), research_accesses=len(research), research_paths=sorted({x[2] for x in research})[:50],
                                  research_by_script=dict(Counter(Path(x[3]).name for x in research)), local_accesses=len(local),
                                  local_by_prefix=dict(pref.most_common(30)), local_by_kind=dict(Counter(x[1] for x in local)),
                                  local_scripts=dict(Counter(Path(x[3]).name for x in local).most_common(20)))
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: dict(research=v["research_accesses"], local=v["local_accesses"]) for k, v in res.items()}))


def verdict(raw: Path, tr: Path, bd: Path, out: Path):
    s, t, b = json.loads(raw.read_text()), json.loads(tr.read_text()), json.loads(bd.read_text())
    hits = []
    for h in s["hits"]:
        key = (Path(h["module"]).name, h["line"])
        if h["kind"] in ("literal_research_path", "path_join_research"):
            if key in CLASSIFIED:
                on_path, why = CLASSIFIED[key]
            elif h["line"] == DOCSTRING_LINE:
                on_path, why = False, "module docstring"
            else:
                on_path, why = None, "NOT CLASSIFIED"
            hits.append(dict(h, on_run_path=on_path, use=why))
    unclassified = [h for h in hits if h["on_run_path"] is None]
    control = t.get("TRACE_control.log", {}).get("research_accesses", 0)
    dyn = {k: v["research_accesses"] for k, v in t.items() if k != "TRACE_control.log"}
    ok = not unclassified and not any(h["on_run_path"] for h in hits) and control > 0 and all(v == 0 for v in dyn.values()) and b["all_equal"]
    res = dict(question="supplement 01 item 5: does the run time read the top-level research/ folder?", answer=("no" if ok else "see details"),
               research_files_to_keep=[], static=dict(entries=s["entries"], closure_size=s["closure_size"], research_hits=hits,
                                                      other_hits=s["hit_counts"], config_values_used_by_closure=[c for c in s["config_files_with_research_values_used_by_closure"] if c["used_by"]],
                                                      note="config gate6_baseline_3h.json (research/04_model_assembly paths) is read only by run_gate6_baseline.py (Gate6); absolute paths and dynamic imports are listed in the raw file (none points into research/)"),
               dynamic=dict(tracer_positive_control_accesses=control, research_accesses_by_step=dyn, note="package unpacked without research/; every Python process of preflight, BUILD_ONLY and POST_ONLY ran with the access trace"),
               dry_run_equality=dict(all_equal=b["all_equal"], note=b["note"]), passed=ok)
    out.write_text(json.dumps(res, indent=1) + "\n"); print(json.dumps(dict(answer=res["answer"], unclassified=len(unclassified), control=control, dynamic=dyn, builds_equal=b["all_equal"])))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "builds":
        builds(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    elif cmd == "trace":
        trace(Path(sys.argv[2]), sys.argv[3:])
    else:
        verdict(*map(Path, sys.argv[2:6]))
