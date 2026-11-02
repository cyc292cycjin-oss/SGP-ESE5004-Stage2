W = "/home/jin/wt_v3_20261102/"
p = W + "tests/research/test_v3_runners.py"; s = open(p, encoding="utf-8", newline="").read()
a = '''        keep = {"V1", "V2"}; d["runs"] = {k: v for k, v in d["runs"].items() if k in keep}
'''
b = '''        keep = list(d["runs"])[:2]; d["runs"] = {k: d["runs"][k] for k in keep}; d["registered_sha"] = {k: v for k, v in d["registered_sha"].items() if k in {d["runs"][r]["base"] + "_unsolved.nc" for r in keep}}
'''
assert s.count(a) == 1; open(p, "w", encoding="utf-8", newline="").write(s.replace(a, b)); print("ok")
