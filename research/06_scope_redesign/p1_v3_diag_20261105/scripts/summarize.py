"""V3 DIAG: lightweight evidence summary (V3_DIAG_EVIDENCE.json) from evidence/ - Gurobi call ledger, window verdicts, deletion filter, bunker
structure, annual right-hand sides, build resources. Reads only files written by this diagnosis. Python stdlib only.

    python summarize.py <work folder>
"""
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def t(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def main(work):
    W = Path(work); E = W / "evidence"
    calls = list(csv.DictReader(open(E / "GUROBI_CALLS.csv")))
    secs = [(t(c["end_utc"]) - t(c["start_utc"])).total_seconds() for c in calls]
    status = (E / "DIAG_STATUS.txt").read_text().splitlines()
    builds = {}
    for ln in status:
        m = re.match(r"BUILD_END:([^:]+):exit=(\d+):(\d+)s:peak_gib=([\d.]+):lp_bytes=(\d+)", ln)
        if m:
            builds[m.group(1)] = dict(exit=int(m.group(2)), seconds=int(m.group(3)), peak_gib=float(m.group(4)), lp_bytes=int(m.group(5)))
    verdict = {}
    for c in calls:
        log = E / "runs" / c["id"] / "gurobi_log_scrubbed.txt"
        txt = log.read_text(errors="ignore") if log.exists() else ""
        if re.search(r"infeasible or unbounded", txt, re.I):
            v = "INF_OR_UNBD"
        elif re.search(r"^Presolved:", txt, re.M):
            v = "PRESOLVE_PASSED"
        elif c["kind"] == "iis":
            v = "IIS_TIME_LIMIT_NO_IIS"
        else:
            v = c["status"] or "UNDECIDED"
        win = {}
        wf = E / "runs" / c["id"] / "DIAG_WINDOW.json"
        if not wf.exists():
            base = re.sub(r"_(dr0|nf3|agg0|pre1|iis|del_\w+|reform|rhs1)$", "", c["id"]); wf = E / "runs" / base / "DIAG_WINDOW.json"
        if wf.exists():
            d = json.loads(wf.read_text())
            win = dict(start=d["window_start"], end_excl=d["window_end_excl"], first=d["first_snapshot"], last=d["last_snapshot"], weighting=d.get("weighting", "runner TRUNCATE (set_representative_weights, 8760/len)"),
                       weight_h=(d.get("weights_after_main") or {}).get("objective", {}).get("per_snapshot_max"))
        verdict[c["id"]] = dict(call=int(c["call"]), kind=c["kind"], verdict=v, presolve_s=c["presolve_s"] or None, wall_s=(t(c["end_utc"]) - t(c["start_utc"])).total_seconds(),
                                extra=c["extra"].strip(), window=win)
    out = dict(instruction="V3_DIAG_INSTRUCTION.md v1 sha256 e6f4c06c7ee4dfd41d3e7834b01b8a3c1d0d61c964233494616bb1e2edfe4d05", code_commit="7d22dda112a3c18ed57e8c061d95e51915980417",
               gurobi_calls=dict(count=len(calls), limit=40, wall_seconds_total=sum(secs), wall_seconds_max=max(secs), by_kind={k: sum(1 for c in calls if c["kind"] == k) for k in sorted({c["kind"] for c in calls})}),
               calls=verdict, builds=builds,
               network_sha256=(E / "network_sha256_check.txt").read_text().splitlines(),
               control_equivalence=(E / "CONTROL_EQUIVALENCE.txt").read_text().splitlines(),
               bunker_static=json.loads((E / "BUNKER_STATIC_F1_F4.json").read_text()),
               annual_rhs_f1={k: v for k, v in json.loads((E / "ANNUAL_RHS_F1.json").read_text()).items() if k in ("research_country_net_zero", "research_co2_storage_cap", "external_annual_caps", "bunker_stores", "weights")})
    (W / "V3_DIAG_EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(out["gurobi_calls"]))
    for k, v in verdict.items():
        w = v["window"]
        print(f'{v["call"]:>2} {k:<20} {v["kind"]:<9} {v["verdict"]:<22} pre={v["presolve_s"]} wall={v["wall_s"]:.0f}s win={w.get("start")}-{w.get("end_excl")} w={w.get("weight_h")} {v["extra"][:70]}')


if __name__ == "__main__":
    main(sys.argv[1])
