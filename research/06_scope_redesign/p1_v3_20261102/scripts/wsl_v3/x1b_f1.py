W = "/home/jin/wt_v3_20261102/"
p = W + "tests/research/test_v3.py"; s = open(p, encoding="utf-8", newline="").read()
a = """    n, led = dedicated_toy()
    assert led["links"] == 6"""
b = """    n, led = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str)
    assert led["links"] == 6"""
assert s.count(a) == 1; open(p, "w", encoding="utf-8", newline="").write(s.replace(a, b)); print("ok")
