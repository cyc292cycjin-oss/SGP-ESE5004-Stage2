p = "/home/jin/dfx3/smoke_summary.py"; s = open(p).read()
old1 = 'post_exits={k: v for k, v in ((m.group(1), m.group(2)) for m in re.finditer(r"^(VIOLATIONS|C1|M12|OWEN|REGRADE|OWEN_REGRADE)_" + sc + r":[^:]+:exit=(\d+)", st, re.M))})'
new1 = 'post_exits={m.group(1): m.group(2) for m in re.finditer(r"^(VIOLATIONS|C1|M12|OWEN|REGRADE|OWEN_REGRADE)_" + sc + r":.*?exit=(\d+)", st, re.M)})'
old2 = 'r":(S+?Z):"'; new2 = 'r":(\S+?Z):"'
assert old1 in s and old2 in s, (old1 in s, old2 in s)
open(p, "w").write(s.replace(old1, new1).replace(old2, new2)); print("patched")
