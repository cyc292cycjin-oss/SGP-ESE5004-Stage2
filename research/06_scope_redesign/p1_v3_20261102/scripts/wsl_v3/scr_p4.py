p = "/home/jin/v3/dry_s2.sh"; s = open(p, encoding="utf-8").read()
a = """R2=$(env -u GRB_LICENSE_FILE PY=$PY GURobi=1 TRUNCATE=56 RUN_DIR=$A/refuse2 GRB_LICENSE_FILE=/etc/hostname bash $A/run_dfx.sh --auth x 2>&1 | tail -1 | cut -c1-90)"""
b = """R2=$(env -u GRB_LICENSE_FILE PY=$PY TRUNCATE=56 RUN_DIR=$A/refuse2 bash $A/run_dfx.sh --auth x 2>&1 | tail -1 | cut -c1-90)"""
assert s.count(a) == 1; open(p, "w", encoding="utf-8").write(s.replace(a, b)); print("ok")
