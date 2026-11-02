"""Supplement 05: read-out scripts derived from those of supplement 04."""
V = "/home/jin/v3/"


def conv(src, dst, pairs):
    s = open(V + src, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, a[:70]
        s = s.replace(a, b)
    open(V + dst, "w", encoding="utf-8").write(s)


conv("chk_st4.py", "chk_st5.py", [('"builds_bound"', '"builds_op"'), ('results_project/v3/builds_bound")', 'results_project/v3/builds_op")')] if False else [("results_project/v3/builds_bound", "results_project/v3/builds_op")])
conv("chk_pc5.py", "chk_pc6.py", [('R, O = M / "path_check5", M / "path_check4"', 'R, O = M / "path_check6", M / "path_check5"'), ("LEDGER_CHECK_179.json", "LEDGER_CHECK_180.json"), ("same check on the one-way networks", "same check on the networks of supplement 04")])
conv("chk_sm4.py", "chk_sm5.py", [('R, O = M / "smoke_s4", M / "smoke_s3"', 'R, O = M / "smoke_s5", M / "smoke_s4"'), ("LEDGER_CHECK_179_SMOKE.json", "LEDGER_CHECK_180_SMOKE.json"), ("smoke_s4/V3_SMOKE_RESULT.json", "smoke_s5/V3_SMOKE_RESULT.json"), ("against the one-way smoke", "against the smoke of supplement 04")])
conv("sm_s4c.py", "sm_s5c.py", [("smoke_s4/{sc}/", "smoke_s5/{sc}/"), ("SOURCE_BALANCE_SMOKE.json", "SOURCE_BALANCE_OP_SMOKE.json"), ('smoke_s4/integrated/V5_GATES.json', 'smoke_s5/integrated/V5_GATES.json')])
print("ok")
