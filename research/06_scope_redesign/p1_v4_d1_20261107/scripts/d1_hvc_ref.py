"""V4 D1 section 2 item 2 (decision 214 items 8 / 9): HVC items of the I2 engine for both bases (i2 = basis b, s2 = basis a), as the reference of
tests/research/test_v4_d1_prep.py::test_hvc_basis_items_equal_i2. Reads the I2 delivery scripts (work/p1_v4_w07_20261106/I2/scripts, read only; i2_items.py
SHA256 1ec27d72...) and the W07 session deliverables they load; writes tables/D1_HVC_REF_I2.csv (one row per country x basis). No solver, no repository write.

    PYTHONHASHSEED=0 <env python> scripts/d1_hvc_ref.py <I2 scripts dir> <out csv>
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

I2S = Path(sys.argv[1]); OUT = Path(sys.argv[2])
sys.path.insert(0, str(I2S))
import i2_items as IT   # noqa: E402

S = IT.load_sessions()
rows = []
for basis, label in (("i2", "b"), ("s2", "a")):
    for cc, h in IT.hvc_items(S, basis).items():
        it = dict(fuel19=h["hvc19_t"] * h["fuel19_per_t"], el19=h["hvc19_t"] * h["el19_per_t"], v2050=IT.vec(h["vec"], h["hvc50_base_t"]))
        new = IT.vec(h["vec"], h["hvc50_new_t"]) if h["hvc50_new_t"] > 0 else {}
        rows.append(dict(country=cc, basis=label, i2_basis=basis, hvc19_t=repr(h["hvc19_t"]), hvc50_base_t=repr(h["hvc50_base_t"]), hvc50_new_t=repr(h["hvc50_new_t"]),
                         row=h["row"] or "", fuel_split=json.dumps(h["fuel_split"]) if h["fuel_split"] else "", el19_per_t=repr(h["el19_per_t"]), fuel19_per_t=repr(h["fuel19_per_t"]),
                         item_fuel19_mwh=repr(it["fuel19"]), item_el19_mwh=repr(it["el19"]), item_v2050_json=json.dumps({k: v for k, v in it["v2050"].items() if v}, sort_keys=True),
                         new_v2050_json=json.dumps({k: v for k, v in new.items() if v}, sort_keys=True)))
OUT.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(OUT, index=False, lineterminator="\n")
print(OUT, len(rows), "rows; i2_items.py sha256", hashlib.sha256((I2S / "i2_items.py").read_bytes()).hexdigest())
