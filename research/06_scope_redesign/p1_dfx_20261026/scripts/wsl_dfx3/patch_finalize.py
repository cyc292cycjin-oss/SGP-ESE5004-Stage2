p = "/home/jin/dfx3/finalize.sh"; s = open(p).read()
old = 'echo "== collect evidence"; bash /home/jin/dfx3/collect_evidence.sh dry_run_v8b > /dev/null;'
new = ('D=/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026\n'
       'echo "== keep the first full-suite log"; [ -f $D/evidence/tests/full.log ] && [ ! -f $D/evidence/tests/full_first_f73f5c06.log ] && ( cd /home/jin/wt_dfx_v3_20261026 && git mv research/06_scope_redesign/p1_dfx_20261026/evidence/tests/full.log research/06_scope_redesign/p1_dfx_20261026/evidence/tests/full_first_f73f5c06.log && echo moved )\n'
       'echo "== collect evidence"; bash /home/jin/dfx3/collect_evidence.sh dry_run_v8b > /dev/null;')
assert old in s; s = s.replace(old, new); open(p, "w").write(s); print("finalize.sh patched")
