"""只读：v5main 网络文件 SHA256 / 字节数与构建回执（integrated_BUILD_RECEIPT.json、no_new_xb_*_VARIANT_RECEIPT.json）中记录的值对照（代替只适用于打包后的
b4_batch4.py base-check）。用法：python 68b_receipts.py   输出 evidence/V5_BUILD_RECEIPT_CHECK.json"""
import hashlib
import json
from pathlib import Path

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111"); B = D / "builds/v5main"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()
def find(o, key, acc, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key and isinstance(v, str):
                acc.append((path + "/" + k, v))
            find(v, key, acc, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            find(v, key, acc, f"{path}[{i}]")
    return acc
out = {}
for rec in sorted(B.glob("*/*RECEIPT.json")):
    r = json.loads(rec.read_text())
    shas = find(r, "sha256", [])
    rows = []
    for nc in sorted(rec.parent.glob("*_unsolved.nc")):
        s = sha(nc)
        rows.append(dict(network=nc.name, bytes=nc.stat().st_size, sha256=s, in_receipt=[p for p, v in shas if v == s]))
    out[str(rec.relative_to(D))] = dict(code_sha=r.get("code_sha") or r.get("commit"), networks=[x for x in rows if x["in_receipt"]], not_in_receipt=[x["network"] for x in rows if not x["in_receipt"]])
(D / "evidence/V5_BUILD_RECEIPT_CHECK.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1)[:3000])
