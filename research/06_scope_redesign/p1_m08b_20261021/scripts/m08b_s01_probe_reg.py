"""M08b supplement 01 probe (read-only): registry rows that still reference the pre-M08a cost layer (ea20gdp rebase) by SHA256."""
import sys
import pandas as pd

REG = "/home/jin/wt_m08b_20261021/research_inputs/registry_v5/DATA_REGISTRY.csv"
OLD = {"708daebadfc81680079e1f8794772e0ab945f33088b624ad6eb6499c06ef17e9": "old raw", "17b1b23037807745571c3cadee0b2c41989d08ecf985c371f94c5619017aba4e": "old prepared"}
NEW = {"790677bc63fbbc80f018db96a475bfdbdeb3e51a80de0fa24c7b89a1076bb289": "new raw", "8d8a31647226fae1c5a172a649917255bd44aa9b85ab8b65d4c388eda1075d44": "new prepared"}
r = pd.read_csv(REG, dtype=str, keep_default_na=False)
pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 70); pd.set_option("display.max_rows", 500)
o = r[r.source_sha256.isin(OLD)]
print("old-sha rows", len(o), "new-sha rows", int(r.source_sha256.isin(NEW).sum()))
print(o.groupby(["derivation_script", "status"]).size().to_string())
print(o[["param_id", "value", "unit", "status", "derivation_script"]].to_string())
if len(sys.argv) > 1:
    for pid in sys.argv[1:]:
        print(r[r.param_id == pid].T.to_string())
# rows whose locator / source names the cost-layer file but carry another SHA
m = r.source_locator.str.contains("costs_2050_EUR2020", regex=False) | r.source.str.contains("EUR2020 layer", regex=False)
print("locator mentions cost layer:", int(m.sum()), r[m].source_sha256.map(lambda s: OLD.get(s) or NEW.get(s) or s[:12]).value_counts().to_string())
