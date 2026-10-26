p = "/home/jin/dfx3/msg_phase3.txt"; s = open(p).read()
assert "FULL_SUITE_RESULT" in s
s = s.replace("P3 (full suite: FULL_SUITE_RESULT)", "P3 (full suite at 17441b20: 702 passed / 67 skipped / 0 failed; the first run at f73f5c06 had 3 failures analysed in the checklist)")
open(p, "w").write(s); print("msg patched")
