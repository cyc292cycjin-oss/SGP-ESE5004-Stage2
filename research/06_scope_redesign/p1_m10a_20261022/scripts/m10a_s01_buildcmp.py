"""M10A supplement 01 D4: compare the v5 BUILD_ONLY dry run with the M10P supplement 01 second dry run (package v3) run by run:
LP dimensions, solver parameters (TimeLimit excepted: 21,600 -> 28,800), input network SHA256, registered SHA256, LP array bytes, BUILD_CHECK passed.
    python m10a_s01_buildcmp.py <v5 build_only dir> <s01 build_only dir> <out json>
"""
import json
import sys
from pathlib import Path

new, old, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
rows, all_ok = {}, True
for rid in [f"R{i}" for i in range(1, 12)]:
    a, b = new / rid, old / rid
    bc_a, bc_b = json.loads((a / "BUILD_CHECK.json").read_text()), json.loads((b / "BUILD_CHECK.json").read_text())
    run_a, run_b = json.loads((a / "RUN.json").read_text()), json.loads((b / "RUN.json").read_text())
    pa, pb = dict(bc_a["parameters"]), dict(bc_b["parameters"])
    tl_a, tl_b = pa.pop("TimeLimit"), pb.pop("TimeLimit")
    lp_bytes = [(p / "lp_bytes.txt").read_text().strip() if (p / "lp_bytes.txt").exists() else None for p in (a, b)]
    dims = ("num_row", "num_col", "nnz")
    r = dict(lp_equal=all(bc_a["lp"][k] == bc_b["lp"][k] for k in dims), lp={k: bc_a["lp"][k] for k in dims}, parameters_equal_except_timelimit=pa == pb, parameters=pa, timelimit=[tl_a, tl_b],
             timelimit_ok=(tl_a == 28800.0 and tl_b == 21600.0), network_sha256_equal=bc_a["network_sha256"] == bc_b["network_sha256"], network_sha256=bc_a["network_sha256"],
             registered_sha256_equal=run_a["registered_sha256"] == run_b["registered_sha256"], lp_bytes=lp_bytes, lp_bytes_equal=lp_bytes[0] == lp_bytes[1],
             passed=[bc_a["passed"], bc_b["passed"]], wall_cap=[run_a.get("wall_cap_s"), run_b.get("wall_cap_s")], time_limit_run_json=[run_a.get("time_limit"), run_b.get("time_limit")],
             peak_rss_gib=[round(bc_a["peak_rss_gib"], 2), round(bc_b["peak_rss_gib"], 2)], build_seconds=[bc_a["lp"]["build_seconds"], bc_b["lp"]["build_seconds"]])
    ok = r["lp_equal"] and r["parameters_equal_except_timelimit"] and r["timelimit_ok"] and r["network_sha256_equal"] and r["registered_sha256_equal"] and r["lp_bytes_equal"] and all(r["passed"]) \
        and r["wall_cap"] == [30000, 22500] and r["time_limit_run_json"] == [28800.0, 21600.0]
    r["all_equal_except_timelimit"] = ok; all_ok &= ok
    rows[rid] = r
res = dict(note="v5 BUILD_ONLY (M10A supplement 01) vs v3 BUILD_ONLY (M10P supplement 01 S01-3); TimeLimit / wall cap differ by design (D1)", all_equal_except_timelimit=all_ok, runs=rows)
out.write_text(json.dumps(res, indent=1))
print(json.dumps(dict(all_equal_except_timelimit=all_ok, runs={k: dict(lp=v["lp_equal"], par=v["parameters_equal_except_timelimit"], tl=v["timelimit"], sha=v["network_sha256_equal"], bytes=v["lp_bytes_equal"], passed=v["passed"]) for k, v in rows.items()}), indent=1))
sys.exit(0 if all_ok else 1)
