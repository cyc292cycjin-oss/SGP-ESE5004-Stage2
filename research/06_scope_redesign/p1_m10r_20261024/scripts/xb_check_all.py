"""M10R B2.3 (read only): for every given network file, which rows of the existing_cross_border_fom_ledger meta refer to components that are
not in the network (the code path changed by the fix); writes one JSON. Usage: python xb_check_all.py <out.json> <name=path.nc> ..."""
import json
import sys

sys.path.insert(0, "/home/jin/m10r")
from inspect_xb import info  # noqa: E402

out = {}
for arg in sys.argv[2:]:
    name, path = arg.split("=", 1)
    r = info(path)
    miss = r["ledger_components_missing_from_network"]
    out[name] = dict(file=path, scenario=r["scenario"], snapshots=r["snapshots"], ledger_rows=r["ledger_rows"], ledger_fom_eur=r["ledger_fom_sum"], fom_eur_meta=r["fom_eur_meta"],
                     xb_lines=r["xb_lines"], xb_links=r["xb_links"], ledger_components_missing=len(miss), missing_with_nonzero_fom=sum(1 for m in miss if m["annual_fom_eur"] != 0),
                     missing_examples=[f"{m['component_type']}:{m['component']}" for m in miss[:6]], fix_path_taken=bool(miss))
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(json.dumps({k: (v["ledger_components_missing"], v["missing_with_nonzero_fom"]) for k, v in out.items()}))
