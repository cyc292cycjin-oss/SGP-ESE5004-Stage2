p = "/home/jin/dfx3/dry_run_v8.sh"; s = open(p).read()
old = "B=$MAIN/results_project/dfx_v3/builds_v2; D=$MAIN/results_project/dfx_v3/dry_run_v8; PKG="
new = "B=$MAIN/results_project/dfx_v3/builds_v2; D=$MAIN/results_project/dfx_v3/${1:-dry_run_v8}; PKG="
assert old in s; open(p, "w").write(s.replace(old, new)); print("patched: dry-run dir = argument 1 (default dry_run_v8)")
