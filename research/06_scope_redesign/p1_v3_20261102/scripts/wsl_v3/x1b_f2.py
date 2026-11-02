W = "/home/jin/wt_v3_20261102/"
p = W + "tests/research/test_v3.py"; s = open(p, encoding="utf-8", newline="").read()
pairs = [('''    for b in sorted(set(t.plant_node) | set(t.landing_node)):
        n.add("Bus", b, carrier="AC", x=100.0 + hash_free(b), y=15.0 + hash_free(b)); n.buses.loc[b, "country"] = b[:2]
''', '''    for i, b in enumerate(sorted(set(t.plant_node) | set(t.landing_node))):
        n.add("Bus", b, carrier="AC", x=100.0 + i, y=15.0 + 0.5 * i); n.buses.loc[b, "country"] = b[:2]
'''), ('''def hash_free(b: str) -> float:
    """a coordinate offset from the node name (no use of Python hash)"""
    return (sum(map(ord, b)) % 7) / 2.0


''', '')]
for a, b in pairs:
    assert s.count(a) == 1, a[:50]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="").write(s); print("ok")
