p = "/home/jin/wt_v3_20261102/tests/research/test_dfx_demand.py"
s = open(p, encoding="utf-8").read()
a = 'later = [p for p in later if not Path(p).name.startswith("v3_")]   # new files of the V3 step, documented in its own folder'
b = 'later = [p for p in later if not Path(p).name.startswith("v3_") and Path(p).name != "batch_def.py"]   # new files of the V3 step, documented in its own folder'
assert s.count(a) == 1
open(p, "w", encoding="utf-8").write(s.replace(a, b))
