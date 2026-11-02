"""Supplement 01 item 8: the two runners read a package BATCH_DEF.json; without it nothing changes."""
import re
W = "/home/jin/wt_v3_20261102/"; P = W + "research/06_scope_redesign/"
EXPORT = 'unset BATCH_DEF; if [ -f "$HERE/BATCH_DEF.json" ]; then export BATCH_DEF="$HERE/BATCH_DEF.json"; fi   # V3 supplement 01: registered batch definition of this package (scripts_project/batch_def.py); without it the v2 tables apply\n'


def sub(path, pairs):
    s = open(path, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:70], s.count(a))
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="").write(s)


# ---- python modules
sub(W + "scripts_project/dfx_batch.py", [
    ('from m10_batch3_summary import COUNTRIES, bn, jl, ledger_totals, owen_main, postproc_errors, sha, unusable_runs  # noqa: E402\n',
     'from m10_batch3_summary import COUNTRIES, bn, jl, ledger_totals, owen_main, postproc_errors, sha, unusable_runs  # noqa: E402\nfrom batch_def import input_receipt, load_def  # noqa: E402\n'),
    ('BUILD_COMMIT = "72083fde6bffd89580869af6dd00885a8d76721f"\n',
     'BUILD_COMMIT = "72083fde6bffd89580869af6dd00885a8d76721f"\n_DEF = load_def()   # V3 supplement 01: the package definition replaces the v2 table and registered inputs; limits and schedule stay\nif _DEF:\n    RUNS, REGISTERED_SHA, REGISTERED_BYTES, BUILD_COMMIT = _DEF["runs"], _DEF["registered_sha"], _DEF["registered_bytes"], _DEF["build_commit"]\n'),
    ('''    for sc in ("integrated", "disconnected"):
        f = nets / f"{sc}_365_24h_unsolved.nc"; rec = jl(nets / f"{sc}_BUILD_RECEIPT.json") or {}; daily = rec.get("daily_network") or {}
        have = sha(f) if f.exists() else None; size = f.stat().st_size if f.exists() else None
''', '''    for run in RUNS.values():
        f = nets / f"{run['base']}_unsolved.nc"; rc = input_receipt(nets, run, "daily_network", BUILD_COMMIT)
        have = sha(f) if f.exists() else None; size = f.stat().st_size if f.exists() else None
'''),
    ('''        rec_ok = bool(have) and have == daily.get("sha256") and rec.get("code_sha") == BUILD_COMMIT and int(daily.get("snapshots") or 0) == 365
        rows[f.name] = dict(file=str(f), bytes=size, sha256=have, receipt_sha256=daily.get("sha256"), receipt_snapshots=daily.get("snapshots"), receipt_code_sha=rec.get("code_sha"),
''', '''        rec_ok = bool(have) and have == rc["sha256"] and rc["chain_ok"] and int(rc["snapshots"] or 0) == 365
        rows[f.name] = dict(file=str(f), bytes=size, sha256=have, receipt_sha256=rc["sha256"], receipt_snapshots=rc["snapshots"], receipt_code_sha=rc["code_sha"],
'''),
    ('g = gate_b6_cost(float(i["objective"]), float(d["objective"]), "integrated", "disconnected")\n    return dict(g, b6_bn=bn(g["difference"]), runs=dict(integrated="V1", disconnected="V2")',
     'g = gate_b6_cost(float(i["objective"]), float(d["objective"]), RUNS["V1"]["scenario"], RUNS["V2"]["scenario"])\n    return dict(g, b6_bn=bn(g["difference"]), runs=dict(integrated="V1", disconnected="V2")'),
])
sub(W + "scripts_project/b4_batch4.py", [
    ('from m10_batch3_summary import COUNTRIES, ITER, bn, jl, ledger_totals, owen_main, postproc_errors, sha, unusable_runs   # noqa: E402\n',
     'from m10_batch3_summary import COUNTRIES, ITER, bn, jl, ledger_totals, owen_main, postproc_errors, sha, unusable_runs   # noqa: E402\nfrom batch_def import input_receipt, load_def   # noqa: E402\n'),
    ('BUILD_COMMIT = "72083fde6bffd89580869af6dd00885a8d76721f"\n',
     'BUILD_COMMIT = "72083fde6bffd89580869af6dd00885a8d76721f"\n_DEF = load_def()   # V3 supplement 01: the package definition replaces the v2 table and registered inputs; limits stay\nif _DEF:\n    RUNS, REGISTERED_SHA, REGISTERED_BYTES, BUILD_COMMIT = _DEF["runs"], _DEF["registered_sha"], _DEF["registered_bytes"], _DEF["build_commit"]\n'),
    ('''    for sc in ("integrated", "disconnected"):
        f = nets / f"{sc}_2920_3h_unsolved.nc"; rec = jl(nets / f"{sc}_BUILD_RECEIPT.json") or {}
        have = sha(f) if f.exists() else None
''', '''    for run in RUNS.values():
        f = nets / f"{run['base']}_unsolved.nc"; rc = input_receipt(nets, run, "network", BUILD_COMMIT)
        have = sha(f) if f.exists() else None
'''),
    ('''        rec_ok = bool(have) and have == (rec.get("network") or {}).get("sha256") and rec.get("code_sha") == BUILD_COMMIT
        rows[f.name] = dict(file=str(f), bytes=(f.stat().st_size if f.exists() else None), sha256=have, receipt_sha256=(rec.get("network") or {}).get("sha256"),
                            receipt_code_sha=rec.get("code_sha"), registered_sha256''',
     '''        rec_ok = bool(have) and have == rc["sha256"] and rc["chain_ok"]
        rows[f.name] = dict(file=str(f), bytes=(f.stat().st_size if f.exists() else None), sha256=have, receipt_sha256=rc["sha256"],
                            receipt_code_sha=rc["code_sha"], registered_sha256'''),
    ('g = gate_b6_cost(float(i["objective"]), float(d["objective"]), "integrated", "disconnected")\n', 'g = gate_b6_cost(float(i["objective"]), float(d["objective"]), RUNS["F1"]["scenario"], RUNS["F2"]["scenario"])\n'),
])

# ---- AutoDL runner
D = P + "p1_dfx_20261026/cloud_package_dfx/"
sub(D + "run_dfx.sh", [
    ('HERE="$(cd "$(dirname "$0")" && pwd)"\n', 'HERE="$(cd "$(dirname "$0")" && pwd)"\n' + EXPORT),
    ('base_scen() { echo "${BASE[$1]%%_*}"; }\n', 'base_scen() { echo "${BASE[$1]%_*_*}"; }\nis_variant() { [ "${SC[$1]}" != "${COSTS[$1]}" ]; }   # V3: a network derived from the one of its cost scenario (no_new_xb from integrated), registered through its variant receipt\n'),
    ('  jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" daily_network.sha256\n', '  if is_variant "$1"; then jget "$NETS/${BASE[$1]}_VARIANT_RECEIPT.json" output.sha256; else jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" daily_network.sha256; fi\n'),
    ('''  local f
  [ "$POST_ONLY" = 1 ] && { log "PREPARE:skipped (POST_ONLY: no solve)"; return 0; }
  for f in integrated_365_24h_unsolved.nc disconnected_365_24h_unsolved.nc integrated_BUILD_RECEIPT.json disconnected_BUILD_RECEIPT.json \\
           integrated_costs_active_research.csv disconnected_costs_active_research.csv; do
''', '''  local f rid need=()
  [ "$POST_ONLY" = 1 ] && { log "PREPARE:skipped (POST_ONLY: no solve)"; return 0; }
  for rid in "${!SC[@]}"; do
    need+=("${BASE[$rid]}_unsolved.nc" "${COSTS[$rid]}_BUILD_RECEIPT.json" "${COSTS[$rid]}_costs_active_research.csv"); if is_variant "$rid"; then need+=("${BASE[$rid]}_VARIANT_RECEIPT.json"); fi
  done
  for f in "${need[@]}"; do
'''),
    ('''  local d="$OUT/$1" lab; lab=$(aux $G6_CMD accept --solve-dir "$d" --build-receipt "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" --repo "$REPO" 2>> "$d/v6.err" | tail -1)
''', '''  local d="$OUT/$1" lab reg=(--build-receipt "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json"); if is_variant "$1"; then reg=(--registered-sha256 "$(registered_of "$1")"); fi
  lab=$(aux $G6_CMD accept --solve-dir "$d" "${reg[@]}" --repo "$REPO" 2>> "$d/v6.err" | tail -1)
'''),
])
sub(D + "preflight_dfx.sh", [
    ('HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"\n', 'HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"\n' + EXPORT),
    ('''  for f in integrated_costs_active_research.csv disconnected_costs_active_research.csv; do [ -s "networks/$f" ] || { echo "networks/$f MISSING"; ok=0; }; done
''', '''  for c in $(cd repo && env -u GRB_LICENSE_FILE "$PY" scripts_project/dfx_batch.py runtable | cut -d'|' -f6 | sort -u); do f=${c}_costs_active_research.csv; [ -s "networks/$f" ] || { echo "networks/$f MISSING"; ok=0; }; done
'''),
])

# ---- HPC runner
B = P + "p1_b4p_20261026/cloud_package_b4/"
sub(B + "run_batch4.sh", [
    ('HERE="$(cd "$(dirname "$0")" && pwd)"\n', 'HERE="$(cd "$(dirname "$0")" && pwd)"\n' + EXPORT),
    ('base_scen() { echo "${BASE[$1]%%_*}"; }\nregistered_of() { jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" network.sha256; }\n',
     'base_scen() { echo "${BASE[$1]%_*_*}"; }\nis_variant() { [ "${SC[$1]}" != "${COSTS[$1]}" ]; }   # V3: a network derived from the one of its cost scenario (no_new_xb from integrated), registered through its variant receipt\nregistered_of() { if is_variant "$1"; then jget "$NETS/${BASE[$1]}_VARIANT_RECEIPT.json" output.sha256; else jget "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" network.sha256; fi; }\n'),
    ('''  local f
  [ "$POST_ONLY" = 1 ] && { log "PREPARE:skipped (POST_ONLY)"; return 0; }
  for f in integrated_2920_3h_unsolved.nc disconnected_2920_3h_unsolved.nc integrated_BUILD_RECEIPT.json disconnected_BUILD_RECEIPT.json integrated_costs_active_research.csv disconnected_costs_active_research.csv; do
''', '''  local f rid need=()
  [ "$POST_ONLY" = 1 ] && { log "PREPARE:skipped (POST_ONLY)"; return 0; }
  for rid in "${!SC[@]}"; do
    need+=("${BASE[$rid]}_unsolved.nc" "${COSTS[$rid]}_BUILD_RECEIPT.json" "${COSTS[$rid]}_costs_active_research.csv"); if is_variant "$rid"; then need+=("${BASE[$rid]}_VARIANT_RECEIPT.json"); fi
  done
  for f in "${need[@]}"; do
'''),
    ('''accept() { local d="${2:-$OUT/$1}" lab; lab=$(aux $G6_CMD accept --solve-dir "$d" --build-receipt "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json" --repo "$REPO" 2>> "$d/v6.err" | tail -1); echo "$lab" > "$d/.label"; echo "$lab"; }
''', '''accept() {
  local d="${2:-$OUT/$1}" lab reg=(--build-receipt "$NETS/$(base_scen "$1")_BUILD_RECEIPT.json"); if is_variant "$1"; then reg=(--registered-sha256 "$(registered_of "$1")"); fi
  lab=$(aux $G6_CMD accept --solve-dir "$d" "${reg[@]}" --repo "$REPO" 2>> "$d/v6.err" | tail -1); echo "$lab" > "$d/.label"; echo "$lab"
}
'''),
])
sub(B + "preflight.sh", [
    ('HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"\n', 'HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"\n' + EXPORT),
    ('''  for f in integrated_costs_active_research.csv disconnected_costs_active_research.csv; do [ -s "networks/$f" ] || { echo "networks/$f MISSING"; ok=0; }; done
''', '''  for c in $(cd repo && env -u GRB_LICENSE_FILE "$PY" scripts_project/b4_batch4.py runtable | cut -d'|' -f6 | sort -u); do f=${c}_costs_active_research.csv; [ -s "networks/$f" ] || { echo "networks/$f MISSING"; ok=0; }; done
'''),
    ('assert b4_batch4.BUILD_COMMIT.startswith("72083fde") and set(b4_batch4.REGISTERED_SHA) == {"integrated_2920_3h_unsolved.nc", "disconnected_2920_3h_unsolved.nc"}, "registered networks"\n',
     'import os\nassert "BATCH_DEF" in os.environ or (b4_batch4.BUILD_COMMIT.startswith("72083fde") and set(b4_batch4.REGISTERED_SHA) == {"integrated_2920_3h_unsolved.nc", "disconnected_2920_3h_unsolved.nc"}), "registered networks"\nassert set(b4_batch4.REGISTERED_SHA) == {r["base"] + "_unsolved.nc" for r in b4_batch4.RUNS.values()}, "registered networks = run table"\n'),
])
H = P + "p1_hpr_20261027/hpc_package_src/"
sub(H + "hpr_job.sh", [
    ('PKG=${PBS_O_WORKDIR:?run under PBS (qsub) - or set PBS_O_WORKDIR for the local drill}; cd "$PKG" || exit 2\n',
     'PKG=${PBS_O_WORKDIR:?run under PBS (qsub) - or set PBS_O_WORKDIR for the local drill}; cd "$PKG" || exit 2\nunset BATCH_DEF; if [ -f "$PKG/BATCH_DEF.json" ]; then export BATCH_DEF="$PKG/BATCH_DEF.json"; fi   # V3 supplement 01: registered batch definition of this package; without it the v2 tables apply\n'),
])
print("patched")
