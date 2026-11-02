"""X1b patch 4: column types after the plant lines (the netCDF export refuses a mixed bool column); test exports the toy network."""
W = "/home/jin/wt_v3_20261102/"
p = W + "scripts_project/v3_layers.py"; s = open(p, encoding="utf-8", newline="").read()
a = '''    if rows:
        fl = list(n.meta.get("existing_cross_border_fom_ledger", []))'''
b = '''    n.links["reversed"] = n.links["reversed"].fillna(False).astype(bool); n.links["stock"] = n.links["stock"].fillna("").astype(str)   # as s4j_layers: a mixed column does not export
    if rows:
        fl = list(n.meta.get("existing_cross_border_fom_ledger", []))'''
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s)
p = W + "tests/research/test_v3.py"; s = open(p, encoding="utf-8", newline="").read()
a = '''def test_x1b_layer_toy():
    from v3_static import stock_by_pair
    n, led = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str)
'''
b = '''def test_x1b_layer_toy(tmp_path):
    from v3_static import stock_by_pair
    n, led = dedicated_toy(); n.lines["border_class"] = pd.Series(dtype=str)
    n.links["country"] = n.links["country"].astype(str); n.export_to_netcdf(tmp_path / "toy.nc")   # the build exports the network: no mixed column
'''
assert s.count(a) == 1; s = s.replace(a, b); open(p, "w", encoding="utf-8", newline="").write(s); print("patched")
