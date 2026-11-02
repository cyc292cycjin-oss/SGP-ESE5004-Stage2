p = "/home/jin/v3/eval_patch.py"
s = open(p).read()
assert s.count('b6_bn=(o["disconnected"] - o["integrated"]) / 1e9') == 2
s = s.replace('b6_bn=(o["disconnected"] - o["integrated"]) / 1e9', 'b6_bn_eur=(o["disconnected"] - o["integrated"]) / 1e9')
a = "    ('''    if a.v2_run:\n        o = {sc: jl("
b = "    ('    if len(nets) == 2:\n', '    if \"integrated\" in nets and \"no_new_xb\" in nets:\n'),\n    ('''    if a.v2_run:\n        o = {sc: jl("
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w").write(s)
