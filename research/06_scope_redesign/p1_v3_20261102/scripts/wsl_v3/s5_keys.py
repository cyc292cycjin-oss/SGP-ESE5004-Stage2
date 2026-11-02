"""Supplement 05: in the read-outs derived from supplement 04 the baseline is the previous network, not the one-way network."""
for f in ("/home/jin/v3/chk_pc6.py", "/home/jin/v3/chk_sm5.py"):
    s = open(f, encoding="utf-8").read(); n = s.count("_one_way"); s = s.replace("_one_way", "_previous"); open(f, "w", encoding="utf-8").write(s); print(f, n)
